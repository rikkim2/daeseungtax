#####################################
#     세무대리 정보조회
#####################################


from datetime import datetime
import time
import requests
from app.test import jsHometax
from django.db import connection
from app.test import utils

def login_and_get_sso(htxLoginID, isNotShowChrome, 
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
        driver = utils.conHometaxLogin(htxLoginID, isNotShowChrome)
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
            raise RuntimeError("token.do 응답이 JSON이 아님")

        sso_token = str(data.get("ssoToken", "") or "")
        userClCd  = str(data.get("userClCd", "") or "")
        txaaAdmNo = str(data.get("txaaAdmNo", "") or "")

        if not sso_token or sso_token.lower() == "null":
            raise RuntimeError("ssoToken 추출 실패(-10131)")
        if not userClCd or userClCd.lower() == "null":
            raise RuntimeError("userClCd 추출 실패(-10132)")
        if not txaaAdmNo or txaaAdmNo.lower() == "null":
            raise RuntimeError("txaaAdmNo 추출 실패(-10133)")

        result = {
            "session": sess,
            "ssoToken": sso_token,
            "userClCd": userClCd,
            "txaaAdmNo": txaaAdmNo,
            "cookies": sess.cookies.get_dict()
        }
        return result

    except Exception as e:
        raise RuntimeError(f"로그인/토큰 처리 실패: {e}") from e
    finally:
        try:
            if driver is not None:
                driver.quit()
        except Exception:
            pass


def get_txaaID(login_session,actionId):
    # 본페이지 접근 전 txaaId 등을 얻는다
    try:
        url = f"https://hometax.go.kr/wqAction.do?actionId={actionId}&screenId=index_pp&popupYn=false&realScreenId="
        Referer_url="https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": "https://hometax.go.kr",
            "Referer": Referer_url,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"'
        }

        # 실제 요청은 POST + 빈 JSON 본문
        response = login_session.post(url, headers=headers, json={})
        print("📥 응답코드:", response.status_code)

        # JSON 파싱
        data = response.json()
        session_map = data.get("resultMsg", {}).get("sessionMap", {})

        # 주요 항목 출력
        print("📌 사용자ID:", session_map.get("userId"))
        print("📌 수임번호 txaaId:", session_map.get("txaaId"))
        print("📌 수임자관리번호 txaaAdmNo:", session_map.get("txaaAdmNo"))
        print("📌 전환여부 afaTxprYn:", session_map.get("afaTxprYn"))

        return session_map

    except Exception as e:
        print(f"❌ txaaID 권한 정보 조회 실패: {e}")
        return None

def get_permission(session,screenId,domain,Referer_url):
    url = f"https://{domain}.hometax.go.kr/permission.do?screenId={screenId}"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json; charset=UTF-8",
        "Origin": "https://hometax.go.kr",
        "Referer": Referer_url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    try:
        res = session.post(url, headers=headers, json={})
        print(f"📥 {domain} permission 응답코드:", res.status_code)
        print(f"📄 {domain} permission 응답 본문:", res.text[:300])  # 일부 미리보기
        
        data = res.json()
        resultMsg = data.get("resultMsg", {}).get("serverProperty", {})
        
        print("📌 systemCode:", resultMsg.get("systemCode"))
        return resultMsg.get("systemCode")

    except Exception as e:
        print(f"❌ {domain} permission 실패:", e)
        return None
    
# 세무대리 > 기장대리 권한획득
def get_KijangDari(login_Session,Referer_url,actionId,scrnId):
    url = f"https://hometax.go.kr/wqAction.do?actionId={actionId}&screenId=index_pp&popupYn=false"
    headers = {
        "Accept": "application/json; charset=UTF-8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://hometax.go.kr",
        "Referer": Referer_url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    # ✅ 요청 payload
    payload = {
        "scrnId":scrnId,
        "pageInfoVO": {
            "totalCount": "0",
            "pageSize": "10",
            "pageNum": "1"
        }
    }
    if actionId=="ATXPPAAA001R037":
        payload = {"ttxppal032DVO":{"menuId":""}}
    response = login_Session.post(url, headers=headers, json=payload)
    data = response.json()
    session_map = data.get("resultMsg", {}).get("sessionMap", {})
    print(f"📥 {actionId}응답코드:", response.status_code)
    print(f"📄 {actionId}응답 본문:", response.text)
    return session_map
    

def post_permission_with_token(session,ssoToken,userClCd,txaaAdmNo,screenId,domain):
    url = f"https://{domain}.hometax.go.kr/permission.do?screenId={screenId}&domain=hometax.go.kr"
    Referer_url = "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml"
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json; charset=UTF-8",
        "Origin": "https://hometax.go.kr",
        "Referer": Referer_url,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "userClCd": userClCd,  
        "txaaAdmNo": txaaAdmNo,
        "ssoToken": ssoToken,
        "popupYn": False
    }
    print(payload)
    try:
        res = session.post(url, headers=headers, json=payload)
        print("📥 token 응답코드:", res.status_code)
        print("📄 token 응답 본문:", res.text)
        return res.status_code
    except Exception as e:
        print("❌ 요청 실패:", e)
        return None

