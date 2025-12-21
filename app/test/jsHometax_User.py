#####################################
#   사용자 아이디 로그인으로 정보조회
#####################################

from app.models import MemUser
from app.models import MemDeal
# from datetime import datetime
import time
import datetime
import json,math
import re
import requests
import urllib.parse
from django.db import connection
from app.test import utils
from urllib.parse import unquote_plus
from typing import Any, Mapping


def login_and_get_sso(id,password,biz_no,biz_type,biz_name,ssn, isNotShowChrome, 
                      entry_url="https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml",
                      referer_url="https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml",
                      timeout=10):
    """
    1) Selenium으로 홈택스 접속/로그인
    2) 받은 쿠키를 requests.Session에 이식
    3) token.do 호출로 SSO 토큰 등 메타 가져오기
    """
    driver = None
    try:
      # 1) 로그인 (utils.conHometaxLogin은 기존 코드 사용)
      password_safe = password.replace("＃", "#")
      driver = utils.conHometaxLogin_Personal(id,password_safe,biz_no,biz_type,biz_name,ssn, isNotShowChrome)
      if driver:
        driver.get(entry_url)
        time.sleep(3)

        # 2) 세션에 쿠키 이식
        sess = requests.Session()
        for c in driver.get_cookies():
            # domain이 없으면 기본 도메인 부여
            domain = c.get("domain") or ".hometax.go.kr"
            sess.cookies.set(c["name"], c["value"], domain=domain)

        # 3) SSO 토큰 조회
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": referer_url
        }
        resp = sess.get("https://www.hometax.go.kr/token.do", headers=headers, timeout=timeout)
        try:
            data = resp.json()
        except ValueError:
            print("token.do 응답이 JSON이 아님")
            return None

        sso_token = str(data.get("ssoToken", "") or "")
        userClCd  = str(data.get("userClCd", "") or "")

        if not sso_token or sso_token.lower() == "null":
            print("ssoToken 추출 실패(-10131)")
            return None
        if not userClCd or userClCd.lower() == "null":
            print("userClCd 추출 실패(-10132)")
            return None

        result = {
            "session": sess,
            "ssoToken": sso_token,
            "userClCd": userClCd,
            "cookies": sess.cookies.get_dict()
        }
        return result
      else:
        print("로그인에 실패했습니다.")
        return None
    except Exception as e:
        print(f"로그인/토큰 처리 실패: {e!r}")
        return None
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass

# 화면 허가권
def call_permission(loginSession,domain, screen_id, timeout: int = 12):
    session = loginSession["session"]
    ssoToken = loginSession["ssoToken"]
    userClCd = loginSession["userClCd"]            
    URL = f"https://{domain}.hometax.go.kr/permission.do"
    params = {
        "screenId": screen_id,
        "domain": "hometax.go.kr"
    }
    headers = {
        "Accept": "application/json; charset=UTF-8",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {
      "userClCd":userClCd,
      "ssoToken":ssoToken,
      "popupYn":"false"  
    }
  
    r = session.post(URL, params=params,  json=payload, headers=headers, timeout=15)
    try:
        data = r.json()                 
    except ValueError:
        # JSON이 아닐 때 디버깅에 도움
        print("Non-JSON response:", r.status_code, r.headers.get("Content-Type"), r.text[:500])
        return None

    # 원하는 경로 추출
    session_map = data.get("resultMsg", {}).get("sessionMap")
    return session_map
    
# 사업용카드 매입내역 총괄
def call_tecr_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,chkPeriod, m_trsDtRngStrt,m_trsDtRngEnd,pageInfoVO, page: int = 1):
    session = loginSession["session"]
    WQ_URL = "https://tecr.hometax.go.kr/wqAction.do"
    params = {
        "actionId": action_id,
        "screenId": screen_id,
        "popupYn": "false",
        "realScreenId": "",
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
        "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
        "X-Requested-With": "XMLHttpRequest",
    }
    payload = {
      "tin": sessionMap["tin"],
      "trsDtRngStrt": m_trsDtRngStrt,
      "trsDtRngEnd": m_trsDtRngEnd,
      "prhTxamtDdcYn": "all",
      "sumTotaTrsAmt": "",
      "resultCd": ""
    }    

    if pageInfoVO:
      # 조회할 페이지는 인자로 받는다
      # page = int(pageInfoVO.get("pageNum", page))
      page_size = str(pageInfoVO.get("pageSize", "20"))
      total_count_hint = pageInfoVO.get("totalCount", "")
    else:
      page = 1
      page_size = 20
      total_count_hint = ""

    payload["pageInfoVO"] = {
        "pageNum": str(page),
        "pageSize": page_size,
        "totalCount": str(total_count_hint) if total_count_hint is not None else "",
    }
    retries = 2
    for attempt in range(retries + 1):
        # ⬇️ wqAction은 반드시 원문을 data= 로 보냄 (json= 쓰면 토큰이 날아감)
        resp = session.post(WQ_URL, params=params, json=payload, headers=headers, timeout=15)

        text = resp.text  # 문자열로 꺼내서 검사
        if "과부하제어" in text or resp.status_code in (429, 503):
            if attempt < retries:
                time.sleep(61)  # busy-wait 대신 sleep
                continue
            return {"error": "throttled", "status": resp.status_code, "body": text[:300]}

        if not text.strip():
            return None

        # 응답이 JSON이면 파싱, 아니면 원문 반환
        try:
          data = resp.json() 
          busnCrdcTrsBrkdAdmDVOList = data.get("busnCrdcTrsBrkdAdmDVOList", []) or []
          if action_id == "ATECRCCA001R06" :
            insert_CostCard_Biz(seq_no,chkPeriod,busnCrdcTrsBrkdAdmDVOList)
          elif action_id == "ATECRCCA001R07" :
            insert_CostCard_Oil(seq_no,chkPeriod,busnCrdcTrsBrkdAdmDVOList)
          # 총 건수/페이지 계산
          pinfo = data.get("pageInfoVO", {})
          page_size = pinfo.get("pageSize")
          total_count = pinfo.get("totalCount")
          # 서버가 문자열로 주는 경우가 많으니 안전 변환
          try:
              total_count_int = int(total_count)
          except (TypeError, ValueError):
              total_count_int = 0  # fallback

          try:
              page_size_int = int(page_size)
          except ValueError:
              page_size_int = 20

          total_pages = max(1, math.ceil(total_count_int / page_size_int))
          print(f"신용카드_저장 (page {page} / {total_pages}) 총개수 {total_count_hint}"  ) 

          # 종료 혹은 다음 페이지 재귀
          if page >= total_pages or not busnCrdcTrsBrkdAdmDVOList:
              return  total_count_int

          return call_tecr_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id, chkPeriod,m_trsDtRngStrt,m_trsDtRngEnd, pinfo, page=page + 1)                    
        except ValueError:
            return None

