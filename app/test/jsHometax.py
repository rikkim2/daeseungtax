import time
import requests
import json
import urllib.parse
import http.client
import http.cookiejar
import urllib.request
from app.test import utils
from xml.etree import ElementTree

HTTP_timeout = 3000
HTTP_UserAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"

_HTTP_ContextType_GET = None
_HTTP_ContextType_POST = "application/x-www-form-urlencoded"
_HTTP_ContextType_XML = "application/xml; charset=UTF-8"
rst = 0
global sbResponseData
global sbSession   #셀레늄방식에서 전환하기 때문에 세션을 이동시켜줘야한다
sbResponseData = ""
sbSession = None
strResData = ""
sbSSOToken = ""
sbuserClCd = ""
sbTxaaAdmNo = ""
TEETsessionID = ""
TXPPsessionID = ""
TEHTsessionID = ""
WMONID = ""

class LoginSystemContext:

    def __init__(self):
        self.m_code = None
        self.m_errCode = None
        self.m_errMsg = None
        self.m_lgnRsltCd = None
        self.m_pswdErrNbcnt = None
        self.m_tin = None
        self.m_secCardId = None

    def copyTo(self, ctx):
        ctx.m_code = self.m_code
        ctx.m_errCode = self.m_errCode
        ctx.m_errMsg = self.m_errMsg
        ctx.m_lgnRsltCd = self.m_lgnRsltCd
        ctx.m_pswdErrNbcnt = self.m_pswdErrNbcnt
        ctx.m_secCardId = self.m_secCardId
        ctx.m_tin = self.m_tin

    def copyFrom(self, ctx):
        self.m_code = ctx.m_code
        self.m_errCode = ctx.m_errCode
        self.m_errMsg = ctx.m_errMsg
        self.m_lgnRsltCd = ctx.m_lgnRsltCd
        self.m_pswdErrNbcnt = ctx.m_pswdErrNbcnt
        self.m_secCardId = ctx.m_secCardId
        self.m_tin = ctx.m_tin

mSession_cookiecontainer = {}
mLoginSystem = {}
mLoginSystem_Main = LoginSystemContext()