# 종소세 신고도움 서비스 저장
def action_ATERNABA134R01(session, txaaId, work_YY, SEQ_NO, biz_name, ceo_name, JUMIN):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA134R01&screenId=UTERNAAT31&popupYn=false&realScreenId=UTERNAAT31"

    # Headers (mimicking real browser behavior)
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803050000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\""
    }

    payload = {
        "attrYr": work_YY,
        "bkpPrxRtnPrxClCd": "01",
        "ntplOrgClCd": "1",
        "screenId": "UTERNAAT31",
        "txaaId": txaaId,
        "txprDscmNoEncCntn": JUMIN
    }
    try:
        res = session.post(url, headers=headers, json=payload)
        print("📥 종합소득세 신고도움 서비스 응답코드:", res.status_code)
        # print("📄 종합소득세 신고도움 서비스 응답본문:", res.text)
        result =  res.json()
        tin = result.get("tin");print(f"TIN:{tin}")
        homeRentIncome = result["hsngRmlRtnGdncBscMttrInqrDVO"] #2천이하 주택임대사업소득
        ekopDVO = result["ekopIcmAmtTrtDVO"]
        save_ekopDVO(ekopDVO,SEQ_NO,work_YY,biz_name,ceo_name,homeRentIncome)
        if "bmanIcmKndInqrList" in result and isinstance(result["bmanIcmKndInqrList"], list): 
            bmanList = result["bmanIcmKndInqrList"]#사업소득
            for item in bmanList:
                save_bmanList(item,SEQ_NO,work_YY,biz_name,ceo_name)     
        if "bfhdFthfRtnGdncDVOList" in result and isinstance(result["bfhdFthfRtnGdncDVOList"], list): 
            warningList = result["bfhdFthfRtnGdncDVOList"]
            for item in warningList:
                save_warningList(item,SEQ_NO,work_YY,biz_name,ceo_name)            
        return tin
    except Exception as e:
        print("❌ 요청 실패:", e)
        return None

#지급명세서 리스트 저장
def action_ATERNABA155R01(session,SEQ_NO,work_YY,biz_name,ceo_name, tin):
    url = "https://teht.hometax.go.kr/wqAction.do"
    params = {
        "actionId": "ATERNABA155R01",
        "screenId": "UTERNAAT71",
        "popupYn": "true",
        "realScreenId": "UTERNAAT71"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803050000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "attrYr": work_YY,
        "ieTin": tin,
        "strtDt": work_YY
    }

    try:
        res = session.post(url, headers=headers, params=params, json=payload)
        if res.status_code == 200:
            data = res.json()
            zkmsList = data["dsdEtcSbmsBrkdNtplDVOList"]#지급명세서
            for item in zkmsList:
                save_income_zkms(item,SEQ_NO,work_YY,biz_name,ceo_name)   
        else:
            print("❌ 오류 응답:", res.text[:300])
            return None

    except Exception as e:
        print("❌ 요청 실패:", e)
        return None

#간이지급명세서리스트 조회전 초기화  
def init_action_ATICMAAA001R99(session):
    url = "https://tewe.hometax.go.kr/wqAction.do"
    params = {
        "actionId": "ATICMAAA001R99",
        "screenId": "UWEICAAD32",
        "popupYn": "true",
        "realScreenId": ""
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
    }

    payload = {
        "cmnCdAdmDVOList": [
            {
                "cmnClsfCd": "19560",
                "hrnkCmnClsfCd": "",
                "hrnkCdVval": "",
                "inqrBaseDt": "",
                "inqrBaseDtUseYn": "N",
                "statusValue": "C"
            },
            {
                "cmnClsfCd": "10455",
                "hrnkCmnClsfCd": "",
                "hrnkCdVval": "",
                "inqrBaseDt": "",
                "inqrBaseDtUseYn": "Y",
                "statusValue": "C"
            }
        ]
    }

    try:
        response = session.post(url, headers=headers, params=params, json=payload)
        print("🧩 초기화 응답코드:", response.status_code)
        print("📄 응답 일부:", response.text[:500])

        if response.status_code == 200:
            return response.json()
        else:
            print("❌ 초기화 실패:", response.text[:300])
            return None

    except Exception as e:
        print("❌ 예외 발생:", e)
        return None

#간이지급명세서리스트 저장    
def action_AWEICAAA029R08(session,tin,cdVval,flagYear,SEQ_NO,biz_name,ceo_name):
    # 코드 (cdVval)	설명 (cdVvalDscCntn)
    # F0026	일용근로소득 지급명세서
    # A0161	간이지급명세서(근로소득)
    # A0162	간이지급명세서(거주자의 사업소득)
    # A0165	간이지급명세서(거주자의 기타소득)
    # F0025	사업장 제공자 등의 과세자료 제출명세서
    # A0163	간이지급명세서(연말정산 사업소득)
    # A0164	간이지급명세서(비거주자의 사업소득)
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=AWEICAAA019R09&screenId=UWEICAAD32&popupYn=false&realScreenId=UWEICAAD32"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "searchVO": {
            "mateKndCd": "F0025",             # 사업장 제공자 등의 과세자료 제출명세서
            "baseYr": flagYear,
            "trgtYrCl": "attrYr",
            "strtBaseYr": flagYear,
            "endBaseYr": flagYear,
            "servClCd": "all",
            "incClCd": "",
            "bsicTfbCd": "",
            "lvyRperNo": "",
            "lvyRperNm": "",
            "lvyRperTin": "",
            "ieNo": "",
            "ieNm": "",
            "ieTin": tin,
            "afaInfrOfrAgrYn": ""
        },
        "pageInfoVO": {
            "pageNum": "1",
            "pageSize": "10",
            "totalCount": "0"
        }
    }

    try:
        res = session.post(url, headers=headers,  json=payload)
        print("📥 응답코드:", res.status_code)

        if res.status_code == 200:
            json_data = res.json()
            print("📄 일부 결과:", str(json_data)[:500])
            return json_data
        else:
            print("❌ 오류 응답:", res.text[:300])
            return None

    except Exception as e:
        print("❌ 요청 실패:", e)
        return None