# 신용카드 등 매출       
def call_CardSale_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,flagYear,chkPeriod,pageInfoVO, page: int = 1):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)      
  session = loginSession["session"]
  WQ_URL = "https://teht.hometax.go.kr/wqAction.do"
  params = {
      "actionId": action_id,
      "screenId": screen_id,
      "popupYn": "false",
      "realScreenId": "",
  }
  headers = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "Origin": "https://hometax.go.kr",
      "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
      "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
      "X-Requested-With": "XMLHttpRequest",
  }
  
  payload = {
      "bsno": memuser.biz_no.replace("-",""),  # 사업자등록번호 (예: '2042683700')
      "dwldYn": "",
      "excelYn": "",
      "qrtFrom": chkPeriod,  # 분기 시작 (예: '1')
      "qrtTo": chkPeriod,      # 분기 끝 (예: '2')
      "stlYr": flagYear
  }   
  if pageInfoVO:
    # 조회할 페이지는 인자로 받는다
    # page = int(pageInfoVO.get("pageNum", page))
    page_size = str(pageInfoVO.get("pageSize", "50"))
    total_count_hint = pageInfoVO.get("totalCount", "")
  else:
    page = 1
    page_size = 50
    total_count_hint = ""

  payload["pageInfoVO"] = {
      "pageNum": str(page),
      "pageSize": page_size,
      "totalCount": str(total_count_hint) if total_count_hint is not None else "",
  }
  retries = 2
  for attempt in range(retries + 1):
      # ⬇️ wqAction은 반드시 원문을 data= 로 보냄 (json= 쓰면 토큰이 날아감)
      resp = session.post(WQ_URL, params=params, json=payload, headers=headers, timeout=15)

      text = resp.text  # 문자열로 꺼내서 검사
      if "과부하제어" in text or resp.status_code in (429, 503):
          if attempt < retries:
              time.sleep(61)  # busy-wait 대신 sleep
              continue
          return {"error": "throttled", "status": resp.status_code, "body": text[:300]}

      if not text.strip():
          return None

      # 응답이 JSON이면 파싱, 아니면 원문 반환
      try:
        data = resp.json() 
        if page==1:
          insert_CardSale(seq_no,flagYear,data)
  
        m = data.get("sleVcexSlsMateInqrDVO", {})
        m_pmdh_sumStlScnt = int(m.get("sumStlScnt") or 0) #거래건수
        m_sumSplCft = int((sumTipExclAmt := int(float(m.get("sumTipExclAmt") or 0))) > 0)
        if sumTipExclAmt > 0:    
          print("판매대행 공급가액 : " + str(m_sumSplCft) + " , 거래건수 : " + str(m_pmdh_sumStlScnt))    
          pmdhDetails = data.get("sleVcexSlsMateInqrDVOList", [])
          insert_PMDHSale(seq_no,flagYear,pmdhDetails)
          
        # 총 건수/페이지 계산
        pinfo = data.get("pageInfoVO", {})
        page_size = pinfo.get("pageSize")
        total_count = pinfo.get("totalCount")
        # 서버가 문자열로 주는 경우가 많으니 안전 변환
        try:
            total_count_int = int(total_count)
        except (TypeError, ValueError):
            total_count_int = 0  # fallback

        try:
            page_size_int = int(page_size)
        except ValueError:
            page_size_int = 20

        total_pages = max(1, math.ceil(total_count_int / page_size_int))
        print(f"판매대행 매출_저장 (page {page} / {total_pages}) 총개수 {total_count_hint}"  ) 

        # 종료 혹은 다음 페이지 재귀
        if page >= total_pages or not pmdhDetails:
            return  total_count_int

        return call_tecr_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,flagYear,chkPeriod,pageInfoVO, page=page + 1)                    
      except ValueError:
          return None    

