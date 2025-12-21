#####################################
#     전자세금계산서 저장
#####################################


from datetime import datetime
import time
import json
from app.test import jsHometax
from django.db import connection
from app.test import utils

REFERER_URL = "https://teet.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/etx/pp/UTEETBDA03.xml"
# referer_url_success = "https://teet.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml"
class ActionCtx_UTEETBDA03:
    def __init__(self):
        self.m_inqrDtStrt = ""    # 조회시작일자
        self.m_inqrDtEnd = ""     # 조회종료일자
        self.m_pageSize = 0       # 페이지당 아이템 개수
        self.m_pageCount = 0      # 페이지 개수
        self.m_totalCount = 0     # 전체 아이템 수

        self.m_wTotaAmt = 0  # 총공급대가
        self.m_wSumTxamt = 0  # 총공급가액

        self.m_qCd = ""           #01 = 1기 예정 02 = 1기 확정 03 = 1기 예+확 04 = 2기 예정 05 = 2기 확정06 = 2기 예+확
        self.m_yCd = ""           #조회연도
        self.m_etxivClCd = ""     #01 : 세금계산서    03 : 계산서

        self.m_bmanCd = ""        # 00 (매출자 기준)  01 (매입자 기준)
        self.m_prhSlsClCd = ""    #01 = 매출, 02 = 매입        
        self.m_dmnrTin = ""       #공급받는자 ==> 매입일 경우 cnvr_tin을 넣는다
        self.m_splrTin = ""       #공급자    ==> 매출일 경우 cnvr_tin을 넣는다
        