#종소세 사대보험 조회 - 주민번호 입력단계
def get_Tin_ATERNABA094R06(session,txprDscmNo):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA094R06&screenId=UTERNAAD71&popupYn=false&realScreenId=UTERNAAD71"
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803060000",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "tin": "",
        "txprDscmNo": txprDscmNo,
        "ttiabam001DVO": {
            "tin": "",
            "txprDclsCd": "",
            "txprDscmNoEncCntn": "",
            "txprNm": ""
        }
    }
    response = session.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        try:
            result = response.json()
            ttiabam001DVO = result["ttiabam001DVO"]
            tin = ttiabam001DVO.get("tin")
            return tin  # JSON tin 결과 반환
        except Exception as e:
            print("JSON 파싱 실패:", e)
            return response.text  # 혹시 JSON이 아닐 경우 원문 출력
    else:
        print("요청 실패:", response.status_code)
        return None
#종소세 사대보험 조회 - 보험료 조회단계 / 사업자있는 경우 포함
def action_ATERNABA140R02(session,tin,SEQ_NO,work_YY):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA140R02&screenId=UTERNAAD71&popupYn=false&realScreenId=UTERNAAD71"

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803060000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "bkpPrxRtnPrxClCd": "01",
        "bmanTin": "",
        "bsnoYn": "",
        "pplHifeRgnSbsrYn": "",
        "tin": tin,
        "txaaId": "",
        "txyr": work_YY
    }

    response = session.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        try:
            result = response.json()
            session_map = result.get("resultMsg", {}).get("sessionMap", {})
            txaaId =    session_map.get("txaaId")
            if "bsnoList" in result and isinstance(result["bsnoList"], list):
                bsnoList = result["bsnoList"]
                for item in bsnoList:
                    bmanTin = item.get("bmanTin", "")
                    bsno = item.get("bsno","")
                    get_ATTABZAA001R01_info(session,bsno)
                    rst = get_ATERNABA140R01_info(session,bmanTin,tin,txaaId,work_YY)
                    get_permission(session,"UTERNAAT73","teht","https://hometax.go.kr/")  
                    #고용보험료
                    if "empInfee" in rst and isinstance(rst["empInfee"], list):
                        empInfee = rst["empInfee"]         
                        for item in empInfee:
                            infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                            sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)   
                            bmanTin = item.get("bmanTin","");print(bmanTin)  
                            infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                            action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)
                    #연금보험료
                    if "pplPnsnInfee" in rst and isinstance(rst["pplPnsnInfee"], list):
                        pplPnsnInfee = rst["pplPnsnInfee"]         
                        for item in pplPnsnInfee:
                            infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                            sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)   
                            bmanTin = item.get("bmanTin","");print(bmanTin)  
                            infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                            action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)
                    #산재보험료
                    if "indsDsstInfee" in rst and isinstance(rst["indsDsstInfee"], list):
                        indsDsstInfee = rst["indsDsstInfee"]         
                        for item in indsDsstInfee:
                            infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                            sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)   
                            bmanTin = item.get("bmanTin","");print(bmanTin)  
                            infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                            action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)
                    #건강보험료
                    if "pplHifeBman" in rst and isinstance(rst["pplHifeBman"], list):
                        pplHifeBman = rst["pplHifeBman"]         
                        for item in pplHifeBman:
                            infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                            sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)   
                            bmanTin = item.get("bmanTin","");print(bmanTin)  
                            infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                            action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)                            
            else:
                print("사업자로 조회된 데이터가 없음")
                get_permission(session,"UTERNAAT73","teht","https://hometax.go.kr/")  
                #지역가입자건강보험료
                if "pplHifeRgnSbsr" in result and isinstance(result["pplHifeRgnSbsr"], list):
                    pplHifeRgnSbsr = result["pplHifeRgnSbsr"]         
                    for item in pplHifeRgnSbsr:
                        infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                        sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)   
                        bmanTin = item.get("bmanTin","");print(bmanTin)  
                        infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                        action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)
                #고용보험료(노무제공자)
                if "empInfee" in result and isinstance(result["empInfee"], list):
                    empInfee = result["empInfee"]         
                    for item in empInfee:
                        infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                        sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)
                        bmanTin = item.get("bmanTin","");print(bmanTin)  
                        infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                        action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)                        
                #산재보험료(노무제공자)
                if "indsDsstInfee" in result and isinstance(result["indsDsstInfee"], list):
                    indsDsstInfee = result["indsDsstInfee"]         
                    for item in indsDsstInfee:
                        infeeKndClNm = item.get("infeeKndClNm", "");print(infeeKndClNm)
                        sumInscAmt = item.get("sumInscAmt","");print(sumInscAmt)    
                        bmanTin = item.get("bmanTin","");print(bmanTin)  
                        infeeKndClCd = item.get("infeeKndClCd","");print(infeeKndClCd)
                        action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY)                                            
        except ValueError:
            return {"error": "응답을 JSON으로 파싱할 수 없습니다.", "text": response.text}
    else:
        return {"error": f"요청 실패: {response.status_code}", "text": response.text}
    