# 현금영수증 매출       
def call_CashSale_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,chkPeriod,trsDtRngStrt,trsDtRngEnd):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)      
  session = loginSession["session"]
  WQ_URL = "https://tecr.hometax.go.kr/wqAction.do"
  params = {
      "actionId": action_id,
      "screenId": screen_id,
      "popupYn": "false",
      "realScreenId": "",
  }
  headers = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "Origin": "https://hometax.go.kr",
      "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
      "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
      "X-Requested-With": "XMLHttpRequest",
  }
 
  payload = {
     "cmttYr":"",
     "tin":sessionMap["tin"],
     "trsDtRngEnd":trsDtRngEnd,
     "trsDtRngStrt":trsDtRngStrt
  }

  retries = 2
  for attempt in range(retries + 1):
      # ⬇️ wqAction은 반드시 원문을 data= 로 보냄 (json= 쓰면 토큰이 날아감)
      resp = session.post(WQ_URL, params=params, json=payload, headers=headers, timeout=15)

      text = resp.text  # 문자열로 꺼내서 검사
      if "과부하제어" in text or resp.status_code in (429, 503):
          if attempt < retries:
              time.sleep(61)  # busy-wait 대신 sleep
              continue
          return {"error": "throttled", "status": resp.status_code, "body": text[:300]}

      if not text.strip():
          return None

      # 응답이 JSON이면 파싱, 아니면 원문 반환
      try:
        data = resp.json() 
        
        cshTrsBrkdInqrDVOList = data.get("cshTrsBrkdInqrDVOList", []) or []
        for item in cshTrsBrkdInqrDVOList:
            m_sttsYm = item.get("sttsYm")    #귀속년월
            m_cshSlsCmttScnt = item.get("cshSlsCmttScnt")    #건수
            m_cshSlsSplCftCmttAmt = 0                    # 공급가액
            if item.get("cshSlsSplCftCmttAmt")  is not None:m_cshSlsSplCftCmttAmt =  item.get("cshSlsSplCftCmttAmt") 
            m_cshSlsVatCmttAmt = 0                   # 세액
            if item.get("cshSlsVatCmttAmt")  is not None:m_cshSlsVatCmttAmt =  item.get("cshSlsVatCmttAmt") 
            m_cshSlsTipCmttAmt = 0                       # 봉사료
            if item.get("cshSlsTipCmttAmt")  is not None:m_cshSlsTipCmttAmt =  item.get("cshSlsTipCmttAmt") 
            m_totaTrsAmt = m_cshSlsSplCftCmttAmt +  m_cshSlsVatCmttAmt  + m_cshSlsTipCmttAmt             # 합계

            str_ins = (
                f"INSERT INTO Tbl_HomeTax_SaleCard VALUES ('{m_sttsYm[:4]}', '{seq_no}', '현금영수증', '{chkPeriod}', "
                f"'{m_sttsYm}', {m_cshSlsCmttScnt}, {m_totaTrsAmt}, {m_cshSlsSplCftCmttAmt}, {m_cshSlsVatCmttAmt}, {m_cshSlsTipCmttAmt}, GETDATE(), "
                f"isnull((SELECT TOP 1 acnt_cd FROM ds_slipledgr2 WHERE seq_no={seq_no} AND work_yy>{int(m_sttsYm[:4])-5} "
                f"AND acnt_cd>=401 AND acnt_cd<430 GROUP BY acnt_cd ORDER BY COUNT(acnt_cd) DESC),'401'),'','')"
            )
            # print(str_ins)
            with connection.cursor() as cursor:
              cursor.execute(str_ins)
            print(f"현금영수증 매출_저장 ( {m_sttsYm} ) 공급대가 {m_totaTrsAmt}, 공급가액 {m_cshSlsSplCftCmttAmt}, 세액 {m_cshSlsVatCmttAmt}"  ) 
        return True                 
      except ValueError:
          return None            

# 현금영수증 매입
def call_CashCost_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,flagYear,txtRangeStart, txtRangeEnd,pageInfoVO, page: int = 1):
  session = loginSession["session"]
  WQ_URL = "https://tecr.hometax.go.kr/wqAction.do"
  params = {
      "actionId": action_id,
      "screenId": screen_id,
      "popupYn": "false",
      "realScreenId": "",
  }
  headers = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "Origin": "https://hometax.go.kr",
      "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
      "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
      "X-Requested-With": "XMLHttpRequest",
  } 
  payload = {
    "tin": sessionMap["tin"],
    "trsDtRngStrt": txtRangeStart,
    "trsDtRngEnd": txtRangeEnd,
    "prhTxamtDdcYn": "all",
    "sumTotaTrsAmt": "",
    "resultCd": ""
  }
  if pageInfoVO:
    # 조회할 페이지는 인자로 받는다
    # page = int(pageInfoVO.get("pageNum", page))
    page_size = str(pageInfoVO.get("pageSize", "20"))
    total_count_hint = pageInfoVO.get("totalCount", "")
  else:
    page = 1
    page_size = 20
    total_count_hint = ""

  payload["pageInfoVO"] = {
      "pageNum": str(page),
      "pageSize": page_size,
      "totalCount": str(total_count_hint) if total_count_hint is not None else "",
  }
  retries = 2
  for attempt in range(retries + 1):
      # ⬇️ wqAction은 반드시 원문을 data= 로 보냄 (json= 쓰면 토큰이 날아감)
      resp = session.post(WQ_URL, params=params, json=payload, headers=headers, timeout=15)

      text = resp.text  # 문자열로 꺼내서 검사
      if "과부하제어" in text or resp.status_code in (429, 503):
          if attempt < retries:
              time.sleep(61)  # busy-wait 대신 sleep
              continue
          return {"error": "throttled", "status": resp.status_code, "body": text[:300]}

      if not text.strip():
          return None

      # 응답이 JSON이면 파싱, 아니면 원문 반환
      try:
        data = resp.json() 
        m_sumTotaTrsAmt = data.get("sumTotaTrsAmt")
        m_sumSplCft = data.get("sumSplCft")      
        cshTrsBrkdInqrDVOList = data.get("cshTrsBrkdInqrDVOList", []) or []

        insert_CashCost(seq_no,flagYear,cshTrsBrkdInqrDVOList)

        # 총 건수/페이지 계산
        pinfo = data.get("pageInfoVO", {})
        page_size = pinfo.get("pageSize")
        total_count = pinfo.get("totalCount")
        # 서버가 문자열로 주는 경우가 많으니 안전 변환
        try:
            total_count_int = int(total_count)
        except (TypeError, ValueError):
            total_count_int = 0  # fallback

        try:
            page_size_int = int(page_size)
        except ValueError:
            page_size_int = 20

        total_pages = max(1, math.ceil(total_count_int / page_size_int))
        print(f"현금영수증 매입_저장 (page {page} / {total_pages}) 총개수 {total_count_hint}"  ) 

        # 종료 혹은 다음 페이지 재귀
        if page >= total_pages or not cshTrsBrkdInqrDVOList:
            return  total_count_int

        return call_CashCost_wqaction(seq_no,loginSession,sessionMap,screen_id,action_id,flagYear,txtRangeStart, txtRangeEnd, pinfo, page=page + 1)                    
      except ValueError:
          return None