class JsHometax:
  def __init__(self, parent):
          
      self.mSession_cookiecontainer = parent.mSession_cookiecontainer
      self.mLoginSystem = parent.mLoginSystem
      self.mLoginSystem_Main = parent.mLoginSystem_Main

  def new_login(id, password):
      global sbSession
      global TXPPsessionID 
      global WMONID
      loginsysCode = ""
      loginsysctx = LoginSystemContext()

      url = "https://www.hometax.go.kr/pubcLogin.do?domain=hometax.go.kr&mainSys=Y"
      password_safe = password.replace("＃", "#")

      headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Referer': 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml',
          'User-Agent': 'Mozilla/5.0'
      }
   
      postdata = "ssoLoginYn=Y&secCardLoginYn=&secCardId=&id=" + urllib.parse.quote(id) + "&pswd=" + password_safe + "&ssoStatus=&portalStatus=&scrnId=UTXPPABA01&userScrnRslnXcCnt=1280&userScrnRslnYcCnt=960"

      sbSession = requests.Session()
      response = sbSession.post(url, data=postdata, headers=headers)
      if "nts_loginSystemCallback" in response.text:
          print("✅ 로그인 성공",response.text)
          
          # url = "https://www.hometax.go.kr/pubcLogin.do?domain=hometax.go.kr&mainSys=Y"

          # headers = {
          #     "User-Agent": "Mozilla/5.0",
          #     "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
          #     "Referer": "https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml",
          #     "X-Requested-With": "XMLHttpRequest"
          # }

          # payload = {
          #     "domain": "hometax.go.kr",
          #     "mainSys": "Y"
          # }
          # response = sbSession.post(url, data=postdata, headers=headers)
          # print("✅ 로그인 성공2",response.text)


          # 쿠키를 추출해서 저장 (예: TXPPsessionID, WMONID)
          cookies = sbSession.cookies.get_dict()
          print("🍪 세션 쿠키 목록:", cookies)

          WMONID = cookies.get("WMONID")
          TXPPsessionID = cookies.get("TXPPsessionID")     

          # pkcEncSsn = get_pkcEncSsn(response)
          # print(pkcEncSsn)
          return sbSession, TXPPsessionID, WMONID
      else:
          print("❌ 로그인 실패 또는 응답 포맷 오류")
          print(response.text)
          return None, None, None

  def sellenium_login(htxLoginID,isNotShowChrome):
    global TEETsessionID 
    global TXPPsessionID 
    global TEHTsessionID 
    global sbSession
    try:
        # WebSquare 페이지로 이동
        driver = utils.conHometaxLogin(htxLoginID,isNotShowChrome) 
        driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml")
        time.sleep(3)
        cookies = driver.get_cookies()
        sbSession = requests.Session()
        for cookie in driver.get_cookies():
            sbSession.cookies.set(cookie['name'], cookie['value'])
        # print(f"✅ TXPPsessionID: {txpp_session_id}")
        TEETsessionID = next((cookie['value'] for cookie in cookies if cookie['name'] == 'TEETsessionID'), None)
        TEHTsessionID = next((cookie['value'] for cookie in cookies if cookie['name'] == 'TEHTsessionID'), None)
        TXPPsessionID = next((cookie['value'] for cookie in cookies if cookie['name'] == 'TXPPsessionID'), None)

        mLoginSystem_Main.m_code = "S"
        mLoginSystem_Main.m_errCode = None
        mLoginSystem_Main.m_errMsg = None
        mLoginSystem_Main.m_lgnRsltCd = "01"
        mLoginSystem_Main.m_pswdErrNbcnt = "0"
        mLoginSystem_Main.m_tin = None
        mLoginSystem_Main.m_secCardId = None

        # 2. Permission 요청 (token.do 접근을 위한 permission 확보)
        referer_url = "https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml"
        screen_id = "index"
        subdomain = "www"
        rst = requestPermission(referer_url, subdomain, screen_id, None, None, None, None, None)
        if rst != 1:
            raise Exception(f"Permission 실패: {getErrorString(rst)}")        
        rstSSOToken = getSSOToken_TaxAdm(referer_url)
        if rstSSOToken != 1:
            raise Exception("ssoToken 추출 실패")

        return rstSSOToken
    except Exception as e:
        print(f"❌ Selenium 오류: {e}")
        return -1
    finally:
        driver.quit()  

  def sellenium_login2(htxLoginID, isNotShowChrome):
      global sbSession
      try:
          # WebSquare 페이지로 이동
          driver = utils.conHometaxLogin(htxLoginID, isNotShowChrome)
          driver.get("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml")
          time.sleep(3)
          cookies = driver.get_cookies()
          sbSession = requests.Session()
          for cookie in cookies:
              sbSession.cookies.set(cookie['name'], cookie['value'], domain=".hometax.go.kr")
          print("🍪1. 로그인 쿠키 설정 후 session.cookies:", sbSession.cookies.get_dict())

          referer_url = "https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml"
          rstSSOToken = getSSOToken_TaxAdm(referer_url)
          if rstSSOToken != 1:
              raise Exception("ssoToken 추출 실패")
          return sbSession  # 세션 객체 반환
      except Exception as e:
          print(f"❌ Selenium2 오류: {e}")
          return None
      finally:
          driver.quit()

  def login(id, password, result_LoginSystemCtx):
      global sbResponseData
      url = "https://www.hometax.go.kr/pubcLogin.do?domain=hometax.go.kr&mainSys=Y"
      pos = [0, 0, 0, 0]
      loginsysCode = ""
      loginsysctx = LoginSystemContext()
      
      flag = 0
      password_safe = password.replace("＃", "#")
      postdata = {
          'ssoLoginYn': 'Y',
          'secCardLoginYn': '',
          'secCardId': '',
          'id': id,
          'pswd': password_safe,
          'ssoStatus': '',
          'portalStatus': '',
          'scrnId': 'UTXPPABA01',
          'userScrnRslnXcCnt': '1280',
          'userScrnRslnYcCnt': '960'
      }

      headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Referer': 'https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml',
          'User-Agent': 'Mozilla/5.0'
      }
   
      postdata = "ssoLoginYn=Y&secCardLoginYn=&secCardId=&id=" + urllib.parse.quote(id) + "&pswd=" + password_safe + "&ssoStatus=&portalStatus=&scrnId=UTXPPABA01&userScrnRslnXcCnt=1280&userScrnRslnYcCnt=960"
      rst = httpRequest_post(url, postdata, "https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml", None, _HTTP_ContextType_POST, 'login')
      strResData = sbResponseData
      # print("IN LOGIN : ")
      # print(strResData)
      # while True:
      str = ["", "", "", ""]
      
      pos[0] = strResData.find("nts_loginSystemCallback")
      # if pos[0] < 0:  break
      pos[0] += 23
      pos[1] = getTagEndPos(strResData, pos[0], '(', ')')
      print(pos[1]) # [" 'code' : 'S', 'errCode' : null, 'errMsg' : decodeURIComponent('').replace(/\\+/g,' ').replace(/\\\\n/g,'\\n'), 'lgnRsltCd' : '01', 'pswdErrNbcnt' : '0', 'tin' : '100000000030598298', 'secCardId' : null"]
      # if pos[0] < 0:    break
      pos[0] += 1
      pos[1] -= 1
      # print(pos[1])#[" 'code' : 'S', 'errCode' : null, 'errMsg' : decodeURIComponent('').replace(/\\+/g,' ').replace(/\\\\n/g,'\\n'), 'lgnRsltCd' : '01', 'pswdErrNbcnt' : '0', 'tin' : '100000000030598298', 'secCardId' : null"]
      str[0] = strResData[pos[0]:pos[1]]
      pos[0] = str[0].find("{")
      # if pos[0] < 0:    break
      loginsysCode = str[0][:pos[0]].replace("'", "").replace(",", "").strip()
      pos[0] += 1
      pos[1] = str[0].find("}", pos[0])
      # if pos[1] < 0:  break
      str[2] = str[0][pos[0]:pos[1]]
      strarr = str[2].split('\r\n,')
      strarr = strarr[0].replace("/g,","").split(',')
      flag |= 0x00000001
      for tmpstr in strarr:
          strarr2 = tmpstr.split(':')
          tmpname = ""
          tmpvalue = ""
          if len(strarr2) < 2:   continue
          tmpname = strarr2[0].replace("'", "").strip().lower()
          tmpvalue = strarr2[1].strip()

          if tmpname == "code":
              loginsysctx.m_code = tmpvalue.replace("'", "").strip()
              flag |= 0x00000010
          elif tmpname == "errcode":
              loginsysctx.m_errCode = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_errCode.lower() == "null":
                  loginsysctx.m_errCode = None
              flag |= 0x00000020
          elif tmpname == "errmsg":
              pos[2] = tmpvalue.find("'")
              if pos[2] >= 0:
                  pos[2] += 1
                  pos[3] = tmpvalue.find("'", pos[2])
              if pos[2] >= 0 and pos[3] >= 0:
                  loginsysctx.m_errMsg = requests.utils.unquote(tmpvalue[pos[2]:pos[3]])
                  flag |= 0x00000040
          elif tmpname == "ignrsltcd":
              loginsysctx.m_lgnRsltCd = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_lgnRsltCd.lower() == "null":
                  loginsysctx.m_lgnRsltCd = None
          elif tmpname == "pswderrnbcnt":
              loginsysctx.m_pswdErrNbcnt = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_pswdErrNbcnt.lower() == "null":
                  loginsysctx.m_pswdErrNbcnt = None
          elif tmpname == "tin":
              loginsysctx.m_tin = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_tin.lower() == "null":
                  loginsysctx.m_tin = None
          elif tmpname == "seccardid":
              loginsysctx.m_secCardId = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_secCardId.lower() == "null":
                  loginsysctx.m_secCardId = None
          flag |= 0x00000080

      if flag != 0x000000F1:    return -1
      if result_LoginSystemCtx is not None:    result_LoginSystemCtx.copyFrom(loginsysctx)
      if loginsysctx.m_code.upper() == "S":
          result_errorCd = 0
          result_errorMsg = None
          if loginsysCode.upper() == "TXPP":
              # 메인 시스템일 경우 성공 로그인 정보 저장
              mLoginSystem_Main.copyFrom(loginsysctx)
          rst = requestPermission("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml", "www", "index", None, None, None, result_errorCd, result_errorMsg)
          return 1
      else:
          return 0
        