#종소세 사대보험 조회 - 보험료 조회단계 / 사업자 정보조회 사전단계
def get_ATTABZAA001R01_info(session,txprDscmNo):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATTABZAA001R01&screenId=UTERNAAD71&popupYn=false&realScreenId="

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803060000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "tin": "",
        "txprClsfCd": "02",
        "txprDscmNo": txprDscmNo,
        "txprDscmNoClCd": "",
        "txprDscmDt": "",
        "searchOrder": "02/01",
        "outDes": "edtBmanNoNtplInfo",
        "txprNm": "",
        "crpTin": "",
        "mntgTxprIcldYn": "",
        "resnoAltHstrInqrYn": "",
        "resnoAltHstrInqrBaseDtm": "",
        "sameBmanInqrYn": "N",
        "rpnBmanRetrYn": "N"
    }

    response = session.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            return {"error": "응답을 JSON으로 변환할 수 없음", "raw": response.text}
    else:
        return {"error": f"요청 실패 - 상태코드: {response.status_code}", "raw": response.text}
#종소세 보험료 합계내역 - 사업자인 경우
def get_ATERNABA140R01_info(session,bmanTin,tin,txaaId,work_YY):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA140R01&screenId=UTERNAAD71&popupYn=false&realScreenId=UTERNAAD71"

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4803000000&tm3lIdx=4803060000",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "bkpPrxRtnPrxClCd": "01",
        "bmanTin": bmanTin,
        "bsnoYn": "Y",
        "pplHifeRgnSbsrYn": "N",
        "tin": tin,
        "txaaId": txaaId,
        "txyr": work_YY
    }

    response = session.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            print("응답 결과:", result)
            if "resultData" in result:
                print("resultData:", result["resultData"])
            return result

        except ValueError:
            print("JSON 파싱 오류")
            return {"error": "JSON 파싱 오류", "raw": response.text}
    else:
        print("요청 실패:", response.status_code)
        return {"error": f"요청 실패 - {response.status_code}", "raw": response.text}
#종소세 사업자아닌 경우 지역건강보험료 월별결과
def action_ATERNABA140R03(session,bmanTin,tin,infeeKndClCd,SEQ_NO,work_YY):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA140R03&screenId=UTERNAAT73&popupYn=true&realScreenId=UTERNAAT73"

    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko,en;q=0.9,en-US;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
        "sec-ch-ua": '"Microsoft Edge";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    payload = {
        "bkpPrxRtnPrxClCd": "01",                # 장부유형
        "bmanTin": bmanTin,        # 인식된 사업자 TIN (가상 예시)
        "infeeKndClCd": infeeKndClCd,                     # 수수료유형 (예: 위임/수임구분)
        "tin": tin,             # 조회 대상자 주민/사업자번호
        "txyr": work_YY                           # 귀속연도
    }

    response = session.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            result = response.json()
            mnhlPmtAmtList = result["mnhlPmtAmtList"]#월별 보험료
            for item in mnhlPmtAmtList:
                save_income_insurance(item,SEQ_NO,work_YY,infeeKndClCd)   
            return result
        except ValueError:
            return {"error": "응답을 JSON으로 파싱할 수 없습니다.", "raw": response.text}
    else:
        return {"error": f"요청 실패 - 상태코드: {response.status_code}", "raw": response.text}

# 부가가치세통합조회
def action_ATERNABA197R01(session, work_YY, work_QT, biz_name, biz_no,kawasekisu,singoGB):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATERNABA197R01&screenId=UTERNAA140&popupYn=false&realScreenId=UTERNAA140"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=48&tm2lIdx=4801000000&tm3lIdx=4801060000",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    rtnClCd = "03" if work_QT in (1, 3) else "01"
    txnrmYm = work_YY
    if work_QT in (1, 2):
        txnrmYm += "01"
    elif work_QT in (3, 4):
        txnrmYm += "07"
    payload = {
        "ht": rtnClCd,
        "jobGb": "S",
        "rtnClCd": rtnClCd,
        "txnrmYm": txnrmYm,
        "txprDscmNo": biz_no
    }
    try:
        res = session.post(url, headers=headers, json=payload)
        print("📥 부가가치세 통합조회 응답코드:", res.status_code)
        result =  res.json()
        rst = save_vatTong(result,biz_name,kawasekisu,singoGB)
        return rst
    except Exception as e:
        print(f"❌ {biz_name} 요청 실패:", e)
        return None

