import datetime
import xml.etree.ElementTree as ET
from app.test import jsHometax
from django.db import connection
class ActionCtx_ATECRCCA001R07:
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


class ActionItem_ATECRCCA001R07:
    def __init__(self):
        self.m_rowSeq = 0                    # 순서번호
        self.m_aprvDt = ""                   # 승인일자
        self.m_crcmClNm = ""                 # 카드사
        self.m_busnCrdCardNoEncCntn = ""     # 카드번호
        self.m_mrntTxprDscmNoEncCntn = ""    # 가맹점 사업자 번호
        self.m_mrntTxprNm = ""               # 가맹점명
        self.m_splCft = 0                    # 공급가액
        self.m_vaTxamt = 0                   # 세액
        self.m_tip = 0                       # 봉사료
        self.m_totaTrsAmt = 0                # 합계
        self.m_bmanClNm = ""                 # 가맹점 유형
        self.m_ddcYnNm = ""                  # 공제여부 결정
        self.m_vatDdcClNm = ""               # 비고
        self.m_busnCrdcTrsBrkdSn = ""
        self.m_busnCrdcTrsBrkdPrhYr = 0      # year
        self.m_crcmClCd = ""
        self.m_txprDclsCd = ""
        self.m_mrntTin = ""
        self.m_crdcTxprDscmNoEncCntn = ""
        self.m_bmanClCd = ""
        self.m_crdcBmanTxprNm = ""
        self.m_statusValue = ""
        self.m_crdcBmanTin = ""
        self.m_vatDdcClCd = ""
        self.m_prhDt = ""                    # Date
        self.m_prhQrt = 0        
        self.m_bcNm = ""                    #업태
        self.m_tfbNm = ""                   #종목

    def readXML(self, node):
        subnode = node.find("mrntTxprDscmNoEncCntn")   # 가맹점 사업자 번호
        if subnode is not None:    self.m_mrntTxprDscmNoEncCntn = subnode.text

        subnode = node.find("totaTrsAmt")               # 합계
        self.m_totaTrsAmt = int(subnode.text)

        subnode = node.find("busnCrdcTrsBrkdSn")
        if subnode is not None:    self.m_busnCrdcTrsBrkdSn = subnode.text

        subnode = node.find("vatDdcClNm")         # 비고
        if subnode is not None:    self.m_vatDdcClNm = subnode.text

        subnode = node.find("rowSeq")           # 순서번호
        self.m_rowSeq = int(subnode.text)

        subnode = node.find("busnCrdCardNoEncCntn")    # 카드번호
        if subnode is not None:    self.m_busnCrdCardNoEncCntn = subnode.text

        subnode = node.find("ddcYnNm")        # 공제여부 결정
        if subnode is not None:    self.m_ddcYnNm = subnode.text

        subnode = node.find("splCft")           # 공급가액
        self.m_splCft = int(subnode.text)

        subnode = node.find("busnCrdcTrsBrkdPrhYr")
        if subnode is not None:  self.m_busnCrdcTrsBrkdPrhYr = int(subnode.text)

        subnode = node.find("crcmClCd")
        if subnode is not None:    self.m_crcmClCd = subnode.text

        subnode = node.find("txprDclsCd")
        if subnode is not None:    self.m_txprDclsCd = subnode.text

        subnode = node.find("mrntTin")
        if subnode is not None:    self.m_mrntTin = subnode.text

        subnode = node.find("crdcTxprDscmNoEncCntn")
        if subnode is not None:    self.m_crdcTxprDscmNoEncCntn = subnode.text

        subnode = node.find("bmanClCd")
        if subnode is not None:    self.m_bmanClCd = subnode.text

        subnode = node.find("crdcBmanTxprNm")
        if subnode is not None:    self.m_crdcBmanTxprNm = subnode.text

        subnode = node.find("tip")
        self.m_tip = int(subnode.text)

        subnode = node.find("statusValue")
        if subnode is not None:    self.m_statusValue = subnode.text

        subnode = node.find("aprvDt")      # 승인일자
        if subnode is not None:   self.m_aprvDt = subnode.text

        subnode = node.find("crdcBmanTin")
        if subnode is not None:    self.m_crdcBmanTin = subnode.text

        subnode = node.find("crcmClNm")
        if subnode is not None:   self.m_crcmClNm = subnode.text

        subnode = node.find("vatDdcClCd")
        if subnode is not None:   self.m_vatDdcClCd = subnode.text

        subnode = node.find("prhDt")
        if subnode is not None:   self.m_prhDt = subnode.text

        subnode = node.find("vaTxamt")
        self.m_vaTxamt = int(subnode.text)

        subnode = node.find("bmanClNm")
        if subnode is not None:   self.m_bmanClNm = subnode.text

        subnode = node.find("prhQrt")
        if subnode is None:
            self.m_prhQrt = -1
        else:
            self.m_prhQrt = int(subnode.text)

        subnode = node.find("mrntTxprNm")
        if subnode is not None:   self.m_mrntTxprNm = subnode.text        
        subnode = node.find("bcNm")                 #업태
        if subnode is None:
            self.m_bcNm = ""
        else:
            self.m_bcNm = subnode.text
        subnode = node.find("tfbNm")                 #종목
        if subnode is None:
            self.m_tfbNm = ""
        else:
            self.m_tfbNm = subnode.text  