# 현금영수증 매출 - 세부내역 저장  ==> 사용안함
def call_CashSale_wqaction2(seq_no,loginSession,sessionMap,screen_id,action_id,flagYear, m_trsDtRngStrt,m_trsDtRngEnd,pageInfoVO, page: int = 1):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)      
  session = loginSession["session"]
  WQ_URL = "https://teht.hometax.go.kr/wqAction.do"
  params = {
      "actionId": action_id,
      "screenId": screen_id,
      "popupYn": "false",
      "realScreenId": "",
  }
  headers = {
      "Accept": "application/json",
      "Content-Type": "application/json",
      "Origin": "https://hometax.go.kr",
      "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
      "User-Agent": session.headers.get("User-Agent", "Mozilla/5.0"),
      "X-Requested-With": "XMLHttpRequest",
  }
  payload = {
    "tin": sessionMap["tin"],
    "trsDtRngStrt": m_trsDtRngStrt,
    "trsDtRngEnd": m_trsDtRngEnd,
    "prhTxamtDdcYn": "all",
    "sumTotaTrsAmt": '0',
    "resultCd": "N",
    "dwldTrsBrkdScnt":"0",
    "totalCount":'0',
    "sumSplCft":'0'
  }  
 
  if pageInfoVO:
    # 조회할 페이지는 인자로 받는다
    # page = int(pageInfoVO.get("pageNum", page))
    page_size = str(pageInfoVO.get("pageSize", "50"))
    total_count_hint = pageInfoVO.get("totalCount", "")
  else:
    page = 1
    page_size = 50
    total_count_hint = ""

  payload["pageInfoVO"] = {
      "pageNum": str(page),
      "pageSize": page_size,
      "totalCount": str(total_count_hint) if total_count_hint is not None else "",
  }
  retries = 2
  for attempt in range(retries + 1):
      # ⬇️ wqAction은 반드시 원문을 data= 로 보냄 (json= 쓰면 토큰이 날아감)
      resp = session.post(WQ_URL, params=params, json=payload, headers=headers, timeout=15)

      text = resp.text  # 문자열로 꺼내서 검사
      if "과부하제어" in text or resp.status_code in (429, 503):
          if attempt < retries:
              time.sleep(61)  # busy-wait 대신 sleep
              continue
          return {"error": "throttled", "status": resp.status_code, "body": text[:300]}

      if not text.strip():
          return None

      # 응답이 JSON이면 파싱, 아니면 원문 반환
      try:
        data = resp.json() 
        cshTrsBrkdInqrDVOList = data.get("cshTrsBrkdInqrDVOList", []) or []
        insert_CashSale2(seq_no,flagYear,cshTrsBrkdInqrDVOList)

        # 총 건수/페이지 계산
        pinfo = data.get("pageInfoVO", {})
        page_size = pinfo.get("pageSize")
        total_count = pinfo.get("totalCount")
        # 서버가 문자열로 주는 경우가 많으니 안전 변환
        try:
            total_count_int = int(total_count)
        except (TypeError, ValueError):
            total_count_int = 0  # fallback

        try:
            page_size_int = int(page_size)
        except ValueError:
            page_size_int = 50

        total_pages = max(1, math.ceil(total_count_int / page_size_int))
        print(f"현금영수증_저장 (page {page} / {total_pages}) 총개수 {total_count_hint}"  ) 

        # 종료 혹은 다음 페이지 재귀
        if page >= total_pages or not cshTrsBrkdInqrDVOList:
            return  total_count_int

        return call_CashSale_wqaction2(seq_no,loginSession,sessionMap,screen_id,action_id, flagYear,m_trsDtRngStrt,m_trsDtRngEnd, pinfo, page=page + 1)                    
      except ValueError:
          return None

