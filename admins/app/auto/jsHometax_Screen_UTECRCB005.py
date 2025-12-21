import datetime
import xml.etree.ElementTree as ET
from app.test import jsHometax
from django.db import connection
from app.test import utils

class ActionCtx_ATECRCBA001R02:
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

class ActionItem_ATECRCBA001R02:
    def __init__(self):
        self.m_trsDtm = ""                   # 거래일시
        self.m_aprvNo = ""                   # 승인번호
        self.m_trsClNm =""                   # 승인거래
        self.m_spstCnfrClNm = ""             #발행수단 : 휴대번호/사업자
        self.m_mrntTxprDscmNoEncCntn = ""    # 상대방사업자번호
        self.m_mrntTxprNm = ""               # 상대방번호
        self.m_splCft = 0                    # 공급가액
        self.m_vaTxamt = 0                   # 세액
        self.m_tip = 0                       # 봉사료
        self.m_totaTrsAmt = 0                # 합계
        self.m_bmanClNm = ""                 # 가맹점 유형
        self.m_ddcYnNm = ""                  # 공제여부 결정  prhTxamtDdcClNm
        self.m_vatDdcClNm = ""               # 선택불공제/일반

    def readXML(self, node):
        subnode = node.find("trsDtTime")                    # 거래일자
        if subnode is None:     self.m_trsDtm = ""
        else:                   self.m_trsDtm = subnode.text
        subnode = node.find("aprvNo")
        if subnode is None:     self.m_aprvNo = ""
        else:                   self.m_aprvNo = subnode.text
        subnode = node.find("trsClNm")
        if subnode is None:     self.m_trsClNm = ""
        else:                   self.m_trsClNm = subnode.text
        subnode = node.find("spstCnfrClNm")
        if subnode is None:     self.m_spstCnfrClNm = ""
        else:                   self.m_spstCnfrClNm = subnode.text
        subnode = node.find("mrntTxprDscmNoEncCntn")
        if subnode is None:     self.m_mrntTxprDscmNoEncCntn = ""
        else:                   self.m_mrntTxprDscmNoEncCntn = subnode.text
        subnode = node.find("mrntTxprNm")
        if subnode is None:     self.m_mrntTxprNm = ""
        else:                   self.m_mrntTxprNm = subnode.text  
        if self.m_mrntTxprNm is None: self.m_mrntTxprNm = ""          
        subnode = node.find("splCft");self.m_splCft = self._xmlTextToLong(subnode)          # 공급가액
        subnode = node.find("vaTxamt");  self.m_vaTxamt = self._xmlTextToLong(subnode)
        subnode = node.find("tip");  self.m_tip = self._xmlTextToLong(subnode)        
        subnode = node.find("totaTrsAmt");self.m_totaTrsAmt = self._xmlTextToLong(subnode)     # 합계
        subnode = node.find("bmanClNm")
        if subnode is None:     self.m_bmanClNm = ""
        else:                   self.m_bmanClNm = subnode.text
        subnode = node.find("prhTxamtDdcClNm")
        if subnode is None:     self.m_ddcYnNm = ""
        else:                   self.m_ddcYnNm = subnode.text
        subnode = node.find("vatDdcClNm")
        if subnode is None:     self.m_vatDdcClNm = ""
        else:                   self.m_vatDdcClNm = subnode.text

    @staticmethod
    def _xmlTextToLong(node):
        if node is None or node.text is None:
            return 0
        return int(node.text) 
               