def getLoginStatus():
    if mLoginSystem_Main is None:                   return False
    if mLoginSystem_Main.m_code is None:            return False
    if mLoginSystem_Main.m_code.upper() == "S":
      return True
    else:
      return False

def requestPermission(refererurl, subdomain, screenId, domain, ssoToken, userClCd, result_errorCd, result_errorMsg):
    url = f"https://{subdomain}.hometax.go.kr/permission.do?screenId={urllib.parse.quote(screenId)}"
    rst = 0
    sbResponseData = ""
    if not getLoginStatus():   
        return -10
    if domain is not None:     url += f"&domain={urllib.parse.quote(domain)}"
    # print(f'ssoToken : {ssoToken}')
    # print(f'userClCd : {userClCd}')
    postdata = {
        "popupYn": "",
        "ssoToken": ssoToken,
        "userClCd": userClCd
    }
    if subdomain == "www":      
        rst = httpRequest_post(url, postdata, refererurl, "https://www.hometax.go.kr", "application/json", sbResponseData)
    else:                       
        rst = httpRequest_post(url, postdata, refererurl, "https://{subdomain}.hometax.go.kr", "application/json", sbResponseData)
    return rst

def httpRequest_post(url, postdata, refererUrl, originUrl, contentType, tmp):
    global sbResponseData
    global TEHTsessionID
    global WMONID
    try:
        if contentType=="application/json":
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # 요청 데이터 (예시)
            data = {
                "key1": "value1",
                "key2": "value2"
            }

            # POST 요청 보내기
            response = requests.post(url,headers=headers, cookies=mSession_cookiecontainer, json=postdata)   
            mSession_cookiecontainer.update(response.cookies.get_dict())
            print("httpRequest_post:"+response.text)
            
            cookies = response.cookies.get_dict()
            print(f"jsHometax의 httpRequest_post의 쿠키 : {cookies}")
            if 'TEHTsessionID' in cookies:
                TEHTsessionID = cookies['TEHTsessionID']
            if 'WMONID' in cookies:
                WMONID = cookies['WMONID']
            sbResponseData = response.text                     
        else:
            params = urllib.parse.urlencode({'': postdata})
            headers = {
                'Content-type': contentType,
                'Referer': refererUrl,
                'User-Agent': 'Mozilla/5.0'
            }
            if originUrl is not None:            headers['Origin'] = originUrl
            response = requests.post(url, data=postdata.encode('ascii'), headers=headers, cookies=mSession_cookiecontainer)

            mSession_cookiecontainer.update(response.cookies.get_dict())
            # print("httpRequest_post:"+response.text)
            # print(response.cookies.get_dict())
            sbResponseData = response.text
        return 1
    except:
        return -1