# 디비저장 - 사업용카드
def insert_CostCard_Biz(seq_no,strChkDate,busnCrdcTrsBrkdAdmDVOList):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)  
  i=1
  for item in busnCrdcTrsBrkdAdmDVOList:
    tran_dt = "" 
    if item.get("aprvDt") is not None:tran_dt = item.get("aprvDt")          
    mrntTxprNm = "" 
    if item.get("mrntTxprNm") is not None:mrntTxprNm = item.get("mrntTxprNm").replace('\'','')
    bcNm = "" 
    if item.get("bcNm") is not None:bcNm = item.get("bcNm")
    tfbNm = "" 
    if item.get("tfbNm") is not None:tfbNm = item.get("tfbNm")
    rowSeq = "" 
    if item.get("rowSeq") is not None:rowSeq = item.get("rowSeq")
    crcmClNm = "" 
    if item.get("crcmClNm") is not None:crcmClNm = item.get("crcmClNm")
    busnCrdCardNoEncCntn = "" 
    if item.get("busnCrdCardNoEncCntn") is not None:busnCrdCardNoEncCntn = item.get("busnCrdCardNoEncCntn")
    mrntTxprDscmNoEncCntn = "" 
    if item.get("mrntTxprDscmNoEncCntn") is not None:mrntTxprDscmNoEncCntn = item.get("mrntTxprDscmNoEncCntn")
    splCft = "" 
    if item.get("splCft") is not None:splCft = item.get("splCft")
    vaTxamt = "" #부가세
    if item.get("vaTxamt") is not None:vaTxamt = item.get("vaTxamt")
    tip = "" 
    if item.get("tip") is not None:tip = item.get("tip")
    totaTrsAmt = "" #공급대가
    if item.get("totaTrsAmt") is not None:totaTrsAmt = item.get("totaTrsAmt")
    bmanClNm = "" #사업자유형 /면세사업자/간이과세자/일반사업자/법인사업자
    if item.get("bmanClNm") is not None:bmanClNm = item.get("bmanClNm")
    ddcYnNm = "" 
    if item.get("ddcYnNm") is not None:ddcYnNm = item.get("ddcYnNm")
    vatDdcClNm = "" 
    if item.get("vatDdcClNm") is not None:vatDdcClNm = item.get("vatDdcClNm")
    

    #2025.1.17 부가세가 없는 경우 사업자 유형을 면세사업자로 바꾼다
    if vaTxamt=="" or vaTxamt=="0": 
        bmanClNm = "면세사업자"

    tmpMonth = int(strChkDate)*3-2
    
    if strChkDate=='1' and int(tran_dt[5:7])<tmpMonth: tran_dt = str(int(tran_dt[0:4])+1)+"-01-01"
    if strChkDate=='2' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"04-01"
    if strChkDate=='3' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"07-01"
    if strChkDate=='4' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"10-01"

    workyear = tran_dt[:4]
    sql =  "INSERT INTO Tbl_HomeTax_Scrap (Tran_YY, Tran_Dt, Tran_chkseq, Stnd_GB, bcNm, tfbNm, HomeTaxId, HomeTaxPW"
    sql += " , Biz_No, Seq_No, RowSeq, biz_name, Biz_Card_TY, AprvDt, CrcmClNm, busnCrdCardNoEncCntn, mrntTxprDscmNoEncCntn, mrntTxprNm, splCft, vaTxamt, tip, totaTrsAmt, bmanClNm"
    sql += " , ddcYnNm, vatDdcClNm, VatChkTY, File_DdctGB, Acnt_Cd, Acnt_Nm, Gerenel_Ty, Crt_Dt, Db_Ins_YN, Db_Ins_Dt, File_MK_YN, File_MK_Dt, WK_GB, lawRsn) "
    sql += f" VALUES ('{workyear}','{tran_dt}','{i}','{strChkDate}','{bcNm}','{tfbNm}','{memdeal.hometaxid}','{memdeal.hometaxpw}"
    sql += f"','{memuser.biz_no}','{memuser.seq_no}','{rowSeq}','{memuser.biz_name}','3','{tran_dt}','{crcmClNm}','{busnCrdCardNoEncCntn}"
    sql += f"','{mrntTxprDscmNoEncCntn}','{mrntTxprNm}','{splCft}','{vaTxamt}','{tip}','{totaTrsAmt}','{bmanClNm}"
    sql += f"','{ddcYnNm}','{vatDdcClNm}','57','Y','830','소모품비','','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"','Y','','','','','')"
    with connection.cursor() as cursor:
      cursor.execute(sql)
      connection.commit()  
    i += 1          