#고지/체납세액 조회
def action_ATENFABA001R01(session, Referer_Url, txaaID,tableName, biz_name, biz_no, seq_no, flagYear, workmm):
    url = "https://teht.hometax.go.kr/wqAction.do?actionId=ATENFABA001R01&screenId=UTENFAAA07&popupYn=false&realScreenId="
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://hometax.go.kr",
        "Referer": Referer_Url,
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }
    payload = {
        # "bsafClCd": "003",
        # "cehtxYn": "",
        # "impsTrgtTin": "",
        # "lintxYn": "",
        # "lvyDcsId": "",
        # "lvyDcsTxprBrkdSn": "",
        # "nromTxamtClCd": "01",
        # "ntltxYn": "",
        # "ntrcYn": "",
        # "restxImrpId": "",
        # "sumCl": "0",
        # "tin": "",
        "txaaID":txaaID,
        "txprNo": biz_no,
        "pageInfoVO":{"pageNum":"1","totalCount":"0","pageSize":"10"}
    }
    print(payload)
    try:
        res = session.post(url, headers=headers, json=payload)
        print("📥 고지/체납세액 조회 응답코드:", res.status_code)
        result =  res.json()
        print(result)
        rst = save_GojiChenap(result,Referer_Url,tableName,biz_name, seq_no, flagYear, workmm)
        return rst
    except Exception as e:
        print("❌ 요청 실패:", e)
        return None
    
#디비저장
def save_GojiChenap(data,Referer_Url,tableName,biz_name, seq_no, flagYear, workmm):

    # for i,tr in enumerate(tbody.find_elements(By.TAG_NAME,'tr')):
    #     cols = tr.find_elements(By.TAG_NAME,'td')
    #     if len(cols)>1:
    #         if i==0:
    #         str_del = "delete from "+tableName+" where seq_no="+ result[2]  + " and work_yy='" + str(flagYear)  + "'  and work_mm='" + str(workmm)  + "'" 
    #         cursor.execute(str_del) 
    #         titleTax		= cols[1].get_attribute("innerText")#과세기간세목명
    #         elec_no			= cols[5].text
    #         due_date		= cols[8].text
    #         amt_Tax			= cols[9].text.replace(",","")
    #         if amt_Tax.strip()=='':amt_Tax='0'
    #         taxoffice		= cols[12].text
    #         if flag=='9':
    #         titleTax		= cols[0].text
    #         elec_no			= cols[4].text
    #         due_date		= cols[7].text
    #         amt_Tax			= cols[9].text.replace(",","")
    #         taxoffice		= cols[10].text               
    #         if titleTax == "종합소득세" and (due_date[:7]==str(flagYear)+"-11" or due_date[:7]==str(flagYear)+"-12" ) :
    #         if amt_Tax!='0' and amt_Tax.strip()!='':
    #             str_mg = "Merge Tbl_income2 as A Using (select '"+result[2]+"' as seq_no, '"+str(flagYear)+"' as work_yy ) as B "
    #             str_mg += "On A.seq_no = B.seq_no and A.work_yy = B.work_yy  "
    #             str_mg += "WHEN Matched Then   "
    #             str_mg += "	Update set YN_4=" + amt_Tax
    #             str_mg += "	When Not Matched Then  "
    #             str_mg += "	INSERT (seq_no,work_YY,YN_1,YN_2,YN_3,YN_4,YN_5,YN_6,YN_7,YN_8,YN_9) "
    #             str_mg += "	values('"+result[2]+"','"+str(flagYear)+"',0,0,0,0,0,0,0,0,'');"
    #             cursor = connection.cursor();print(str_mg)
    #             cursor.execute(str_mg)				
    #         else:
    #         if amt_Tax!='0' and amt_Tax.strip()!='':
    #             str_ins = "insert into "+tableName+" values('"+result[2]+"','"+result[5]+"','"+str(flagYear)+"','"+str(workmm)+"','"+str(flagYear)+"-"+ ("0"+str(workmm))[-2:] +"-"+ today[-2:]+"','','"+titleTax+"',"+amt_Tax+",'"+elec_no+"','"+taxoffice+"','"+due_date+"')"
    #             cursor = connection.cursor();print(str_ins)
    #             cursor.execute(str_ins)
    #     strsql = "insert into 스크래핑관리 values('"+today+"','"+result[2]+"','"+result[5]+"','"+txtBigo+"')"       
    #     cursor.execute(strsql) 
    return 1