def httpRequest_get(url, refererUrl, originUrl, tmp):
    global sbResponseData
    try:
        headers = {
            "User-Agent": HTTP_UserAgent,
            "Referer": refererUrl
        }
        cookies = mSession_cookiecontainer
        if originUrl is not None:
            headers["Origin"] = originUrl

        response = requests.get(url, headers=headers, cookies=cookies, timeout=HTTP_timeout)
        # print("httpRequest_get")
        # print(response.text)
        if response.status_code == 200:
            sbResponseData = response.text
            return 1
        else:
            return -1001
    except:
        return -1

def getTagEndPos(string, startpos, begin_tag, end_tag):
    curpos = string.find(begin_tag, startpos)
    if curpos < 0:
        return -1

    dimen = 1
    curpos += 1

    while dimen > 0:
        pos_a = string.find(begin_tag, curpos)
        pos_b = string.find(end_tag, curpos)

        if pos_a < 0:
            if pos_b >= 0:
                dimen -= 1
                curpos = pos_b + 1
                continue
            else:
                break  # ERROR

        if pos_b < pos_a:
            dimen -= 1
        else:
            dimen += 1

        curpos = min(pos_a, pos_b) + 1

    if dimen > 0:
        return -1

    return curpos

#최초 로그인시 pkcEncSsn 획득
def get_pkcEncSsn(rstSSOToken):
    global WMONID
    ### 값 설정
    url = 'https://hometax.go.kr/wqAction.do?actionId=ATXPPZXA001R01&screenId=UTXPPABA01'
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=58&tm2lIdx=&tm3lIdx=",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Cookie": f"NTS_LOGIN_SYSTEM_CODE_P=TXPP; TXPPsessionID={TXPPsessionID}; WMONID={WMONID}"
    }
    print(headers)
    res = sbSession.post(url=url, headers=headers)
    print(res.json())
    ### 지정 pkcEncSsn
    root = ElementTree.fromstring(res.content) ### xml
    pkcEncSsn = root.find("pkcEncSsn").text
    
    ### 지정 WMONID
    WMONID = res.cookies.get_dict()['WMONID'] ### cookie

    return pkcEncSsn 

