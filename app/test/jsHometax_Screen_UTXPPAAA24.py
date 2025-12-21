#######################
#  개인사업자 TIN찾기  #
#######################

import time
import json
from app.test import jsHometax

REFERER_URL = "https://hometax.go.kr/websquare/popup.html?w2xPath=/ui/pp/a/a/UTXPPAAA24.xml"
class JsHometax_Screen_UTXPPAAA24:
    def __init__(self):
        self.m_trsDtRngStrt = ""   # 시작 날짜
        self.m_trsDtRngEnd = ""    # 종료 날짜
        self.m_sumTotaTrsAmt = 0  # 총 사용 금액 (봉사료 제외)
        self.m_sumSplCft = 0      # 
        self.m_pageSize = 0       # 페이지당 아이템 개수
        self.m_pageCount = 0      # 페이지 개수
        self.m_totalCount = 0     # 전체 아이템 개수
        self.m_userNm = ""
        self.m_txprDscmNo = ""
        self.m_userId = ""    
    def requestPermission(self):
        rst = 0
        reqperm_errorCd = 0
        reqperm_errorMsg = None
        sbSSOToken = ""
        sbuserClCd = ""
        
        if not jsHometax.getLoginStatus():      return -10

        rst = jsHometax.requestPermission(REFERER_URL, "www", "UTXPPAAA24", None, None, None, reqperm_errorCd, reqperm_errorMsg)
        # print("IN UTXPPAAA24 - jsHometax.requestPermission")
        # print(rst)           
        if rst != 1:      return rst

        rst = jsHometax.getSSOToken(REFERER_URL)
        sbSSOToken = jsHometax.sbSSOToken
        sbuserClCd = jsHometax.sbuserClCd        
        if rst != 1:      return rst

        rst = jsHometax.requestPermission(REFERER_URL, "www", "UTXPPAAA24", "hometax.go.kr", sbSSOToken, sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
        if rst != 1:      return rst

        return 1

    def action_ATXPPAAA003R01_getTin(self,biz_no, biz_tin):
        sbResponseData = ""
        strResData = ""
        refererUrl = "https://hometax.go.kr/wqAction.do?actionId=ATXPPAAA003R01&screenId=UTXPPAAA24&popupYn=false&realScreenId="
        url = "https://hometax.go.kr/wqAction.do?actionId=ATXPPAAA003R01&screenId=UTXPPAAA24&popupYn=false&realScreenId="
        postdata = "<map id='ATXPPAAA003R01'/><nts<nts>nts>33UcUzKSA5HAYSKx9MEujvbGAM87OI0QcO17gWLUj5o22"
        postdata = {
            "originTin": "",
            "scrnId": "index",
            "ntsData": "nts>57wWjj5SbFwZSdBJJXUH31JAqqJisnxy74wp69zhMdYQ46"
        }
        rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, "application/json", sbResponseData);
        strResData = jsHometax.sbResponseData
        # print("IN action_ATXPPAAA003R01_getTin : "+strResData)
        if "과부하제어" in strResData:
            time.sleep(61)
            return biz_tin
        elif "처리중 예외가 발생하였습니다." in jsHometax.sbResponseData :
            return biz_tin
        elif jsHometax.sbResponseData == "":
            return biz_tin
        
        # JSON 문자열을 Python 딕셔너리로 변환
        data = json.loads(strResData)

        # 1. sessionMap 내부의 값 추출
        session_map = data.get("resultMsg", {}).get("sessionMap", {})
        txprDscmNoEncCntn_session = session_map.get("txprDscmNoEncCntn")
        tin_session = session_map.get("tin")

        # 2. bmanBscInfrInqrDVOList 내부의 값 추출
        bman_list = data.get("bmanBscInfrInqrDVOList", [])
        if bman_list:
            txprDscmNoEncCntn_bman = bman_list[0].get("txprDscmNoEncCntn")
            tin_bman = bman_list[0].get("tin")
            if txprDscmNoEncCntn_bman == biz_no.replace("-", ""):
                return tin_bman
        else:
            txprDscmNoEncCntn_bman = None
            tin_bman = None

        return tin_bman