def save_vatTong(data,sangho,kawasekisu,singoGB):
    txprDscmNo = data.get("txprDscmNo")[:10]
    biz_no=f"{txprDscmNo[:3]}-{txprDscmNo[3:5]}-{txprDscmNo[5:]}"
    kwasekikan    = data.get("txnrm")
    singoyouhyng  = data.get("bmanClNm")
    bubinyejung  = data.get("smscCrpBmanYn")
    kwanhanseo  = data.get("txhfNm")
    juupjongcode  = data.get("tfbCd")
    kanibukayul  = data.get("smpVatRte")
    saleTI  = safe_number(data.get("etxivSlsAmt"))
    saleTIvat  = safe_number(data.get("etxivSlsTxamt"))
    costTI  = safe_number(data.get("etxivPrhAmt"))
    costTIvat  = safe_number(data.get("etxivPrhTxamt"))
    saleNTI  = safe_number(data.get("etivSlsTxamt"))
    costNTI  = safe_number(data.get("etivPrhTxamt"))
    saleSinca  = safe_number(data.get("totaStlAmt"))
    costSinca  = safe_number(data.get("busnCrdcPrhAmt"))
    costSincavat  = safe_number(data.get("busnCrdcPrhTxamt"))
    saleCash  = safe_number(data.get("cshptSlsAmt"))       
    saleCashvat  = safe_number(data.get("cshptSlsTxamt"))
    costCash  = safe_number(data.get("cshptPrhAmt"))
    costCashvat  = safe_number(data.get("cshptPrhTxamt"))   
    saleDaehang = safe_number(data.get("totaSleVcexSlsAmt"))
    costBockji  = safe_number(data.get("cargDrerWlfCardPrhAmt"))
    costBockjivat  = safe_number(data.get("cargDrerWlfCardPrhTxamt"))         
    saleExport = '0'  
    pretax  = safe_number(data.get("schuNftam")) 
    pretaxNot  = safe_number(data.get("schuRtnNrfnTxamt")) 
    pretaxKani  = safe_number(data.get("schuImpsTxamt")) 
    pretaxKaniSingo  = safe_number(data.get("schuRtnTxamt")) 
    purchaseSpecial  = safe_number(data.get("buyePmtSpcsPpmTxamt")) 
    salecashSheet  = data.get('cshSlsSpcfNsbAdttxYn')
    realestateSheet = data.get('raltRmlSplCftSpecAdttxYn')

    strsql_f = "SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = 'C17'"#c17은 고정임 수정말 것
    with connection.cursor() as cursor:
        cursor.execute(strsql_f, (biz_no,kawasekisu))
        result_f = cursor.fetchall()
        connection.commit() 
        str_del = "delete from 부가가치세통합조회 where 과세기수='"+ kawasekisu  + "' and 과세기간='" + kwasekikan  + "' and 사업자등록번호='" + biz_no  + "'" 
        # 부가가치세통합조회는 신고여부따라 삭제하지 않고 국세청에서 나오는 데이터대로 쌓는다
        # if  result_f:   str_del = "delete from 부가가치세통합조회 where 과세기수='"+ kawasekisu  + "' and 과세기간='" + kwasekikan  + "' and 사업자등록번호='" + result[3]  + "'" 
        # else:           str_del = "delete from 부가가치세통합조회 where 과세기수='"+ kawasekisu  + "' and 사업자등록번호='" + result[3]  + "'" 
        cursor = connection.cursor()
        # print(str_del);
        cursor.execute(str_del)
        
        str_ins = (
            f"INSERT INTO 부가가치세통합조회 VALUES ('{kawasekisu}', '{kwasekikan}', '{singoGB}', '{biz_no}', "
            f"'{sangho}', '{singoyouhyng}', '{bubinyejung}', '{kwanhanseo}', '{juupjongcode}', '{kanibukayul}', "
            f"{saleTI}, {saleTIvat}, {saleNTI}, {saleSinca}, 0, "
            f"{saleCash}, {saleCashvat}, {saleExport}, 0, "
            f"{costTI}, {costTIvat}, {costNTI}, {costSinca}, {costSincavat}, "
            f"{costCash}, {costCashvat}, {costBockji}, {costBockjivat}, "
            f"{pretax}, {pretaxNot}, {pretaxKani}, {pretaxKaniSingo}, {purchaseSpecial}, "
            f"'{salecashSheet}', '{realestateSheet}', '{saleDaehang}') "
        )
        # print(str_ins)
        cursor.execute(str_ins);
        print(f"부가가치세통합조회 저장완료 : {sangho} - {kwasekikan}")
    return 1

def save_income_insurance(item,SEQ_NO,work_YY,infeeKndClCd): 
    infee_map = {
        "1": "지역가입자건강보험료",
        "2": "사업자직장건강보험료",
        "7": "사업장사용자부담건강보험료",
        "5": "연금보험료",
        "3": "고용보험료",
        "8": "고용보험료노무제공자",
        "4": "산재보험료",
        "9": "산재보험료노무제공자"
    }

    # 모든 항목 초기화
    record = {
        "seq_no": SEQ_NO,
        "work_YY": work_YY,
        "work_MM": item.get("month", "")
    }

    # 보험 항목들에 대해 값 
    selectLabel = ""
    for code, label in infee_map.items():
        if infeeKndClCd == code:
            selectLabel = label
            record[label] = nullToBlank(item.get("mnhlPmtAmt", ""))
        else:
            record[label] = 0    

    cols = ', '.join(record.keys())
    #문자열 내에서 {} 값이 None일 경우 대비 필요
    vals = ', '.join([f"'{v}'" if isinstance(v, str) else 'NULL' if v is None else str(v) for v in record.values()])
    work_MM = record["work_MM"]

    # UPDATE SET 구문 생성
    update_set = ', '.join([
        f"{col} = ISNULL({col}, 0) + {record[col]}" if col in infee_map.values()
        else f"{col} = '{record[col]}'" if isinstance(record[col], str)
        else f"{col} = NULL" if record[col] is None
        else f"{col} = {record[col]}"
        for col in record.keys()
        if col not in ('seq_no', 'work_YY', 'work_MM')
    ])

    sql = f"""
    MERGE INTO Income_insurance AS T
    USING (SELECT '{SEQ_NO}' AS seq_no, '{work_YY}' AS work_YY,  '{ work_MM}' AS work_MM) AS S
    ON T.seq_no = S.seq_no AND T.work_YY = S.work_YY AND T.work_MM = S.work_MM

    WHEN MATCHED THEN 
        UPDATE SET {update_set}    

    WHEN NOT MATCHED THEN
        INSERT ({cols})
        VALUES ({vals});
    """
    # print(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.commit()      
    print(f"✅ {work_YY}년 {selectLabel} {work_MM}월 저장")
    return 1

