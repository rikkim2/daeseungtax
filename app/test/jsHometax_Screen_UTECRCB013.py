####################################
#   현금영수증 사용내역 조회 #
#   2024년말경 XML방식에서 JSON방식으로 변경됨
####################################
import json
import datetime
import xml.etree.ElementTree as ET
from app.test import jsHometax
from django.db import connection
from app.test import utils

######################
# 현금영수증 건별매출 #
######################
class ActionCtx_ATECRCBA001R03:
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


REFERER_URL = "https://tecr.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/cr/c/b/UTECRCB024.xml"
class JsHometax_Screen_UTECRCB013:

  def requestPermission(self):
      rst = 0
      # print("IN UTECRCB023")
      # print(REFERER_URL)
      reqperm_errorCd = 0
      reqperm_errorMsg = None

      sbSSOToken = ""
      sbuserClCd = ""

      if not jsHometax.getLoginStatus():    return -10

      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB013", None, None, None, reqperm_errorCd, reqperm_errorMsg)
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
      rst = jsHometax.requestPermission(REFERER_URL, "tecr", "UTECRCB013", "hometax.go.kr", sbSSOToken, sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
      # print(rst)
      if rst != 1:    return rst
      
      return 1

  def action_ATECRCBA001R03(self,actionctx, startdate, enddate):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R03&screenId=UTECRCB013&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R03&screenId=UTECRCB013&popupYn=false&realScreenId="

      sbResponseData = ""
      strResData = ""
      sbSSOToken = ""
      sbuserClCd = ""


      if not jsHometax.getLoginStatus():    return -10
      # 1.요청페이로드
      postdata = {
        "tin": jsHometax.mLoginSystem_Main.m_tin,
        "trsDtRngStrt": startdate,
        "trsDtRngEnd": enddate,
        "prhTxamtDdcYn": "all",
        "sumTotaTrsAmt": "",
        "resultCd": "",
        "ntsData": "nts>23TmC70S5nbs1Cp3CBBvRTOri7JmTSInZ71uwWQfcqI12"
      }
      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, 'application/json', sbResponseData)
      strResData = jsHometax.sbResponseData    
      #print(strResData)
      if "과부하제어" in strResData:
          print("과부하제어 대기중")
          ThisMoment = datetime.now()
          duration = datetime.timedelta(seconds=61)   # 61초 후 재생
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
            ThisMoment = datetime.now()
          return -9
      elif strResData == "":
          return -10000
      
      response_data = json.loads(strResData)
      actionctx.m_sumTotaTrsAmt = response_data.get("sumTotaTrsAmt")
      actionctx.m_sumSplCft = response_data.get("sumSplCft")
      actionctx.m_trsDtRngStrt = response_data.get("trsDtRngStrt")
      actionctx.m_trsDtRngEnd = response_data.get("trsDtRngEnd")
      
      pageSize = response_data.get("pageInfoVO", {}).get("pageSize")
      if pageSize:      actionctx.m_pageSize = int(pageSize)
      totalCount = response_data.get("pageInfoVO", {}).get("totalCount")
      if totalCount:      actionctx.m_totalCount = int(totalCount)
      actionctx.m_pageCount = ((actionctx.m_totalCount + actionctx.m_pageSize - 1) // actionctx.m_pageSize)

      return 1  

  def action_ATECRCBA001R03_getItems(self,actionctx, page,cursor,workyear,strChkDate,txtRangeStart,txtRangeEnd,HometaxID,HometaxPW,flagSeqNo,biz_no,biz_name):
      refererUrl = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R03&screenId=UTECRCB013&popupYn=false&realScreenId="
      url = "https://tecr.hometax.go.kr/wqAction.do?actionId=ATECRCBA001R03&screenId=UTECRCB013&popupYn=false&realScreenId="
      postdata = {
        "tin": jsHometax.mLoginSystem_Main.m_tin,
        "trsDtRngStrt": actionctx.m_trsDtRngStrt,
        "trsDtRngEnd": actionctx.m_trsDtRngEnd,
        "prhTxamtDdcYn": "all",
        "sumTotaTrsAmt": actionctx.m_sumTotaTrsAmt,
        "resultCd": "N",
        "dwldTrsBrkdScnt":"0",
        "totalCount":'0',
        "sumSplCft":actionctx.m_sumSplCft,
        "pageInfoVO": {
            "pageNum": page,
            "pageSize": actionctx.m_pageSize,
            "totalCount": actionctx.m_totalCount
        },        
        "ntsData": "nts>23TmC70S5nbs1Cp3CBBvRTOri7JmTSInZ71uwWQfcqI12"
      }
      rst = jsHometax.httpRequest_post(url, postdata, refererUrl, None, "application/json", '')
      strResData = jsHometax.sbResponseData

      if "과부하제어" in strResData:
          print("과부하제어 대기중")
          ThisMoment = datetime.datetime.now()
          duration = datetime.timedelta(seconds=61)   #61초 후 재시도
          AfterWards = ThisMoment + duration
          while AfterWards >= ThisMoment:
              ThisMoment = datetime.datetime.now()
          return -10000
      elif strResData == "":
          return -10000
      # print(strResData)
      response_data = json.loads(strResData)


    #   list_element = xmldoc.find("list[@id='cshTrsBrkdInqrDVOList']")
      list_element = response_data.get("cshTrsBrkdInqrDVOList", [])

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
        sql += f",isnull((select max(rowSeq)+1 from Tbl_HomeTax_CashCost where seq_no={flagSeqNo} and left(tran_dt,4)={workyear} and stnd_GB='{utils.get_quarter(m_trsDtm[5:7])}'),0)"
        sql += f",'{utils.get_quarter(m_trsDtm[5:7])}','{flagSeqNo}','{biz_name}','{m_cshptTrsTypeNm}','{m_splCft}','{m_vaTxamt}'"
        sql += f",'{m_tip}','{m_totaTrsAmt}','{m_aprvNo}','{m_trsClNm}','{m_trsClCd}','{m_pblClCd}','{m_spstCnfrPartNo}'"
        sql += f",'{m_rcprTxprNm}','{m_spstCnfrClNm}','{m_cshptUsgClNm}',getdate())"
        # print(sql)
        cursor.execute(sql)
        connection.commit()
      
      return 1