REFERER_URL = "https://tecr.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/cr/c/b/UTECRCB024.xml" 
class JsHometax_Screen_UTECRCB024:
  def __init__(self):
      self.m_rowSeq = 0                    # 순서번호
      self.m_aprvDt = ""                   # 승인일자
      self.m_crcmClNm = ""                 # 카드사
      self.m_busnCrdCardNoEncCntn = ""     # 카드번호
      self.m_mrntTxprDscmNoEncCntn = ""    # 가맹점 사업자 번호
      self.m_mrntTxprNm = ""               # 가맹점명
      self.m_splCft = 0                    # 공급가액
      self.m_vaTxamt = 0                   # 세액
      self.m_tip = 0                       # 봉사료
      self.m_totaTrsAmt = 0                # 합계
      self.m_bmanClNm = ""                 # 가맹점 유형
      self.m_ddcYnNm = ""                  # 공제여부 결정
      self.m_vatDdcClNm = ""               # 비고
      self.m_busnCrdcTrsBrkdSn = ""
      self.m_busnCrdcTrsBrkdPrhYr = 0      # year
      self.m_crcmClCd = ""
      self.m_txprDclsCd = ""
      self.m_mrntTin = ""
      self.m_crdcTxprDscmNoEncCntn = ""
      self.m_bmanClCd = ""
      self.m_crdcBmanTxprNm = ""
      self.m_statusValue = ""
      self.m_crdcBmanTin = ""
      self.m_vatDdcClCd = ""
      self.m_prhDt = ""                    # Date
      self.m_prhQrt = 0

  def readXML(self, node):
      subnode = node.find("mrntTxprDscmNoEncCntn")   # 가맹점 사업자 번호
      if subnode is None:
          self.m_mrntTxprDscmNoEncCntn= ""
      else:
          self.m_mrntTxprDscmNoEncCntn = subnode.text
      subnode = node.find("totaTrsAmt")               # 합계
      self.m_totaTrsAmt = int(subnode.text)
      
      subnode = node.find("busnCrdcTrsBrkdSn")
      if subnode is None:
          self.m_busnCrdcTrsBrkdSn= ""
      else:
          self.m_busnCrdcTrsBrkdSn = subnode.text

      subnode = node.find("vatDdcClNm")         # 비고
      if subnode is None:
          self.m_vatDdcClNm= ""
      else:
          self.m_vatDdcClNm = subnode.text

      subnode = node.find("rowSeq")           # 순서번호
      self.m_rowSeq = int(subnode.text)

      subnode = node.find("busnCrdCardNoEncCntn")    # 카드번호
      if subnode is None:
          self.m_busnCrdCardNoEncCntn= ""
      else:
          self.m_busnCrdCardNoEncCntn = subnode.text

      subnode = node.find("ddcYnNm")        # 공제여부 결정
      if subnode is None:
          self.m_ddcYnNm= ""
      else:
          self.m_ddcYnNm = subnode.text

      subnode = node.find("splCft")           # 공급가액
      self.m_splCft = int(subnode.text)

      subnode = node.find("busnCrdcTrsBrkdPrhYr")
      self.m_busnCrdcTrsBrkdPrhYr = int(subnode.text)

      subnode = node.find("crcmClCd")
      if subnode is None:
          self.m_crcmClCd= ""
      else:
          self.m_crcmClCd = subnode.text

      subnode = node.find("txprDclsCd")
      if subnode is None:
          self.m_txprDclsCd= ""
      else:
          self.m_txprDclsCd = subnode.text

      subnode = node.find("mrntTin")
      if subnode is None:
          self.m_mrntTin= ""
      else:
          self.m_mrntTin = subnode.text

      subnode = node.find("crdcTxprDscmNoEncCntn")
      if subnode is None:
          self.m_crdcTxprDscmNoEncCntn= ""
      else:
          self.m_crdcTxprDscmNoEncCntn = subnode.text

      subnode = node.find("bmanClCd")
      if subnode is None:
          self.m_bmanClCd= ""
      else:
          self.m_bmanClCd = subnode.text

      subnode = node.find("crdcBmanTxprNm")
      if subnode is None:
          self.m_crdcBmanTxprNm= ""
      else:
          self.m_crdcBmanTxprNm = subnode.text

      subnode = node.find("tip")
      self.m_tip = int(subnode.text)

      subnode = node.find("statusValue")
      if subnode is None:
          self.m_statusValue= ""
      else:
          self.m_statusValue = subnode.text

      subnode = node.find("aprvDt")      # 승인일자
      if subnode is None:
          self.m_aprvDt= ""
      else:
          self.m_aprvDt = subnode.text

      subnode = node.find("crdcBmanTin")
      if subnode is None:
          self.m_crdcBmanTin= ""
      else:
          self.m_crdcBmanTin = subnode.text

      subnode = node.find("crcmClNm")
      if subnode is None:
          self.m_crcmClNm= ""
      else:
          self.m_crcmClNm = subnode.text

      subnode = node.find("vatDdcClCd")
      if subnode is None:
          self.m_vatDdcClCd= ""
      else:
          self.m_vatDdcClCd = subnode.text

      subnode = node.find("prhDt")
      if subnode is None:
          self.m_prhDt= ""
      else:
          self.m_prhDt = subnode.text

      subnode = node.find("vaTxamt")
      self.m_vaTxamt = int(subnode.text)

      subnode = node.find("bmanClNm")
      if subnode is None:
          self.m_bmanClNm= ""
      else:
          self.m_bmanClNm = subnode.text

      subnode = node.find("prhQrt")
      if subnode is None:
          self.m_prhQrt = -1
      else:
          self.m_prhQrt = int(subnode.text)

      subnode = node.find("mrntTxprNm")
      if subnode is None:
          self.m_mrntTxprNm= ""
      else:
          self.m_mrntTxprNm = subnode.text


  @staticmethod
  def _xmlTextToLong(node):
      if node is None or node.text is None:
          return 0
      return int(node.text)

  @staticmethod
  def _xmlTextToInt(node):
      if node is None or node.text is None:
          return 0
      return int(node.text)  
  


  def requestPermission(self):
      rst = 0
      # print("IN UTECRCB024")
      # print(REFERER_URL)
      reqperm_errorCd = 0
      reqperm_errorMsg= ""

      sbSSOToken = ""
      sbuserClCd = ""

      if not jsHometax.getLoginStatus():    return -10

      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB024", None, None, None, reqperm_errorCd, reqperm_errorMsg)
      print("IN UTECRCB024 - jsHometax.requestPermission : " + str(rst))

      if rst != 1:    return rst
      rst = jsHometax.getSSOToken(REFERER_URL)
      sbSSOToken = jsHometax.sbSSOToken
      sbuserClCd = jsHometax.sbuserClCd
      # print(sbSSOToken)     
      # print(sbuserClCd)       
      print("IN UTECRCB024 - jsHometax.getSSOToken : " + str(rst))
      if rst != 1:    return rst
      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB024", "hometax.go.kr", sbSSOToken, sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
      print("IN UTECRCB024 - jsHometax.requestPermission : " + str(rst))
      if rst != 1:    return rst
      
      return 1    
  

  def action_ATECRCCA001R07(self,actionctx, startdate, enddate):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCCA001R07&screenId=UTECRCB024&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCCA001R07&screenId=UTECRCB024&popupYn=false&realScreenId="

      sbResponseData = ""
      strResData = ""
      sbSSOToken = ""
      sbuserClCd = ""

      xmldoc= ""
      xmlnodelst= ""
      xmlnode= ""
      xml_tmpnode= ""
      xmlrawnode_pageInfoVO= ""
      xmlrawnode_sessionMap= ""

      if not jsHometax.getLoginStatus():    return -10

      # xmldoc = XmlDocument()
      result_LoginSystemCtx = jsHometax.LoginSystemContext()

      # 1. First Data
      postdata = "<map id=\"ATECRCCA001R07\"><tin>" + jsHometax.mLoginSystem_Main.m_tin + "</tin><trsDtRngStrt>" + startdate + "</trsDtRngStrt><trsDtRngEnd>" + enddate + "</trsDtRngEnd><prhTxamtDdcYn>all</prhTxamtDdcYn><sumTotaTrsAmt/><resultCd/></map>"
      # print(postdata)
      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, jsHometax._HTTP_ContextType_XML, sbResponseData)
      strResData = jsHometax.sbResponseData    
      # print(strResData)
      if "과부하제어" in strResData:
          ThisMoment = datetime.now()
          duration = datetime.timedelta(seconds=61)   # 61초 후 재생
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
              # System.Windows.Forms.Application.DoEvents()
              ThisMoment = datetime.now()
          return -10000
      elif strResData == "":
          return -10000
      
      xmldoc = ET.fromstring(strResData)
      # print(strResData)
      xmlnodelst = xmldoc.findall("map")
      if xmlnodelst is None:    return -10000
      # print(xmlnodelst)
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
  

  def action_ATECRCCA001R07_getItems(self,actionctx, page,cursor,workyear,strChkDate,HometaxID,HometaxPW,flagSeqNo,biz_no,biz_name):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCCA001R07&screenId=UTECRCB024&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCCA001R07&screenId=UTECRCB024&popupYn=false&realScreenId="
      postdata = f"<map id=\"ATECRCCA001R07\"><tin>{jsHometax.mLoginSystem_Main.m_tin}</tin><trsDtRngStrt>{actionctx.m_trsDtRngStrt}</trsDtRngStrt><trsDtRngEnd>{actionctx.m_trsDtRngEnd}</trsDtRngEnd><prhTxamtDdcYn>all</prhTxamtDdcYn><sumTotaTrsAmt>{actionctx.m_sumTotaTrsAmt}</sumTotaTrsAmt><resultCd>N</resultCd><dwldTrsBrkdScnt>0</dwldTrsBrkdScnt><totalCount>0</totalCount><sumSplCft>{actionctx.m_sumSplCft}</sumSplCft><map id=\"pageInfoVO\"><pageSize>{actionctx.m_pageSize}</pageSize><pageNum>{page}</pageNum><totalCount>{actionctx.m_totalCount}</totalCount></map></map>"

      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, jsHometax._HTTP_ContextType_XML, '')
      strResData = jsHometax.sbResponseData
      if "과부하제어" in strResData:
          print("과부하제어 대기중")
          ThisMoment = datetime.now()
          duration = datetime.timedelta(seconds=61)   #61초 후 재시도
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
              ThisMoment = datetime.now()
          return -9
      elif strResData == "":
          return -10000
      # print(strResData)
      xmldoc = ET.fromstring(strResData)
      xmlnodelst = xmldoc.findall("map")
      if xmlnodelst is None:          return -10000
      xmlnode = xmlnodelst[0]
      if xmlnodelst is None:          return -10000
      list_element = xmldoc.find("list[@id='busnCrdcTrsBrkdAdmDVOList']")
      map_elements = list_element.findall("map")
      if map_elements is None:          return -10000
      i=1
      for node in map_elements:
          item = ActionItem_ATECRCCA001R07()
          item.readXML(node)
          bizName = item.m_mrntTxprNm
          if bizName is not None:bizName = bizName.replace(",", "").replace("'", "")
          mrntTxprNm = item.m_mrntTxprNm
          if mrntTxprNm is not None:mrntTxprNm = mrntTxprNm.replace('\'','')     
          else      : mrntTxprNm = "" 
          tmpMonth = int(strChkDate)*3-2
          tran_dt = item.m_aprvDt
          if strChkDate=='1' and int(item.m_aprvDt[5:7])<tmpMonth: item.m_aprvDt = str(int(item.m_aprvDt[0:4])+1)+"-01-01"
          if strChkDate=='2' and int(item.m_aprvDt[5:7])<tmpMonth: item.m_aprvDt = item.m_aprvDt[0:5]+"04-01"
          if strChkDate=='3' and int(item.m_aprvDt[5:7])<tmpMonth: item.m_aprvDt = item.m_aprvDt[0:5]+"07-01"
          if strChkDate=='4' and int(item.m_aprvDt[5:7])<tmpMonth: item.m_aprvDt = item.m_aprvDt[0:5]+"10-01"   
        #   if strChkDate=='5' and int(item.m_aprvDt[5:7])<1: item.m_aprvDt = str(int(item.m_aprvDt[0:4])+1)+"-01-01"
        #   if strChkDate=='6' and int(item.m_aprvDt[5:7])<7: item.m_aprvDt = item.m_aprvDt[0:5]+"07-01"            
          sql =  "INSERT INTO Tbl_HomeTax_Scrap (Tran_YY, Tran_Dt, Tran_chkseq, Stnd_GB, bcNm, tfbNm, HomeTaxId, HomeTaxPW"
          sql += " , Biz_No, Seq_No, RowSeq, biz_name, Biz_Card_TY, AprvDt, CrcmClNm, busnCrdCardNoEncCntn, mrntTxprDscmNoEncCntn, mrntTxprNm, splCft, vaTxamt, tip, totaTrsAmt, bmanClNm"
          sql += " , ddcYnNm, vatDdcClNm, VatChkTY, File_DdctGB, Acnt_Cd, Acnt_Nm, Gerenel_Ty, Crt_Dt, Db_Ins_YN, Db_Ins_Dt, File_MK_YN, File_MK_Dt, WK_GB, lawRsn) "
          sql += " VALUES ('"+str(workyear)+"','"+tran_dt+"','"+str(i)+"','"+strChkDate+"','"+item.m_bcNm+"','"+item.m_tfbNm+"','"+HometaxID+"','"+HometaxPW
          sql += "','"+biz_no+"','"+flagSeqNo+"','"+str(item.m_rowSeq)+"','"+biz_name+"','3','"+item.m_aprvDt+"','"+item.m_crcmClNm+"','"+item.m_busnCrdCardNoEncCntn
          sql += "','"+item.m_mrntTxprDscmNoEncCntn+"','"+mrntTxprNm+"','"+str(item.m_splCft)+"','"+str(item.m_vaTxamt)+"','"+str(item.m_tip)+"','"+str(item.m_totaTrsAmt)+"','"+item.m_bmanClNm
          sql += "','"+item.m_ddcYnNm+"','"+item.m_vatDdcClNm+"','57','Y','830','소모품비','','"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"','Y','','','','','')"
          cursor.execute(sql)
          connection.commit()
          i += 1
      return 1