def action_ATEETBDA005R06_getItems(i,invoice_list, memuser):
    today = str(datetime.now())[:10].replace("-","")
    for row in invoice_list:
        if i in [1,2]: 
          approveNo = row.get("etan", "")
          kkdk      = str(row.get("totaAmt", "0")).replace(",", "")
          kkke      = str(row.get("sumSplCft", "0")).replace(",", "")
          kkkt      = str(row.get("sumTxamt", "0")).replace(",", "")
          TIsep     = row.get("etxivKndCd")       #전자세금계산서분류
          TIuh      = row.get("isnTypeCd")       #발급유형  인터넷/asp  
          receiveYN = row.get("recApeClCd")        #영수/청구
          eml_sup   = row.get("mchrgEmlAdrSls") or ''
          eml_buyer1=row.get("mchrgEmlAdrPrh") or ''
        else:          
          approveNo = row.get("etan", "")
          kkdk      = str(row.get("totaAmt", "0")).replace(",", "")
          kkke      = str(row.get("totaAmt", "0")).replace(",", "")
          kkkt      = "0"
          TIsep     = str(row.get("etxivKndCd", "0")) #전자세금계산서분류
          TIuh      = row.get("isnTypeCd")       #발급유형  인터넷/asp 
          receiveYN = row.get("recApeClCd")        #영수/청구
          eml_sup   = row.get("mchrgEmlAdrSls") or ''
          eml_buyer1= row.get("mchrgEmlAdrPrh") or ''
        supplier_name="";buyer_name="";supplier_ceoname="";buyer_ceoname=""
        if i in [1,3]:
          supplier_bizno = row.get("splrTxprDscmNo")
          supplier_name = memuser.biz_name      #tnmNmB
          supplier_ceoname = memuser.ceo_name   #rprsFnmB
          supplier_address = row.get("adrB", "") or ''
          supplier_address = supplier_address.replace("'", "")
          buyer_bizno = row.get("dmnrTxprDscmNo")      
          buyer_name=row.get("tnmNm") or ''
          buyer_name = buyer_name.replace("\'","")
          buyer_ceoname = row.get("rprsFnm") or ''
          buyer_ceoname = buyer_ceoname.replace("\'","")
          buyer_address = row.get("adr") or ''
          buyer_address = buyer_address.replace("'", "")
        else:
          supplier_bizno = row.get("splrTxprDscmNo")
          supplier_name=row.get("tnmNm") or ''
          supplier_name = supplier_name.replace("\'","")
          supplier_ceoname = row.get("rprsFnm") or ''
          supplier_ceoname = supplier_ceoname.replace("\'","")
          supplier_address = row.get("adr") or ''
          supplier_address = supplier_address.replace("'", "")
          buyer_bizno = row.get("dmnrTxprDscmNo")      
          buyer_name =  memuser.biz_name    #tnmNmB
          buyer_ceoname = memuser.ceo_name    #rprsFnmB
          buyer_address = row.get("adrB") or ''
          buyer_address = buyer_address.replace("'", "")  

        sql_select = f"select 승인번호 from 전자세금계산서 where seq_no={memuser.seq_no} and 승인번호='{approveNo}'"   
        with connection.cursor() as cursor:
          cursor.execute(sql_select)
          result = cursor.fetchone()

          if result is None:
            #sql = "Merge 전자세금계산서 as A Using (select  '"+memuser.seq_no+"' as seq_no,'"+approveNo+"' as 승인번호 ) as B "
            #sql += "On A.승인번호 = B.승인번호 and A.seq_no=B.seq_no when not matched then "
            sql = "insert into  전자세금계산서 values('"
            sql += memuser.seq_no+"','"
            sql += memuser.biz_no+"','"
            sql += str(i)+"','"
            sql += row.get("wrtDt")+"','"   #작성일자
            sql += approveNo+"','"
            sql += row.get("isnDtm")+"','"  #발급일자
            sql += row.get("tmsnDt")+"','"  #전송일자
            sql += supplier_bizno+"','"
            sql += supplier_name + "','"    #공급자상호
            sql += supplier_ceoname + "','" #공급자성명
            sql += supplier_address + "','"  #공급자주소
            sql += buyer_bizno +"','"
            sql += buyer_name +"','"
            sql += buyer_ceoname +"','"
            sql += buyer_address + "','"
            sql += kkdk +"','"  #합계
            sql += kkke +"','"  #공급가액
            sql += kkkt +"','"  #세액
            sql += TIsep +"','" #전자세금계산서분류
            sql += row.get("etxivKndCd", "") + "','"        #전자세금계산서종류
            sql += TIuh +"','"  #발급유형  인터넷/asp
            sql += row.get("etxivSq1RmrkCntn", "") + "','"        #비고
            sql += receiveYN +"','"  #영수/청구
            sql += eml_sup +"','"  #공급자이메일
            sql += eml_buyer1 +"','"  #공급받는자이메일1
            sql += "','"      #공급받는자이메일2
            lsatSplDt = row.get("lsatSplDt")  or ''                            
            sql += lsatSplDt + "','"             #품목일자
            lsatNm = row.get("lsatNm") or ''
            sql += lsatNm.replace("\'","")+"','"   #품목명
            lsatUtprc = row.get("lsatUtprc") or ''
            lsatQty = row.get("lsatQty") or ''
            lsatSplCft = row.get("lsatSplCft") or 0
            lsatTxamt = row.get("lsatTxamt") or 0
            sql += f"{lsatUtprc}','"                #품목규격
            sql += f"{lsatQty}','"               #품목수량
            sql += f"{lsatSplCft}','"             #품목단가
            sql += f"{lsatSplCft}','"             #품목공급가액
            sql += f"{lsatTxamt}','"             #품목세액
            sql += "','"                                   #품목비고
            sql += today + "','"
            sql += "','"
            sql += "','"
            sql += "N','','','');"
            print(sql)
            with connection.cursor() as cursor:
              cursor.execute(sql)
              connection.commit()           
              print('디비저장성공')
            strsql = "exec SP_세금계산서_Scrap '" + memuser.seq_no + "','" + today + "','"+approveNo+"' "
            utils.execute_query_with_retry(strsql);time.sleep(0.1)  
    return 1