# 디비저장 - 복지카드 @@사업용카드에 중복있으면 지우고 복지카드를 남긴다  
def insert_CostCard_Oil(seq_no,strChkDate,busnCrdcTrsBrkdAdmDVOList):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)      
  i=1
  for item in busnCrdcTrsBrkdAdmDVOList:
    tran_dt = "" 
    if item.get("trsDt") is not None:tran_dt = item.get("trsDt")          
    mrntTxprNm = "" 
    if item.get("mrntTxprNm") is not None:mrntTxprNm = item.get("mrntTxprNm").replace('\'','')
    bcNm = "" 
    if item.get("bcNm") is not None:bcNm = item.get("bcNm")
    tfbNm = "" 
    if item.get("tfbNm") is not None:tfbNm = item.get("tfbNm")
    rowSeq = "" 
    if item.get("rowSeq") is not None:rowSeq = item.get("rowSeq")
    crcmClNm = "" 
    if item.get("crccTxprNm") is not None:crcmClNm = item.get("crccTxprNm")
    busnCrdCardNoEncCntn = "" 
    if item.get("wlfCardNoEncCntn") is not None:busnCrdCardNoEncCntn = item.get("wlfCardNoEncCntn")
    mrntTxprDscmNoEncCntn = "" 
    if item.get("mrntTxprDscmNoEncCntn") is not None:mrntTxprDscmNoEncCntn = item.get("mrntTxprDscmNoEncCntn")
    splCft = "" 
    if item.get("splCft") is not None:splCft = item.get("splCft")
    vaTxamt = "" 
    if item.get("vaTxamt") is not None:vaTxamt = item.get("vaTxamt")
    tip = "" 
    if item.get("tip") is not None:tip = item.get("tip")
    totaTrsAmt = "" 
    if item.get("totaTrsAmt") is not None:totaTrsAmt = item.get("totaTrsAmt")
    bmanClNm = "" 
    if item.get("bmanClNm") is not None:bmanClNm = item.get("bmanClNm")
    ddcYnNm = "" 
    if item.get("ddcYnNm") is not None:ddcYnNm = item.get("ddcYnNm")
    vatDdcClNm = "" 
    if item.get("ddcYnNm") is not None:vatDdcClNm = item.get("ddcYnNm")
    
    tmpMonth = int(strChkDate)*3-2
    
    if strChkDate=='1' and int(tran_dt[5:7])<tmpMonth: tran_dt = str(int(tran_dt[0:4])+1)+"-01-01"
    if strChkDate=='2' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"04-01"
    if strChkDate=='3' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"07-01"
    if strChkDate=='4' and int(tran_dt[5:7])<tmpMonth: tran_dt = tran_dt[0:5]+"10-01"

    with connection.cursor() as cursor:
        select_query = f"""
            SELECT 1
            FROM Tbl_HomeTax_Scrap
            WHERE seq_no = {seq_no}
              AND tran_dt = '{tran_dt}'
              AND Biz_Card_TY = 3
              AND busnCrdCardNoEncCntn = '{busnCrdCardNoEncCntn}'
              AND totaTrsAmt = '{totaTrsAmt}'
        """
        # print(select_query)
        cursor.execute(select_query)
        row = cursor.fetchone()

        if row:
            delete_query = f"""
                DELETE FROM Tbl_HomeTax_Scrap
                WHERE seq_no = {seq_no}
                  AND tran_dt = '{tran_dt}'
                  AND Biz_Card_TY = 3
                  AND busnCrdCardNoEncCntn = '{busnCrdCardNoEncCntn}'
                  AND totaTrsAmt = '{totaTrsAmt}'
            """
            # print(delete_query)
            cursor.execute(delete_query)
            connection.commit()
            
    workyear = tran_dt[:4]
    sql =  "INSERT INTO Tbl_HomeTax_Scrap (Tran_YY, Tran_Dt, Tran_chkseq, Stnd_GB, bcNm, tfbNm, HomeTaxId, HomeTaxPW"
    sql += " , Biz_No, Seq_No, RowSeq, biz_name, Biz_Card_TY, AprvDt, CrcmClNm, busnCrdCardNoEncCntn, mrntTxprDscmNoEncCntn, mrntTxprNm, splCft, vaTxamt, tip, totaTrsAmt, bmanClNm"
    sql += " , ddcYnNm, vatDdcClNm, VatChkTY, File_DdctGB, Acnt_Cd, Acnt_Nm, Gerenel_Ty, Crt_Dt, Db_Ins_YN, Db_Ins_Dt, File_MK_YN, File_MK_Dt, WK_GB, lawRsn) "
    sql += f" VALUES ('{workyear}','{tran_dt}','{i}','{strChkDate}','{bcNm}','{tfbNm}','{memdeal.hometaxid}','{memdeal.hometaxpw}"
    sql += f"','{memuser.biz_no}','{seq_no}','{rowSeq}','{memuser.biz_name}','2','{tran_dt}','{crcmClNm}','{busnCrdCardNoEncCntn}"
    sql += f"','{mrntTxprDscmNoEncCntn}','{mrntTxprNm}','{splCft}','{vaTxamt}','{tip}','{totaTrsAmt}','{bmanClNm}"
    sql += f"','{ddcYnNm}','{vatDdcClNm}','57','Y','830','소모품비','','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"','Y','','','','','')"
    with connection.cursor() as cursor:
      cursor.execute(sql)
      connection.commit()  
    i += 1    

# 디비저장 - 신용카드카드매출
def insert_CardSale(seq_no,flagYear,data):
  m_trsDtRngStrt = data.get("qrtFrom") #시작기수
  m_trsDtRngEnd = data.get("qrtTo")    #종료기수
  #신용카드 데이터
  cardRoot = data.get("crdcTrsBrkdMateAdmDVO", {})
  m_card_etcSls = cardRoot.get("etcSls")
  m_card_totaStlAmt = cardRoot.get("totaStlAmt")
  m_card_tip = cardRoot.get("tip")
  m_card_stlScnt = cardRoot.get("stlScnt")
  print(f"카드매출_저장 : {m_card_etcSls} 건, 총금액 {m_card_totaStlAmt}, 공급가액 {m_card_stlScnt}, 팁 {m_card_tip}"  ) 
  # 신용카드매출 상세 리스트
  if int(m_card_totaStlAmt)>0:
    delYYMM=""
    # print(f'작업분기:{m_trsDtRngEnd}')
    if   str(m_trsDtRngEnd)=='1':delYYMM=f"'{flagYear}01','{flagYear}02','{flagYear}03'"
    elif str(m_trsDtRngEnd)=='2':delYYMM=f"'{flagYear}04','{flagYear}05','{flagYear}06'"
    elif str(m_trsDtRngEnd)=='3':delYYMM=f"'{flagYear}07','{flagYear}08','{flagYear}09'"
    elif str(m_trsDtRngEnd)=='4':delYYMM=f"'{flagYear}10','{flagYear}11','{flagYear}12'"  
    cardDetails = data.get("crdcTrsBrkdMateAdmDVOList", [])  
    with connection.cursor() as cursor:
      #일단 지우고
      str_del = "delete from Tbl_HomeTax_SaleCard where seq_no="+ seq_no  + " and Tran_MM in (" + delYYMM  + ") and SaleGubun ='신용카드 자료'"  
      cursor.execute(str_del)
      for d in cardDetails:
        txtYYMM = d.get("stlYm", "")
        txtTitle = d.get("mateKndNm", "")
        txtCnt = str(d.get("stlScnt", 0) or 0)
        txtTotsum = str(d.get("totaStlAmt", 0) or 0)
        txtSincaSale = str(d.get("etcSls", 0) or 0)
        txtPurchase = "0"
        txtFreetax = "0"
        stnd_Gb = '1' if int(txtYYMM[4:6]) <= 3 else '2' if int(txtYYMM[4:6]) <= 6 else '3' if int(txtYYMM[4:6]) <= 9 else '4'

        str_ins = (
            f"INSERT INTO Tbl_HomeTax_SaleCard VALUES ('{txtYYMM[:4]}', '{seq_no}', '{txtTitle}', '{stnd_Gb}', "
            f"'{txtYYMM}', {txtCnt}, {txtTotsum}, {txtTotsum}, {txtPurchase}, {txtFreetax}, GETDATE(), "
            f"isnull((SELECT TOP 1 acnt_cd FROM ds_slipledgr2 WHERE seq_no={seq_no} AND work_yy>{int(flagYear)-5} "
            f"AND acnt_cd>=401 AND acnt_cd<430 GROUP BY acnt_cd ORDER BY COUNT(acnt_cd) DESC),'401'),'','')"
        )
        # print(str_ins)
        cursor.execute(str_ins)

