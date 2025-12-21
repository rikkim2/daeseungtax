#####################################
#     합계표 저장
#####################################


from datetime import datetime
import time
import json
from app.test import jsHometax
from django.db import connection
from app.test import utils


# referer_url_success = "https://teet.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml"
class ActionCtx_UTEETBDB17:
    def __init__(self):
        self.m_inqrDtStrt = ""    # 조회시작일자  =>합계표는 기간이 없다 
        self.m_inqrDtEnd = ""     # 조회종료일자  =>합계표는 기간이 없다 

        self.m_wTotaAmt = 0  # 총공급대가
        self.m_wSumTxamt = 0  # 총공급가액

        self.m_rtnClCd = ""           #1 = 1기 예정, 2 = 1기 확정, 3 = 1기 예+확, 4 = 2기 예정, 5 = 2기 확정, 6 = 2기 예+확
        self.m_wrtYr = ""           #조회연도

        self.m_prhSlsClCd = ""    #01 = 매출, 02 = 매입        
        self.m_dmnrTin = ""       #공급받는자 ==> 매입일 경우 cnvr_tin을 넣는다
        self.m_splrTin = ""       #공급자    ==> 매출일 경우 cnvr_tin을 넣는다

        self.m_ATEETBDA002R = ""    #url결정
        self.m_UTEETBDB = ""    #url결정