#수임자 전환
def switch_to_afa_biz( afa_info):
    url = "https://teet.hometax.go.kr/wqAction.do?actionId=ATEETZAA002R02&screenId=UTEETZZA21&popupYn=true&realScreenId="

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml",
        "Origin": "https://hometax.go.kr",
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"TEETsessionID={TEETsessionID}; WMONID={WMONID};"
    }

    payload = {
        "afaBmanRprsFnm": afa_info.get("rprsFnm"),    # 대표자명 없어도 됨
        "afaBmanTin": afa_info.get("afaBmanTin"),
        "afaBmanTxprDscmNo": afa_info.get("bsno"), # 사업자등록번호 없어도 됨
        "afaBmanTxprNm":afa_info.get("txprNm"),     # 법인명 없어도 됨
        "agrYn": "Y",
        "prxBsno": "",
        "txaaCnvrYn": "",
        "pageInfoVO": {
            "pageNum": "1",
            "pageSize": "10",
            "totalCount": "2"
        },
        "ntsData": sbSSOToken
    }
    print(payload)
    response = sbSession.post(url, headers=headers, json=payload)
    print(response)
    print("🔍 수임자전환 상태코드:", response.status_code)
    # print("🔍 수임자전환 응답:", response.text)

    if response.status_code == 200:
        data = response.json()
        if data.get("resultMsg", {}).get("result") == "S":
            print("✅ 수임자 전환 성공")
            return True
        else:
            print("❌ 수임자 전환 실패:", data.get("resultMsg", {}).get("msg"))
            return False
    else:
        raise Exception("수임자 전환 실패: " + str(response.status_code))

# 수임납세자 전환용 Tin + 기본 정보 얻기
def get_afaBmanTin(flag, flagNo, biz_name,ceo_name):
    prxBsno = flagNo;DscmNo = "";BmanTxprNm = biz_name; RprsFnm = ""
    if flag=="ssn":
        prxBsno = "";DscmNo = flagNo;BmanTxprNm = ""; RprsFnm = ceo_name
    url = "https://teet.hometax.go.kr/wqAction.do?actionId=ATEETZAA002R02&screenId=UTEETZZA21&popupYn=true&realScreenId="
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml",
        "Origin": "https://hometax.go.kr",
        "Cookie": f"TEETsessionID={TEETsessionID}; WMONID={WMONID}; NTS_REQUEST_SYSTEM_CODE_P=TEET"
    }

    payload = {
        "afaBmanRprsFnm": ceo_name,
        "afaBmanTin": "",
        "afaBmanTxprDscmNo": DscmNo,
        "afaBmanTxprNm": "",
        "agrYn": "",
        "prxBsno": prxBsno,
        "txaaCnvrYn": "",
        "pageInfoVO": {
            "pageNum": "1",
            "pageSize": "10",
            "totalCount": "1278"
        },
        "ntsData": sbSSOToken 
    }
    print(payload)
    response = sbSession.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            rows = result.get("afdsSttnInfrDVOList", [])
            # print(rows)
            if not rows:
                print("❌ 수임자 데이터 없음")
                return {}

            # 수임자 1개만 추출
            first_row = rows[0]
            print(first_row)
              
            # afa_info = {
            #     "afaBmanTin": first_row.get("afaBmanTin"),
            #     "bsno": first_row.get("bsno"),
            #     "rprsFnm": first_row.get("rprsFnm"),       #대표자
            #     "txprNm": first_row.get("txprNm"),        #상호
            # }
            afa_info = {
                "afaBmanTin": first_row.get("afaBmanTin"),      # 수임자 TIN
                "bsno": first_row.get("bsno"),                  # 사업자등록번호
                "rprsFnm": first_row.get("rprsFnm"),            # 대표자 성명
                "txprNm": first_row.get("txprNm"),              # 상호명
                "txaaId": first_row.get("txaaId"),              # 수임등록번호
                "taPrxClntClCd": first_row.get("taPrxClntClCd"),# 수임유형코드 (예: 01: 기장)
                "rnum": first_row.get("rnum"),# ntplOrgClCd
                "bmanStatCdNm": first_row.get("bmanStatCdNm"),  # 사업자상태 (예: 계속사업자)
                "afaClCd": first_row.get("afaClCd"),            # 수임구분 (예: 기장대리수임)
                "searchLstAltDtm": first_row.get("searchLstAltDtm"),  # 조회일시
                "statusValue": first_row.get("statusValue"),    # 상태값
                # 필요시 추가 필드
                "rprsResno": first_row.get("rprsResno"),        # 대표자 주민번호 (마스킹)
                "tnmNm": first_row.get("tnmNm"),                # 세무대리인명
                "telno": first_row.get("telno"),                # 전화번호
                "fnm": first_row.get("fnm"),                    # 대표 이름 또는 세무사 이름
                "clnttnmnm": first_row.get("clnttnmnm"),        # 클라이언트명?
                "txaaAdmNo": first_row.get("txaaAdmNo"),        # 수임자 관리번호 (있다면)
                "txaaresno": first_row.get("txaaresno"),        # 수임자 주민번호 (있다면)
            }            

            print(f"🔍 추출된 수임자 정보: {afa_info}")
            return afa_info

        except Exception as e:
            print(f"❌ JSON 파싱 오류: {e}")
            return {}
    else:
        print(f"❌ 요청 실패: {response.status_code}")
        print(response.text)
        return {}