# 디비저장 - 판매대행 데이터
def insert_PMDHSale(seq_no,flagYear,pmdhDetails):
  with connection.cursor() as cursor:
    for d in pmdhDetails:
      txtYYMM = d.get("stlYm", "")
      txtTitle = d.get("txprNm", "")              #대행업체명
      txtCnt = str(d.get("sumStlScnt", 0) or 0)   #집계건수
      txtTotsum = str(d.get("sumTipExclAmt", 0) or 0)   #금액
      txtSincaSale = str(d.get("sumTipExclAmt", 0) or 0) #공급가액이지만 판매대행은 공급대가로 넣는다
      txtPurchase = "0"
      txtFreetax = "0"
      stnd_Gb=0
      if len(txtYYMM)>=6:  
        if int(txtYYMM[4:6])<=3 :					stnd_Gb = '1'
        elif int(txtYYMM[4:6])<=6 :				stnd_Gb = '2'
        elif int(txtYYMM[4:6])<=9 :				stnd_Gb = '3'
        elif int(txtYYMM[4:6])<=12 :				stnd_Gb = '4'

        str_ins = "INSERT INTO Tbl_HomeTax_SaleCard VALUES ('"+txtYYMM[:4]+"', '"+seq_no + "', '" + txtTitle + "', '" + stnd_Gb + "', '"+txtYYMM+"', "+txtCnt+","+ txtTotsum +","+txtSincaSale+","+txtPurchase + "," + txtFreetax + ", GETDATE(),"
        str_ins +="isnull((SELECT TOP 1 acnt_cd  FROM ds_slipledgr2 where seq_no="+ seq_no  + " and work_yy>"+str(int(flagYear)-5)+" and acnt_cd>=401 and acnt_cd<430 GROUP BY acnt_cd ORDER BY COUNT(acnt_cd) DESC),'401'),'','')"
        # print(str_ins)
        cursor.execute(str_ins)   

# 디비저장 - 현금영수증 매입
def insert_CashCost(seq_no,flagYear,list_element):
  memuser = MemUser.objects.get(seq_no=seq_no)    
  with connection.cursor() as cursor:
    for item in list_element:
      m_trsDtm = ""                   # 거래일시
      if item.get("trsDtTime")  is not None:m_trsDtm =  item.get("trsDtTime")[:10]
      m_aprvNo = ""                   # 승인번호
      if item.get("aprvNo")  is not None:m_aprvNo =  item.get("aprvNo") 
      m_trsClNm =""                   # 승인거래
      if item.get("trsClNm")  is not None:m_trsClNm =  item.get("trsClNm") 
      m_spstCnfrClNm = ""             #발행수단 : 휴대번호/사업자
      if item.get("spstCnfrClNm")  is not None:m_spstCnfrClNm =  item.get("spstCnfrClNm")
      m_mrntTxprDscmNoEncCntn = ""    # 상대방사업자번호
      if item.get("mrntTxprDscmNoEncCntn")  is not None:m_mrntTxprDscmNoEncCntn =  item.get("mrntTxprDscmNoEncCntn")
      m_mrntTxprNm = ""               # 상대방상호호
      if item.get("mrntTxprNm")  is not None:m_mrntTxprNm =  item.get("mrntTxprNm").replace("'","")
      m_splCft = 0                    # 공급가액
      if item.get("splCft")  is not None:m_splCft =  int(item.get("splCft"))
      m_vaTxamt = 0                   # 세액
      if item.get("vaTxamt")  is not None:m_vaTxamt =  int(item.get("vaTxamt"))
      m_tip = 0                       # 봉사료
      if item.get("tip")  is not None:m_tip =  int(item.get("tip") )
      m_totaTrsAmt = 0                # 합계
      if item.get("totaTrsAmt")  is not None:m_totaTrsAmt =  int(item.get("totaTrsAmt") )
      m_bmanClNm = ""                 # 가맹점 유형
      if item.get("bmanClNm")  is not None:m_bmanClNm =  item.get("bmanClNm") 
      m_ddcYnNm = ""                  # 공제여부 결정  prhTxamtDdcClNm
      if item.get("ddcYnNm")  is not None:m_ddcYnNm =  item.get("ddcYnNm") 
      m_vatDdcClNm = ""               # 선택불공제/일반
      if item.get("vatDdcClNm")  is not None:m_vatDdcClNm =  item.get("vatDdcClNm") 
      if m_trsClNm=="취소거래" and m_splCft>0:
              m_splCft = m_splCft * -1
              m_vaTxamt = m_vaTxamt * -1
              m_tip = m_tip * -1
              m_totaTrsAmt = m_totaTrsAmt * -1          
      sql =  f"INSERT INTO Tbl_HomeTax_CashCost VALUES ('{ m_trsDtm}'"
      sql += f",isnull((select max(rowSeq)+1 from Tbl_HomeTax_CashCost where seq_no={seq_no} and left(tran_dt,4)={flagYear} and stnd_GB='{utils.get_quarter(m_trsDtm[5:7])}'),0)"
      sql += f",'{utils.get_quarter(m_trsDtm[5:7])}','{memuser.biz_no}','{seq_no}','{memuser.biz_name}','{m_aprvNo}','{m_trsClNm}','{m_spstCnfrClNm}'"
      sql += f",'{m_mrntTxprDscmNoEncCntn}','{m_mrntTxprNm}','{m_splCft}','{m_vaTxamt}','{m_tip}','{m_totaTrsAmt}','{m_bmanClNm}'"
      sql += f",'{m_ddcYnNm}','{m_vatDdcClNm}','61','공제','830','소모품비',getdate(),'N','','','')"
      print(sql)
      cursor.execute(sql)