class JsHometax_Screen_UTEETBDB17:
    def requestPermission(self,actionctxTIS):
        rst = 0
        reqperm_errorCd = 0
        reqperm_errorMsg = ""
        UTEETBDB = f"UTEETBDB{actionctxTIS.m_UTEETBDB}"
        REFERER_URL = f"https://teet.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/etx/pp/{UTEETBDB}.xml"
        REFERER_URL = "https://teet.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml"
        if not jsHometax.getLoginStatus():
            return -10

        rst = jsHometax.requestPermission(REFERER_URL, "teet", UTEETBDB, "teet.hometax.go.kr", jsHometax.sbSSOToken, jsHometax.sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
        return rst
    def action_ATTABZAA001R01():
        
        url = "https://teet.hometax.go.kr/wqAction.do?actionId=ATTABZAA001R01&screenId=UTEETBDB19&popupYn=false&realScreenId="

        if not jsHometax.getLoginStatus():
            return -10
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml",
            "Origin": "https://hometax.go.kr",
            "User-Agent": "Mozilla/5.0",
            "Cookie": f"TXPPsessionID={jsHometax.TXPPsessionID}; TEETsessionID={jsHometax.TEETsessionID}; WMONID={jsHometax.WMONID};"
        }
                    
        payload = {
            "tin":"",
            "txprClsfCd":"99",
            "txprDscmNo":"2208533586",
            "txprDscmNoClCd":"",
            "txprDscmDt":"",
            "searchOrder":"",
            "outDes":"txprBscListDVOOutDes",
            "txprNm":"",
            "crpTin":"",
            "mntgTxprIcldYn":"",
            "resnoAltHstrInqrYn":"",
            "resnoAltHstrInqrBaseDtm":"",
            "sameBmanInqrYn":"N",
            "rpnBmanRetrYn":"N"
        }
        response = jsHometax.sbSession.post(url, headers=headers, data=json.dumps(payload))  
        if response.status_code != 200:
            raise Exception(f"❌ 요청 실패: {response.status_code}")    
        result = response.json()
        result_msg = result.get("resultMsg", {})            
        if result_msg.get("result") != "S":
            raise Exception(f"❌ 조회 실패: {result_msg.get('msg')}")
        return 1

    def action_ATEETBDA002R01(gubun, actionctxTIS,  memuser,work_qt):
        today = str(datetime.now())[:10].replace("-","")
        
        url = f"https://teet.hometax.go.kr/wqAction.do?actionId=ATEETBDA002R{actionctxTIS.m_ATEETBDA002R}&screenId=UTEETBD{actionctxTIS.m_UTEETBDB}&popupYn=false&realScreenId="

        if not jsHometax.getLoginStatus():
            return -10
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&menuCd=index4",
            "Origin": "https://hometax.go.kr",
            "User-Agent": "Mozilla/5.0",
            "Cookie": f"TXPPsessionID={jsHometax.TXPPsessionID}; TEETsessionID={jsHometax.TEETsessionID}; WMONID={jsHometax.WMONID};"
        }
                    
        payload = {
            "dtCl": "03",
            "fleDwldYn": "",
            "fleTp": "",
            "icldCstnBmanInfr": "",
            "icldLsatInfr": "",
            "prhSlsClCd": actionctxTIS.m_prhSlsClCd,
            "prxTin": "",
            "resnoSecYn": "",
            "srtClCd": "",
            "srtOpt": "",
            "trsTermDt": "",
            "etxivIsnStblListDVOPrmt": {
                "dmnrTin": actionctxTIS.m_dmnrTin,
                "dtCl": "",
                "pageSize": "10",
                "rtnClCd": actionctxTIS.m_rtnClCd,
                "splrTin": actionctxTIS.m_splrTin,
                "wrtDtEnd": "",
                "wrtDtStrt": "",
                "wrtMnth": "",
                "wrtYr": actionctxTIS.m_wrtYr
            }
            #"ntsData": jsHometax.sbSSOToken
        }

        response = jsHometax.sbSession.post(url, headers=headers, data=json.dumps(payload))
        strResData = response.text
        if "과부하제어" in strResData:
            print("과부하제어 대기중")
            time.sleep(61)
            return -9
        elif strResData == "":
            return -10000

        if response.status_code != 200:
            print(f"구분:{gubun} - {payload}")
            print(f"구분:{gubun} - {url}")
            raise Exception(f"❌ 요청 실패: {response.status_code}")

        if 'application/json' in response.headers.get('Content-Type', ''):
            result = response.json()
            result_msg = result.get("resultMsg", {})
        else:
            print("⚠️ JSON 응답이 아님:", response)
            return -1

        if result_msg.get("result") != "S":
            print(result)
            print(payload)
            raise Exception(f"❌ 조회 실패: {result_msg.get('msg')}")
        
        row = result["etxivIsnStblListDVOPrmt"]
        # print(row)
        def safe_number(value):
            """None 또는 문자열/숫자 처리 후 숫자형 문자열 반환"""
            if value in [None, "None", ""]:
                return "0"
            return str(value).replace(",", "")
        kkdk = kkke = kkkt = totSlsCnt = totEtxivIsnScnt = 0
        kkdk  = safe_number(row.get("totSumAmt"))        # 전체 공급대가
        kkke  = safe_number(row.get("totSumSplCft"))     # 전체 공급가액
        kkkt  = safe_number(row.get("totSumTxamt"))      # 전체 세액
        totSlsCnt = safe_number(row.get("totSlsCnt"))    # 업체수
        totEtxivIsnScnt = safe_number(row.get("totEtxivIsnScnt"))  # 거래건수

        actionctxTIS.m_wTotaAmt = kkdk
        actionctxTIS.m_wSumTxamt = kkke
        sql = f"""
        MERGE 전자세금계산서합계표 AS A
        USING (SELECT '{memuser.seq_no}' AS seq_no, '{actionctxTIS.m_wrtYr}' AS work_yy, '{work_qt}' AS work_qt, '{gubun}' AS 매입매출구분) AS B
        ON A.seq_no = B.seq_no AND A.work_yy = B.work_yy AND A.work_qt = B.work_qt AND A.매입매출구분 = B.매입매출구분
        WHEN MATCHED THEN
            UPDATE SET
                업체수 = {totSlsCnt},
                합계금액 = {kkdk},
                공급가액 = {kkke},
                세액 = {kkkt},
                건수 = {totEtxivIsnScnt},
                crtdt = '{today}'
        WHEN NOT MATCHED THEN
            INSERT (seq_no, work_yy, work_qt, 매입매출구분,업체수,합계금액,공급가액,세액,건수, crtdt)
            VALUES ('{memuser.seq_no}', '{actionctxTIS.m_wrtYr}', '{work_qt}', '{gubun}', {totSlsCnt}, {kkdk}, {kkke}, {kkkt}, {totEtxivIsnScnt}, '{today}');
        """
        # print(sql)
        cursor = connection.cursor()
        cursor.execute(sql)
        cursor.commit()  

        print(f"✅ {memuser.biz_name} {actionctxTIS.m_wrtYr}년 {work_qt}분기 전자세금계산서 합계표 저장 구분:{gubun} (1-매출세계, 2-매입세계, 3-매출계, 4-매입계)")

        return 1