def save_income_zkms(zkmsList,SEQ_NO,work_YY,biz_name,ceo_name):
    record = {
        "seq_no":SEQ_NO,
        "work_YY": work_YY,
        "귀속년도": zkmsList.get("spcfAttrYr", ""),
        "징수의무자상호": nullToBlank(zkmsList.get("sbmtNm", "")),        
        "징수의무자사업자번호": nullToBlank(zkmsList.get("sbmtNo", "")),
        "지급명세서종류": zkmsList.get("mateKndNm", ""),
        "제출일자": zkmsList.get("cvaAplnDtm", "")
    }

    cols = ', '.join(record.keys())
    #문자열 내에서 {} 값이 None일 경우 대비 필요
    vals = ', '.join([f"'{v}'" if isinstance(v, str) else 'NULL' if v is None else str(v) for v in record.values()])
    seq_no = record["seq_no"]
    work_yy = record["work_YY"]

    sql = f"""
    MERGE INTO Income_ZKMS AS T
    USING (SELECT '{seq_no}' AS seq_no, '{work_yy}' AS work_YY,  '{ zkmsList.get("sbmtNo", "")}' AS sbmtNo, '{ zkmsList.get("mateKndNm", "")}' AS mateKndNm) AS S
    ON T.seq_no = S.seq_no AND T.work_YY = S.work_YY AND T.징수의무자사업자번호 = S.sbmtNo AND T.지급명세서종류 = S.mateKndNm

    WHEN NOT MATCHED THEN
        INSERT ({cols})
        VALUES ({vals});
    """
    # print(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.commit()      
    print(f"✅ {biz_name}({ceo_name}) {work_YY}년 종합소득세 지급명세서리스트 저장")
    return 1

def save_ekopDVO(ekopDVO,SEQ_NO,work_YY,biz_name,ceo_name,homeRentIncome):
    record = {
        "seq_no":SEQ_NO,
        "work_YY": ekopDVO.get("txnrmYm")[:4],
        "이름": ekopDVO.get("txprNm"),
        "생년월일": ekopDVO.get("jumin"),
        "안내유형": ekopDVO.get("gdncTypeCd"),
        "기장의무": ekopDVO.get("bkpDutyClCdNm"),
        "추계시적용경비율": ekopDVO.get("xpsrt"),
        "납부기한직권연장여부": ekopDVO.get("pmtDdtXtnKrYn"),
        "ARS개별인증번호": ekopDVO.get("arsRtnIndvCertNo"),
        "주업종코드": ekopDVO.get("rtnAtonTfbCd"),
        "업종": ekopDVO.get("rtnAtonTfbCdNm"),
        "세무서": ekopDVO.get("txhfNm"),
        "관계부서": ekopDVO.get("deptOgzNm"),
        "조사관이름": ekopDVO.get("fnm"),
        "조사관전화번호": ekopDVO.get("telNo"),
        "이자소득": safe_number(ekopDVO.get("intrIncAmtYn")),
        "배당소득": safe_number(ekopDVO.get("dvdnIncAmtYn")),
        "근로소득단수": safe_number(ekopDVO.get("erinAmtYn")),
        "근로소득복수": safe_number(ekopDVO.get("dblErinAmtYn")),
        "연금소득": safe_number(ekopDVO.get("pnsnIncAmtYn")),
        "기타소득": safe_number(ekopDVO.get("etcIncAmtYn")),
        "종교인기타소득": ekopDVO.get("rgpIncAmtYn"),
        "주택임대수입금액": safe_number(homeRentIncome.get("icmAmt")),
        "중간예납세액": safe_number(ekopDVO.get("etpTxamt")),
        "원천징수세액": safe_number(ekopDVO.get("pwtxTxamt")),
        "국민연금보험료": safe_number(ekopDVO.get("npInfeeDdcAmt")),
        "개인연금저축": safe_number(ekopDVO.get("ntplPnsnDdcAmt")),
        "소기업소상공인공제부금": safe_number(ekopDVO.get("smceDdcIntlIncDdcAmt")),
        "퇴직연금세액공제": safe_number(ekopDVO.get("rtpnIncDdcAmt")),
        "연금계좌세액공제": safe_number(ekopDVO.get("pnsnSvngDdcAmt")),
        "무기장가산세": ekopDVO.get("gdncKndCdShYn"),
        "계산서보고불성실": safe_number(ekopDVO.get("invcStblNsbDlySbmsAmt")),
        "현금영수증미가맹": ekopDVO.get("cshptNjnnTypeCdNm"),
        "현금영수증미발급": safe_number(ekopDVO.get("cshptNisnAmtBaseAmt")),
        "현금영수증발급거부10만원미만": safe_number(ekopDVO.get("cshptOhtwBlwIsnRjcScnt")),
        "현금영수증발급거부10만원이상": safe_number(ekopDVO.get("cshptOhtwOverIsnRjcAmt")),
        "신용카드발급거부10만원이상": safe_number(ekopDVO.get("crdcOhtwOverIsnRjcAmt")),
        "신용카드발급거부10만원미만": safe_number(ekopDVO.get("crdcOhtwBlwIsnRjcScnt")),
        "사업장현황신고불성실": safe_number(ekopDVO.get("pfbPsteEnosRtnAmt")),
        "사업용계좌미신고": ekopDVO.get("busnAccNestlYn")
    }

    cols = ', '.join(record.keys())
    #문자열 내에서 {} 값이 None일 경우 대비 필요
    vals = ', '.join([f"'{v}'" if isinstance(v, str) else 'NULL' if v is None else str(v) for v in record.values()])
    seq_no = record["seq_no"]
    work_yy = record["work_YY"]

    sql = f"""
    MERGE INTO Income_ekop AS target
    USING (SELECT '{seq_no}' AS seq_no, '{work_yy}' AS work_YY) AS source
    ON target.seq_no = source.seq_no AND target.work_YY = source.work_YY

    WHEN NOT MATCHED THEN
        INSERT ({cols})
        VALUES ({vals});
    """
    # print(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.commit()      
    print(f"✅ {biz_name}({ceo_name}) {work_YY}년 종합소득세 신고도움 서비스 ekopDVO 저장")
    return 1

