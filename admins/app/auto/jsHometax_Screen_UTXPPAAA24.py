import time
import requests
import xml.etree.ElementTree as ET
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
        print("IN UTXPPAAA24 - jsHometax.requestPermission")
        print(rst)           
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
        rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, jsHometax._HTTP_ContextType_XML, sbResponseData);
        strResData = jsHometax.sbResponseData
        # print("IN action_ATXPPAAA003R01_getTin : "+strResData)
        if "과부하제어" in strResData:
            time.sleep(61)
            return biz_tin
        elif jsHometax.sbResponseData == "":
            return biz_tin
        
        xmldoc = ET.fromstring(strResData)
        xmlnodelst = xmldoc.findall("map")

        if xmlnodelst is None:            return biz_tin
        xmlnode = xmlnodelst[0]
        if xmlnodelst is None:            return biz_tin

        xml_tmpnodelst = xmldoc.find("list[@id='bmanBscInfrInqrDVOList']")
        # print("IN action_ATXPPAAA003R01_getTin : ")
        # print(xml_tmpnodelst)        
        if xml_tmpnodelst is None:            return biz_tin
        xmlrawnode_busnCrdcTrsBrkdAdmDVOList = xml_tmpnodelst

        tmpBizNo = biz_tin

        for node in xmlrawnode_busnCrdcTrsBrkdAdmDVOList:
            subnode = node.find("txprDscmNoEncCntn")
            if subnode is not None and subnode.text == biz_no.replace("-", ""):
                subnode = node.find("tin")
                if subnode is not None:
                    tmpBizNo = subnode.text
                    jsHometax.mLoginSystem_Main.m_tin = tmpBizNo
                    break

        return tmpBizNo

def _xmlTextToInt(node, nullval=-1):
    if node is None:    return nullval
    else:
        rst = None
        val = None
    try:
        val = int(node.text)
        rst = True
    except ValueError:
        rst = False
    if rst:
        return val
    else:
        return nullval

def _xmlTextToLong(node, nullval=-1):
    if node is None:
        return nullval
    else:
        rst = None
        val = None
    try:
        val = int(node.text)
        rst = True
    except ValueError:
        rst = False
    if rst:
        return val
    else:
        return nullval