REFERER_URL = "https://tecr.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/cr/c/b/UTECRCB005.xml"
class JsHometax_Screen_UTECRCB005:

  def requestPermission(self):
      rst = 0
      reqperm_errorCd = 0
      reqperm_errorMsg = None

      sbSSOToken = ""
      sbuserClCd = ""

      if not jsHometax.getLoginStatus():    return -10

      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB005", None, None, None, reqperm_errorCd, reqperm_errorMsg)
      # print("IN UTECRCB023 - jsHometax.requestPermission")
      # print(rst)      
      if rst != 1:    return rst
      rst = jsHometax.getSSOToken(REFERER_URL)
      sbSSOToken = jsHometax.sbSSOToken
      sbuserClCd = jsHometax.sbuserClCd
      # print(sbSSOToken)     
      # print(sbuserClCd)       
      # print(rst)
      if rst != 1:    return rst
      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB005", "hometax.go.kr", sbSSOToken, sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
      # print(rst)
      if rst != 1:    return rst
      
      return 1

  def action_ATECRCBA001R02(self,actionctx, startdate, enddate):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R02&screenId=UTECRCB005&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R02&screenId=UTECRCB005&popupYn=false&realScreenId="

      sbResponseData = ""
      strResData = ""
      sbSSOToken = ""
      sbuserClCd = ""

      xmldoc = None
      xmlnodelst = None
      xmlnode = None
      xml_tmpnode = None
      xmlrawnode_pageInfoVO = None
      xmlrawnode_sessionMap = None

      if not jsHometax.getLoginStatus():    return -10

      # result_LoginSystemCtx = jsHometax.LoginSystemContext() 필요없음

      # 1. First Data
      postdata = "<map id=\"ATECRCBA001R02\"><tin>" + jsHometax.mLoginSystem_Main.m_tin + "</tin><trsDtRngStrt>" + startdate + "</trsDtRngStrt><trsDtRngEnd>" + enddate + "</trsDtRngEnd><prhTxamtDdcYn>all</prhTxamtDdcYn><sumTotaTrsAmt/><resultCd/></map>"
      # print(postdata)
      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, jsHometax._HTTP_ContextType_XML, sbResponseData)
      strResData = jsHometax.sbResponseData    
      # print(strResData)
      if "과부하제어" in strResData:
          print("과부하제어 대기중")
          ThisMoment = datetime.now()
          duration = datetime.timedelta(seconds=61)   # 61초 후 재생
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
            ThisMoment = datetime.now()
          return -10000
      elif strResData == "":
          return -10000
      
      xmldoc = ET.fromstring(strResData)
      xmlnodelst = xmldoc.findall("map")
      if xmlnodelst is None:    return -10000
      print(xmlnodelst)
      print(strResData)
      if xmldoc.find('sumTotaTrsAmt') is None: return -10000
      actionctx.m_sumTotaTrsAmt = int(xmldoc.find('sumTotaTrsAmt').text)
      actionctx.m_sumSplCft = int(xmldoc.find('sumSplCft').text)
      actionctx.m_trsDtRngStrt = xmldoc.find('trsDtRngStrt').text
      actionctx.m_trsDtRngEnd = xmldoc.find('trsDtRngEnd').text
      xmlrawnode_pageInfoVO = xmlnodelst[1]
      xml_tmpnode = xmlrawnode_pageInfoVO.find('pageSize').text
      if xml_tmpnode is None:          return -10000
      actionctx.m_pageSize = int(xml_tmpnode)

      xml_tmpnode = xmlrawnode_pageInfoVO.find('totalCount').text
      if xml_tmpnode is None:          return -10000
      actionctx.m_totalCount = int(xml_tmpnode)

      actionctx.m_pageCount = ((actionctx.m_totalCount + actionctx.m_pageSize - 1) // actionctx.m_pageSize)
      print(actionctx.m_pageCount)
      return 1  

  def action_ATECRCBA001R02_getItems(self,actionctx, page,cursor,workyear,strChkDate,txtRangeStart,txtRangeEnd,HometaxID,HometaxPW,flagSeqNo,biz_no,biz_name):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R02&screenId=UTECRCB013&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R02&screenId=UTECRCB013&popupYn=false&realScreenId="
      postdata = f"<map id=\"ATECRCBA001R02\"><tin>{jsHometax.mLoginSystem_Main.m_tin}</tin><trsDtRngStrt>{actionctx.m_trsDtRngStrt}</trsDtRngStrt><trsDtRngEnd>{actionctx.m_trsDtRngEnd}</trsDtRngEnd><prhTxamtDdcYn>all</prhTxamtDdcYn><sumTotaTrsAmt>{actionctx.m_sumTotaTrsAmt}</sumTotaTrsAmt><resultCd>N</resultCd><dwldTrsBrkdScnt>0</dwldTrsBrkdScnt><totalCount>0</totalCount><sumSplCft>{actionctx.m_sumSplCft}</sumSplCft><map id=\"pageInfoVO\"><pageSize>{actionctx.m_pageSize}</pageSize><pageNum>{page}</pageNum><totalCount>{actionctx.m_totalCount}</totalCount></map></map>"

      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, jsHometax._HTTP_ContextType_XML, '')
      strResData = jsHometax.sbResponseData
      if "과부하제어" in strResData:
          print("과부하제어 대기중")
          ThisMoment = datetime.datetime.now()
          duration = datetime.timedelta(seconds=61)   #61초 후 재시도
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
              ThisMoment = datetime.datetime.now()
          return -9
      elif strResData == "":
          return -10000
      print(strResData)
      xmldoc = ET.fromstring(strResData)
      xmlnodelst = xmldoc.findall("map")
      if xmlnodelst is None:          return -10000
      xmlnode = xmlnodelst[0]
      if xmlnodelst is None:          return -10000
      list_element = xmldoc.find("list[@id='cshTrsBrkdInqrDVOList']")
      if list_element is None:          return -10000
      map_elements = list_element.findall("map")
      if map_elements is None:          return -10000
      for node in map_elements:
          item = ActionItem_ATECRCBA001R02()
          item.readXML(node)
          if item.m_trsClNm=="취소거래" and item.m_splCft>0:
                item.m_splCft = item.m_splCft * -1
                item.m_vaTxamt = item.m_vaTxamt * -1
                item.m_tip = item.m_tip * -1
                item.m_totaTrsAmt = item.m_totaTrsAmt * -1          
          sql =  "INSERT INTO Tbl_HomeTax_CashCost VALUES ('" + item.m_trsDtm +"',isnull((select max(rowSeq)+1 from Tbl_HomeTax_CashCost where seq_no="+flagSeqNo+" and left(tran_dt,4)="+str(workyear)+" and stnd_GB='"+utils.get_quarter(item.m_trsDtm[5:7])+"'),0)"
          sql += ",'"+utils.get_quarter(item.m_trsDtm[5:7])+"','"+biz_no+"','"+flagSeqNo+"','"+biz_name+"','"+item.m_aprvNo+"','"+item.m_trsClNm+"','"+item.m_spstCnfrClNm
          sql += "','"+item.m_mrntTxprDscmNoEncCntn+"','"+item.m_mrntTxprNm+"','"+ str(item.m_splCft)+"','"+str(item.m_vaTxamt)+"','"+str(item.m_tip)+"','"+str(item.m_totaTrsAmt)+"','"+item.m_bmanClNm
          sql += "','"+item.m_ddcYnNm+"','"+item.m_vatDdcClNm+"','61','공제','830','소모품비',getdate(),'N','','','')"
          print(sql)
          cursor.execute(sql)
          connection.commit()
       
      return 1