class JsHometax_Screen_UTEETBDA03:
    def requestPermission(self):
        rst = 0
        reqperm_errorCd = 0
        reqperm_errorMsg = ""

        if not jsHometax.getLoginStatus():
            return -10

        rst = jsHometax.requestPermission(REFERER_URL, "teet", "UTEETBDA03", "teet.hometax.go.kr", jsHometax.sbSSOToken, jsHometax.sbuserClCd, reqperm_errorCd, reqperm_errorMsg)
        return rst

    def action_ATEETBDA005R06(gubun, actionctxTI,  memuser):
        url = "https://teet.hometax.go.kr/wqAction.do?actionId=ATEETBDA005R06&screenId=UTEETBDA03&popupYn=false&realScreenId="
        refererUrl = url

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
        
        page = 1
        while True:
          payload = {
              "baseDt": "",
              "cstnInfoYn": "",
              "fleDwldYn": "",
              "fleTp": "",
              "icldCstnBmanInfr": "",
              "icldLsatInfr": "N",
              "resnoSecYn": "Y",
              "schBaseDt": "20250301",
              "srtClCd": "1",
              "srtOpt": "01",
              "pageInfoVO": {  "pageNum": page, "pageSize": "10", "totalCount": ""},
              "excelPageInfoVO": {"pageNum": "1", "pageSize": "10", "totalCount": "0"},
              "etxivIsnBrkdTermDVOPrmt": {
                  "bmanCd": actionctxTI.m_bmanCd,           #00 (매출자 기준)  01 (매입자 기준)
                  "dmnrMpbNo": "",
                  "dmnrTxprDscmNo": "",
                  "etxivClsfCd": "all",
                  "etxivKndCd": "all",
                  "gubunCd": "",
                  "isnTypeCd": "all",
                  "mCd": "04",#항상 동일
                  "mqCd": "2",#항상 동일
                  "pageNum": "",
                  "prhSlsClCd": actionctxTI.m_prhSlsClCd,   #01 = 매출, 02 = 매입
                  "qCd": actionctxTI.m_qCd,          #01 = 1기 예정 02 = 1기 확정 03 = 1기 예+확 04 = 2기 예정 05 = 2기 확정06 = 2기 예+확
                  "radio8": "",
                  "screenId": "",
                  "splrMpbNo": "",
                  "splrTxprDscmNo": "",
                  "tnmNm": "",
                  "yCd": actionctxTI.m_yCd,        #조회연도
                  "dmnrTin": actionctxTI.m_dmnrTin,        #공급받는자 ==> 매입일 경우 cnvr_tin을 넣는다
                  "dtCl": "01",#항상동일
                  "etxivClCd": actionctxTI.m_etxivClCd,    #01 : 세금계산서    03 : 계산서
                  "inqrDtEnd": actionctxTI.m_inqrDtEnd,      #조회종료
                  "inqrDtStrt": actionctxTI.m_inqrDtStrt,     #조회시작
                  "pageSize": "10",
                  "splrTin": actionctxTI.m_splrTin,  
                  "tmsnDtIn": "",
                  "tmsnDtOut": ""
              },
              "ntsData": jsHometax.sbSSOToken
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
              raise Exception(f"❌ 요청 실패: {response.status_code}")

          result = response.json()
          result_msg = result.get("resultMsg", {})

          if result_msg.get("result") != "S":
              raise Exception(f"❌ 조회 실패: {result_msg.get('msg')}")

          invoice_list = result.get("etxivIsnBrkdTermDVOList", [])
          action_ATEETBDA005R06_getItems(gubun,invoice_list, memuser)
          
          KKKK_info = result.get("etxivIsnBrkdTermDVO", {})
          wTotaAmt = KKKK_info.get("wTotaAmt", 0) or 0
          wSumTxamt = KKKK_info.get("wSumTxamt", 0) or 0
          actionctxTI.m_wTotaAmt = wTotaAmt
          actionctxTI.m_wSumTxamt = wSumTxamt

          page_info = result.get("pageInfoVO", {})
          total_count = int(page_info.get("totalCount", 0))
          page_size = int(page_info.get("pageSize", 10))
          total_page = (total_count + page_size - 1) // page_size

          print(f"✅ {page}/{total_page} 페이지 완료 {memuser.biz_name} {actionctxTI.m_yCd}년 {actionctxTI.m_qCd}분기 전자세금계산서 저장 (구분 {gubun}: 1-매출세계, 2-매입세계, 3-매출계, 4-매입계)")

          if page >= total_page:
              break

          page += 1


        return 1