# 디비저장 - 현금영수증 세부매출 - 사용안함
def insert_CashSale2(seq_no,flagYear,list_element):
  memdeal = MemDeal.objects.get(seq_no=seq_no)  
  memuser = MemUser.objects.get(seq_no=seq_no)  
  for item in list_element:
        m_trsDtm = "" 
        if item.get("trsDtm")  is not None:m_trsDtm =  item.get("trsDtm") 
        m_cshptTrsTypeNm = ""           #거래종류 
        if item.get("cshptTrsTypeNm")  is not None:m_cshptTrsTypeNm =  item.get("cshptTrsTypeNm") 
        m_splCft = 0                    # 공급가액
        if item.get("splCft")  is not None:m_splCft =  item.get("splCft") 
        m_vaTxamt = 0                   # 세액
        if item.get("vaTxamt")  is not None:m_vaTxamt =  item.get("vaTxamt") 
        m_tip = 0                       # 봉사료
        if item.get("tip")  is not None:m_tip =  item.get("tip") 
        m_totaTrsAmt = 0                # 합계
        if item.get("totaTrsAmt")  is not None:m_totaTrsAmt =  item.get("totaTrsAmt") 
        m_aprvNo = ""                   # 승인번호
        if item.get("aprvNo")  is not None:m_aprvNo =  item.get("aprvNo") 
        m_trsClNm = ""                 #승인거래
        if item.get("trsClNm")  is not None:m_trsClNm =  item.get("trsClNm") 
        m_trsClCd = ""                 #
        if item.get("trsClCd")  is not None:m_trsClCd =  item.get("trsClCd")
        m_pblClCd = ""                 #사업자 
        if item.get("pblClCd")  is not None:m_pblClCd =  item.get("pblClCd")
        m_spstCnfrPartNo = ""          #0901
        if item.get("spstCnfrPartNo")  is not None:m_spstCnfrPartNo =  item.get("spstCnfrPartNo")
        m_rcprTxprNm = ""              #매출은 거래상대방 매입은 나자신
        if item.get("rcprTxprNm")  is not None:m_rcprTxprNm =  item.get("rcprTxprNm").replace("'","")
        m_spstCnfrClNm=""                #발행수단 : 휴대번호/사업자
        if item.get("spstCnfrClNm")  is not None:m_spstCnfrClNm =  item.get("spstCnfrClNm")
        m_cshptUsgClNm = ""              #발행종류 : 지출증빙/소득공제    매입은 없음
        if item.get("cshptUsgClNm")  is not None:m_cshptUsgClNm =  item.get("cshptUsgClNm")

        if m_trsClNm=="취소거래" and m_splCft>0:
            m_splCft = m_splCft * -1
            m_vaTxamt = m_vaTxamt * -1
            m_tip = m_tip * -1
            m_totaTrsAmt = m_totaTrsAmt * -1

        sql =  f"INSERT INTO Tbl_HomeTax_CashSale VALUES ('{m_trsDtm}'"
        sql += f",isnull((select max(rowSeq)+1 from Tbl_HomeTax_CashCost where seq_no={seq_no} and left(tran_dt,4)={flagYear} and stnd_GB='{utils.get_quarter(m_trsDtm[5:7])}'),0)"
        sql += f",'{utils.get_quarter(m_trsDtm[5:7])}','{seq_no}','{memuser.biz_name}','{m_cshptTrsTypeNm}','{m_splCft}','{m_vaTxamt}'"
        sql += f",'{m_tip}','{m_totaTrsAmt}','{m_aprvNo}','{m_trsClNm}','{m_trsClCd}','{m_pblClCd}','{m_spstCnfrPartNo}'"
        sql += f",'{m_rcprTxprNm}','{m_spstCnfrClNm}','{m_cshptUsgClNm}',getdate())"
        # print(sql)
        with connection.cursor() as cursor:  
          cursor.execute(sql)
          connection.commit() 