def save_bmanList(bmanTrn,SEQ_NO,work_YY,biz_name,ceo_name):
    record = {
        "seq_no":SEQ_NO,
        "work_YY": work_YY,
        "사업자번호": nullToBlank(bmanTrn.get("txprDscmNoEncCntn", "")),
        "상호": nullToBlank(bmanTrn.get("bmanNm", "")),
        "소득구분": bmanTrn.get("incClCd", ""),
        "수입종류구분코드": bmanTrn.get("icmAmtKndClCdNm", ""),
        "업종코드": bmanTrn.get("tfbCd", ""),
        "사업형태": bmanTrn.get("jntBmanNm", ""),
        "기장의무": bmanTrn.get("bkpDutyClCdNm", ""),
        "경비율": bmanTrn.get("xpsrt", ""),
        "수입금액": safe_number(bmanTrn.get("icmAmt")),
        "기준경비율일반": bmanTrn.get("baseXpsrtGnrlRte"),
        "기준경비율자가": bmanTrn.get("baseXpsrtMhRte"),
        "단순경비율일반": bmanTrn.get("smplXpsrtGnrlRte"),
        "단순경비율자가": bmanTrn.get("smplXpsrtMhRte"),
        "사업소득개수": safe_number(bmanTrn.get("totaSumAmt")),
        "사업소득합계": safe_number(bmanTrn.get("totaSumIcmAmt")),
        "원천징수의무자상호": nullToBlank(bmanTrn.get("whtxRperNm", "")),
        "원천징수의무자사업자번호": nullToBlank(bmanTrn.get("whtxRperNo", "")),
    }

    cols = ', '.join(record.keys())
    #문자열 내에서 {} 값이 None일 경우 대비 필요
    vals = ', '.join([f"'{v}'" if isinstance(v, str) else 'NULL' if v is None else str(v) for v in record.values()])
    seq_no = record["seq_no"]
    work_yy = record["work_YY"]

    sql = f"""
    MERGE INTO Income_bman AS T
    USING (SELECT '{seq_no}' AS seq_no, '{work_yy}' AS work_YY,  '{ bmanTrn.get("icmAmtKndClCdNm", "")}' AS icmAmtKndClCdNm, '{ bmanTrn.get("tfbCd", "")}' AS tfbCd, '{ bmanTrn.get("incClCd", "")}' AS incClCd) AS S
    ON T.seq_no = S.seq_no AND T.work_YY = S.work_YY AND T.수입종류구분코드 = S.icmAmtKndClCdNm AND T.소득구분 = S.incClCd AND T.업종코드 = S.tfbCd

    WHEN NOT MATCHED THEN
        INSERT ({cols})
        VALUES ({vals});
    """
    # print(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.commit()      
    print(f"✅ {biz_name}({ceo_name}) {work_YY}년 종합소득세 신고도움 서비스 bmanList 저장")
    return 1

def save_warningList(fthfRtn,SEQ_NO,work_YY,biz_name,ceo_name):
    record = {
        "seq_no":SEQ_NO,
        "work_YY": work_YY,
        "경고코드": nullToBlank(fthfRtn.get("fthfRtnGdncClusCd", "")),
        "경고항목": fthfRtn.get("fthfRtnGdncClusCdNm", ""),
        "경고항목설명": fthfRtn.get("fthfRtnGdncClusDscCntn", "")
    }

    cols = ', '.join(record.keys())
    #문자열 내에서 {} 값이 None일 경우 대비 필요
    vals = ', '.join([f"'{v}'" if isinstance(v, str) else 'NULL' if v is None else str(v) for v in record.values()])
    seq_no = record["seq_no"]
    work_yy = record["work_YY"]

    sql = f"""
    MERGE INTO Income_warning AS T
    USING (SELECT '{seq_no}' AS seq_no, '{work_yy}' AS work_YY,  '{ fthfRtn.get("fthfRtnGdncClusCd", "")}' AS fthfRtnGdncClusCd) AS S
    ON T.seq_no = S.seq_no AND T.work_YY = S.work_YY AND T.경고코드 = S.fthfRtnGdncClusCd

    WHEN NOT MATCHED THEN
        INSERT ({cols})
        VALUES ({vals});
    """
    # print(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    cursor.commit()      
    print(f"✅ {biz_name}({ceo_name}) {work_YY}년 종합소득세 신고도움 서비스 사전경고 저장")
    return 1

def safe_number(value):
    """None 또는 문자열/숫자 처리 후 숫자형 문자열 반환"""
    if value in [None, "None","null", ""]:
        return "0"
    return str(value).replace(",", "")

def nullToBlank(value):
    return "" if value == "null" else value    