def getTEETsession_WMONID():
    global TEETsessionID
    global WMONID

    ### 수임납세자 정보조회 접근권 허가
    url = 'https://teet.hometax.go.kr/permission.do?screenId=UTEETBDA03&domain=hometax.go.kr'
    payload = f"<map id='postParam'><ssoToken>{sbSSOToken}</ssoToken><userClCd>{sbuserClCd}</userClCd><txaaAdmNo>{sbTxaaAdmNo}</txaaAdmNo><popupYn>false</popupYn></map>"
    ## 요청
    res= requests.post(url = url, data = payload)
    print(res.cookies.get_dict())
    ### 지정 TEETsessionID
    TEETsessionID = res.cookies.get_dict()['TEETsessionID']
    WMONID = res.cookies.get_dict()['WMONID']
    print(f"6. WMONID 세션 받기 : {WMONID}")
    return 1

def getSSOToken_TaxAdm(refererurl):
    global sbResponseData
    global sbSSOToken   
    global sbuserClCd 
    global sbTxaaAdmNo
    url = "https://www.hometax.go.kr/token.do"

    rst = 0
    sbResponseData = ""
    strResData = ""
    strdata = ""
    # if not getLoginStatus():        return -10

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": refererurl
    }

    response = sbSession.get(url, headers=headers)
    # strResData = sbResponseData
    # strdata = json.loads(response)
    strdata = response.json()
    
    sso_token = strdata.get("ssoToken")
    # print(f"sso_token:{sso_token}")
    if len(sso_token) == 0 or sso_token.lower() == "null":
        return -10131
    sbSSOToken = sso_token
    userClCd = strdata.get("userClCd")
    # print(f"userClCd:{userClCd}")
    if len(userClCd) == 0 or userClCd.lower() == "null":
        return -10132
    sbuserClCd = userClCd
    txaaAdmNo = strdata.get("txaaAdmNo")
    # print(f"txaaAdmNo:{txaaAdmNo}")
    if len(txaaAdmNo) == 0 or txaaAdmNo.lower() == "null":
        return -10133
    sbTxaaAdmNo = txaaAdmNo
    return 1

def getSSOToken(refererurl):
    global sbResponseData
    global sbSSOToken   
    global sbuserClCd 
    url = "https://www.hometax.go.kr/token.do"

    rst = 0
    sbResponseData = ""
    strResData = ""

    strdata = ""

    pos_a = 0
    pos_b = 0

    if not getLoginStatus():        return -10

    rst = httpRequest_get(url, refererurl, None, sbResponseData)
    strResData = sbResponseData

    strdata = json.loads(strResData)
    sso_token = strdata.get("ssoToken")
    if len(sso_token) == 0 or sso_token.lower() == "null":
        return -10131
    sbSSOToken = sso_token
    userClCd = strdata.get("userClCd")
    if len(userClCd) == 0 or userClCd.lower() == "null":
        return -10132
    sbuserClCd = userClCd

    return 1

def getErrorString(errno):
    if errno == 1:
        return "성공"
    elif errno == 0:
        return "실패"
    elif errno == -1:
        return "기타오류"
    elif errno == -10:
        return "사용할 수 없는 상태입니다. 로그인 상태를 확인해주세요."
    elif errno == -1001:
        return "HTTP오류. 페이지를 찾을 수 없습니다."
    elif errno == -10000:
        return "파싱오류"
    elif errno == -10131:
        return "ssoToken 읽기 실패. 세션이 올바르지 않는 것으로 보입니다."
    elif errno == -10132:
        return "userClCd 읽기 실패. 세션이 올바르지 않는 것으로 보입니다."
    else:
        return "알수없는코드"
