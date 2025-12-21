import os
import math
from decimal import Decimal
import time
import json
import PyPDF2
from dotenv import load_dotenv
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
import datetime
from datetime import datetime
import smtplib
import locale
import natsort ## 숫자 정렬용 라이브러리
from django.core.cache import cache
from django.utils.timezone import now
from urllib.parse import unquote
from django.http import JsonResponse
from django.db import connection, transaction
from django.views.decorators.csrf import csrf_exempt
from app.models import MemDeal
from app.models import MemUser
from app.models import MemAdmin
from app.models import userProfile
from popbill import (
    ContactInfo,
    CorpInfo,
    JoinForm,
    KakaoButton,
    KakaoReceiver,
    KakaoService,
    MessageService,
    PaymentForm,
    PopbillException,
    RefundForm,
)
from django.db.models import Q
from django.db.models import F, Subquery, OuterRef
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app.models import TblMail
from app.models import TblGoji
from app.models import TblEquityeval  # 모델 import (실제 경로에 맞게 수정)
from app.models import TblMngJaroe
from django.core.exceptions import ObjectDoesNotExist

import mimetypes
from pathlib import Path
from typing import Iterable, Tuple, List

# 탭메뉴 관련
def render_tab_template(request, template_name, context=None):
    """
    1. 탭 요청(AJAX)이면 -> 해당 템플릿(내용물만 있음)을 그대로 렌더링
    2. 일반 요청(주소창 입력, 새로고침)이면 -> 대시보드(dsboard)로 강제 이동
    """
    if context is None:
        context = {}

    # 1. 탭 관리자(TabManager)를 통한 요청인 경우
    if request.GET.get('is_ajax_tab') == '1':
        return render(request, template_name, context)

    # 2. 일반 접근인 경우 (새로고침 포함) -> 메인 대시보드로 튕겨냄
    # 'dsboard'는 urls.py에 정의된 대시보드 name이어야 합니다.
    return redirect('dsboard')


# 메일 발송내용을 결정한다 => template도 확인해야돼
@csrf_exempt
def sendMail(request):
  if request.method != "POST":
    return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)
  MailAddr = 'daeseung23@gmail.com'
  data = json.loads(request.body)
  seq_no = data.get("seq_no","")  
  work_YY = data.get("work_YY","")
  work_MM = data.get("work_MM","")
  work_qt = 0
  if work_MM in [1, 2, 3]:
      work_qt = 1
  elif work_MM in [4, 5, 6]:
      work_qt = 2
  elif work_MM in [7, 8, 9]:
      work_qt = 3
  elif work_MM in [10, 11, 12]:
      work_qt = 4    
  mail_class = data.get("mail_class","") 
  sendmail_class = mail_class
  targetUrl =  data.get("targetUrl","") 

  # 제목, 본문 작성
  memuser = MemUser.objects.get(seq_no=seq_no)
  memdeal = MemDeal.objects.get(seq_no=seq_no)
  memadmin = MemAdmin.objects.filter(
    admin_id=Subquery(
        MemDeal.objects.filter(seq_no=seq_no).values('biz_manager')[:1]
    )
  ).values('admin_name', 'admin_tel_no','admin_email').first()

  Subject = ""
  Content = ""
  tax_data = []
  TXT_CorpName = "세무법인대승"
  TXT_OfficeAddress = "서울특별시 강남구 강남대로84길 15, 206호(역삼동, 강남역효성해링턴타워)"
  recipient_list = [email.strip() for email in memuser.email.split(";") if email.strip()]  # 리스트 변환
  # ✅ 수신자가 없으면 종료
  if not recipient_list:
      print( "수신자 이메일이 존재하지 않습니다.")
      return JsonResponse({"error": "수신자 이메일이 존재하지 않습니다."}, status=400)  
  user_file_names =  data.get("user_file_names","")  # 파일명 리스트 (JSON 배열)
  user_path = data.get("user_path","")  # 파일 저장 경로  

  half_length = len(memuser.user_pwd) // 2  # 앞 절반의 길이
  strPassword = memuser.user_pwd[:half_length] + '*' * (len(memuser.user_pwd) - half_length)
  if memuser.user_pwd=="1":
    strPassword = "최초 1로 설정되어 있으며 로그인시 임시비밀번호를 이메일로 전달받아 비밀번호를 수정하시기 바랍니다."

  if mail_class=='goji':
    Subject = f"[{TXT_CorpName}] {work_YY}년 {work_MM}월 고지세액 안내 - {memuser.biz_name}"
    tax_data = list(TblGoji.objects.filter(seq_no=seq_no,work_yy=work_YY,work_mm=work_MM).values(
        'taxmok', 'taxamt', 'taxnapbunum', 'taxoffice', 'taxduedate'
    ))
  elif mail_class=='pay':    
    mail_class = "Mail"
    Subject = f"[{TXT_CorpName}] {work_YY}년 {work_MM}월 귀속 급여대장 및 원천세 신고납부 안내 - {memuser.biz_name}"
    strPay = resultmsg2 = resultmsg1 =has_Napbuseo= ""
    yearAndMonth = f"{work_YY}{work_MM}"
    if len(str(work_MM)) == 1:
      yearAndMonth = f"{work_YY}0{work_MM}"    
    sql = ("SELECT * FROM 원천세전자신고 WHERE 사업자등록번호=%s and 과세연월=%s ")
    rs = fetch_results(sql, (memuser.biz_no,yearAndMonth))

    if rs: 
      rs = rs[0]  # 첫 번째 딕셔너리 가져오기
      arrPay = []
      if int(rs["A01"]) > 0:          arrPay.append("근로")
      if int(rs["a03"]) > 0:          arrPay.append("일용")
      if int(rs["A20"]) > 0:          arrPay.append("퇴직")
      if int(rs["A30"]) > 0:          arrPay.append("사업")
      if int(rs["A40"]) > 0:          arrPay.append("기타")
      if int(rs["A50"]) > 0:          arrPay.append("이자")
      if int(rs["A60"]) > 0:          arrPay.append("배당")
      #if int(rs["A80"]) > 0:          arrPay.append("법인원천")
      strPay = ", ".join(arrPay) if arrPay else ""    

      folder_path = os.path.join('static/cert_DS/', memuser.biz_name, str(work_YY), "인건비")
      if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # 폴더 내 파일 목록 가져오기
        monthly_files = [file for file in files if file.startswith(f"{work_MM}월")]  # "12월"로 시작하는 파일 필터링
        if monthly_files:
          has_Napbuseo = any("납부서" in file for file in monthly_files)      

      if has_Napbuseo:
        resultmsg1 = "첨부된 원천세 및 지방세 납부서를 확인하여 가까운 은행에 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
        resultmsg1 += "홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 원천세를 선택하여 납부하시기 바랍니다."

      # 신고됐는데 납부서가 없는 경우
      else:
        if memdeal.goyoung_banki=="Y":
          resultmsg1 = f"[{memuser.biz_name}]의 경우 반기신고 대상자이므로 원천징수한 소득세등은 반기의 다음달 10일까지 납부서를 발송드릴 예정입니다. "
        else:
          resultmsg1 = "당월은 원천세 및 지방세 납부가 없습니다. 급여대장상 납부금액과 납부서상 납부할 금액이 차이나는 경우 연말정산 환급금과 당월분 납부금액이 상계된 것입니다."
      if int(rs["A01"]) > 0: 
        if int(work_MM)==2:
          resultmsg2 = f"{work_MM}월은 근로자 연말정산 환급(징수)분이 반영되어 차인지급액 변동이 있으니 급여대장상의 차인지급액을 다시 한번 확인하여 주시기 바랍니다."
        elif int(work_MM)==7:
          resultmsg2 = f"{work_MM}월은 국민연금 변경(기준소득월액 결정)분이 반영되어 차인지급액 변동이 있으니 급여대장상의 차인지급액을 다시 한번 확인하여 주시기 바랍니다."
                  
    else:
      strPay = "근로소득"
      if memdeal.goyoung_banki=="Y":
        resultmsg1 = f"[{memuser.biz_name}]의 경우 반기신고 대상자이므로 원천징수한 소득세등은 반기의 다음달 10일까지 납부서를 발송드릴 예정입니다. "
      else:
        resultmsg1 = "당월은 원천세 및 지방세 납부가 없습니다. 급여대장상 납부금액과 납부서상 납부할 금액이 차이나는 경우 연말정산 환급금과 당월분 납부금액이 상계된 것입니다."

    tax_data.append({
      "strPay":strPay,
      "user_id":memuser.user_id,
      "strPassword":strPassword,       
      "resultmsg1":resultmsg1,
      "resultmsg2":resultmsg2
    })      
    tax_data = tax_data[0]
  elif mail_class=='CorpIntro':
    Subject = f"[{TXT_CorpName}] {work_YY}년 귀속 법인세 신고 안내 - {memuser.biz_name}"
    tax_data.append({"next_YY":int(work_YY)+1})
    mail_class = "Corp"
  elif mail_class=='CorpResult':
    Subject = f"[{TXT_CorpName}] {work_YY}년 귀속 법인세 접수결과 안내 - {memuser.biz_name}"
    txtfiscalMM = f"0{memdeal.fiscalmm}" if int(memdeal.fiscalmm) < 10 else str(memdeal.fiscalmm)
    yearEnd = f"{work_YY}{txtfiscalMM}"    
    tax_result = list(TblEquityeval.objects.filter(사업자번호=memuser.biz_no,  사업연도말=yearEnd ).values(
      "수입금액","농특세","분납세액","차감납부세액","최저한세적용대상","최저한세적용제외","산출세액_법인세","산출세액_토지","산출세액_합계","차감납부세액_법인세","차감납부세액_토지","차감납부세액_합계","과세표준_법인세","과세표준_토지","과세표준_합계"
    ))   
    mail_class = "Corp"

    if tax_result:
      nongtax = str(tax_result[0]["농특세"]).strip()  # Trim() -> strip(), 값이 없으면 빈 문자열 반환
      nongtax_bunnap = nongtax_afterChungdang = 0
      dueDate_Corptax = "03.31"; dueDate_wetax = "04.30"; dueDate_bunnap = "05.31"; 
      if txtfiscalMM=="06":
        dueDate_Corptax = "09.30"; dueDate_wetax = "10.31"; dueDate_bunnap = "11.30"; 
      elif txtfiscalMM=="03":
        dueDate_Corptax = "06.30"; dueDate_wetax = "07.31"; dueDate_bunnap = "08.31"; 
      if nongtax and nongtax != "0":  # 빈 문자열과 "0"이 아닌 경우만 실행
        nongtax_bunnap = float(nongtax[15:30])  # Mid(nongtax,16,15) -> 슬라이싱 [15:30]
        nongtax_afterChungdang = float(nongtax[-15:])  # Right(nongtax,15) -> 슬라이싱 [-15:]

      if nongtax_bunnap > 0:
        strBunnap = f"(농특세 : {format(nongtax_bunnap // 10 * 10, ',')} 별도)    {format(int(tax_result['분납세액']) // 10 * 10, ',')}"
      else:
        strBunnap = f"{format(int(tax_result[0]['분납세액']) // 10 * 10, ',')}"
      ckn =  "{:,.0f}".format(int(tax_result[0]['차감납부세액'])// 10 * 10)
      nts = "{:,.0f}".format(nongtax_afterChungdang// 10 * 10)
      if nongtax_afterChungdang > 0:
        strNongtax = f"(농특세 : {nts} 별도)    {ckn}"
      else:
        strNongtax = ckn
      taxDeduct = int(tax_result[0]["최저한세적용대상"])+int(tax_result[0]["최저한세적용제외"])
      taxSanchun_Corptax =   (int(tax_result[0]["산출세액_법인세"])/10 // 10) * 10 
      taxSanchun_Land =   (int(tax_result[0]["산출세액_토지"])/10 // 10) * 10  
      taxSanchun_Total =(int(tax_result[0]["산출세액_합계"])/10 // 10) * 10 
      taxCKK_corptax = (int(tax_result[0]["차감납부세액_법인세"]) // 10) * 10  
      taxCKK_land = (int(tax_result[0]["차감납부세액_토지"]) // 10) * 10  
      taxCKK_total = (int(tax_result[0]["차감납부세액_합계"]) // 10) * 10  

      resultmsg2 = resultmsg1 = ""
      if int(tax_result[0]["차감납부세액"]) < 0:
          if int(tax_result[0]["과세표준_합계"]) > 0:
              resultmsg1 = "금번 법인세는 세액감면 공제를 통하여 납부할 세액 없이 신고 마쳤습니다. "
              resultmsg1 += "당기에 발생한 세액공제를 전액 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
          else:
              resultmsg1 = f"{work_YY}년에 발생된 결손금은 이월되어 향후 10년 내 발생하는 순이익에서 차감되며 납부할 법인세를 감소시킵니다. "
          if int(tax_result[0]["산출세액_합계"])>0:
              resultmsg1 += "다만, 법인세할 지방소득세는 보내드린 지방세 납부서를 통하여 다음달 말일까지 납부하여 주시기 바랍니다. "
          resultmsg2 = "법인세 환급액은 다음달 말일까지 등록된 사업용계좌로 입금됩니다. "
      
      # "차감납부세액" 값이 0이면
      elif int(tax_result[0]["차감납부세액"]) == 0:
          if int(tax_result[0]["과세표준_합계"]) > 0:
              resultmsg1 = "금번 법인세는 세액감면 공제를 통하여 납부할 세액 없이 신고 마쳤습니다. "
              resultmsg2 = "당기에 발생한 세액공제를 전액 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
          else:
              resultmsg1 = f"{work_YY}년에 발생된 결손금은 이월되어 향후 10년 내 발생하는 순이익에서 차감되며 납부할 법인세를 감소시킵니다. "
              resultmsg2 = "당기에 발생한 세액공제를 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
          if int(tax_result[0]["산출세액_합계"])>0:
              resultmsg1 += "다만, 법인세할 지방소득세는 보내드린 지방세 납부서를 통하여 다음달 말일까지 납부하여 주시기 바랍니다. "

      # "차감납부세액" 값이 0보다 크면
      else:
          resultmsg1 = "법인세 및 조세특례제한법상 세액감면 공제사항을 모두 검토 반영하여 신고서를 작성하였습니다."
          resultmsg2 = "첨부된 법인세 및 지방세 납부서를 확인하여 가까운 은행에 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
          resultmsg2 += "홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 법인세를 선택하여 납부하시기 바랍니다. "

      new_data = {
        "next_YY":int(work_YY)+1,
        "user_id":memuser.user_id,
        "strPassword":strPassword,        
        "resultmsg1":resultmsg1,
        "resultmsg2":resultmsg2,
        "revenue": "{:,.0f}".format(float(tax_result[0]["수입금액"])), 
        "total_tax": "{:,.0f}".format(float(tax_result[0]["차감납부세액"])),
        "taxKwase_corptax":"{:,.0f}".format(float(tax_result[0]["과세표준_법인세"])),
        "taxKwase_land":"{:,.0f}".format(float(tax_result[0]["과세표준_토지"])),
        "taxKwase_total":"{:,.0f}".format(float(tax_result[0]["과세표준_합계"])),
        "taxCKK_corptax":"{:,.0f}".format(taxCKK_corptax),
        "taxCKK_land":"{:,.0f}".format(taxCKK_land),
        "taxCKK_total":"{:,.0f}".format(taxCKK_total),
        "nongtax_bunnap":"{:,.0f}".format(float(nongtax_bunnap)),
        "dueDate_bunnap":dueDate_bunnap,
        "dueDate_wetax":dueDate_wetax,
        "dueDate_Corptax":dueDate_Corptax,
        "strBunnap":strBunnap,
        "strNongtax":strNongtax,
        "taxDeduct":"{:,.0f}".format(float(taxDeduct)),
        "taxSanchun_Corptax":"{:,.0f}".format(float(taxSanchun_Corptax)),#지방세
        "taxSanchun_Land":"{:,.0f}".format(float(taxSanchun_Land)),
        "taxSanchun_Total":"{:,.0f}".format(float(taxSanchun_Total))
      }
      tax_data.append(new_data) 
      tax_data = tax_data[0]
  elif mail_class=='CorpJungkanIntro':
    mail_class = "Corp"
    Subject = f"[{TXT_CorpName}] {work_YY}년 귀속 법인세 중간예납 신고납부 안내 - {memuser.biz_name}"
    sql = f"select ISNULL(총부담세액_합계, 0) total_tax from tbl_equityeval WHERE 사업자번호='{memuser.biz_no}' AND left(사업연도말,4)='{work_YY-1}'"
    # print(sql)
    rows = fetch_results(sql,'')
    if not rows:
        total_tax = 0.0
    else:
        first = rows[0]
        if isinstance(first, dict):
            total_tax = float(first.get("total_tax") or 0.0)
        elif isinstance(first, (list, tuple)):
            total_tax = float(first[0] or 0.0)
        else:
            total_tax = float(first or 0.0)

    preTax = total_tax / 2
    new_data = {
      "work_YY":work_YY,
      "user_id":memuser.user_id,
      "strPassword":strPassword,        
      "preTax":"{:,.0f}".format(float(preTax))
    }
    tax_data.append(new_data) 
    tax_data = tax_data[0]
  elif mail_class=='CorpJungkanResult':
    mail_class = "Corp"
    Subject = f"[{TXT_CorpName}] {work_YY}년 귀속 법인세 중간예납 신고결과 안내 - {memuser.biz_name}"
    sql = f"select 중간예납신고방법,법인세  from tbl_equityeval_MID WHERE 사업자번호='{memuser.biz_no}' AND left(사업연도말,4)='{work_YY}'"
    # print(sql)
    rows = fetch_results(sql,'')
    if not rows:
        total_tax = 0.0
        submitWay = ""
    else:
        first = rows[0]
        if isinstance(first, dict):
          total_tax = float(first.get("법인세") or 0.0)
          submitWay = first.get("중간예납신고방법")


    new_data = {
      "work_YY":work_YY,
      "user_id":memuser.user_id,
      "strPassword":strPassword,        
      "midTax":"{:,.0f}".format(float(total_tax)),
      "submitWay":submitWay
    }
    tax_data.append(new_data) 
    tax_data = tax_data[0]       
  elif mail_class=='CorpFee':
    Subject = f"[{TXT_CorpName}] {work_YY}년 귀속 법인세 세무조정료 안내 - {memuser.biz_name}"
    tax_result = calculate_fees(mail_class,seq_no,work_YY)
    mail_class = "Corp"

    if tax_result:
      addition_dc_yj_style = "padding-left:26px;color:#054059;line-height: 28px;"
      addition_dc_yj_in1_style = "padding-right:12px;color:#000;text-align:right; "
      addition_dc_yj_in2_style = "padding-left:52px;color:#054059;line-height: 28px;"
      if tax_result["AdditionDC_YJ"] == 1:
          addition_dc_yj_style = "padding-left:26px;text-decoration:line-through;color:#ff0000;line-height: 28px;"
          addition_dc_yj_in1_style = "padding-right:12px;text-align:right;text-decoration:line-through;color:#ff0000;"
          addition_dc_yj_in2_style = "padding-left:52px;line-height: 28px;text-decoration:line-through;color:#ff0000;"

      addition_ddct_style = "padding-left:26px;color:#054059;line-height: 28px;"
      addition_ddct1_style = "padding-right:12px;color:#000;text-align:right; "
      addition_ddct2_style = "padding-left:52px;color:#054059;line-height: 28px;"            
      if tax_result["AdditionDC_Ddct"] == 1:
          addition_ddct_style = "padding-left:26px;text-decoration:line-through;color:#ff0000;line-height: 28px;"
          addition_ddct1_style = "padding-right:12px;text-align:right;text-decoration:line-through;color:#ff0000;"
          addition_ddct2_style = "padding-left:52px;line-height: 28px;text-decoration:line-through;color:#ff0000;"
          
      AdditionDC = SAddition = OAddition = FAddition = ""
      if tax_result["AdditionDC_Stnd"] not in ['','0'] and int(tax_result["AdditionDC_Stnd"])>0:
          AdditionDC_Amt = "{:,.0f}".format(  int(tax_result["stndfee"]) * int(tax_result["AdditionDC_Stnd"])/100  )
          AdditionDC = f"""
          <tr>	
            <td width='180px'  style='padding-left:26px;color:blue;line-height: 28px;'>🔻 기준보수의 {tax_result["AdditionDC_Stnd"]}% 할인</td>	
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
            <td width='140px'  style='padding-right:12px;color:blue;text-align:right;'> (-) {AdditionDC_Amt}</td>
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
          </tr>
          """    
      if tax_result["SAddition_Rsn"] not in ['','0'] and int(tax_result["SAddition_Amt"])>0:
          SAddition = f"""
          <tr>	
            <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {tax_result["SAddition_Rsn"]}</td>	
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
            <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(tax_result["SAddition_Amt"]))}</td>
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
          </tr>
          """
      if tax_result["OAddition_Rsn"] not in ['','0'] and int(tax_result["OAddition_Amt"])>0:
          OAddition = f"""
          <tr>	
            <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {tax_result["OAddition_Rsn"]}</td>	
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
            <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(tax_result["OAddition_Amt"]))}</td>
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
          </tr>
          """
      if tax_result["FAddition_Rsn"] not in ['','0'] and int(tax_result["FAddition_Amt"])>0:
          FAddition = f"""
          <tr>	
            <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {tax_result["FAddition_Rsn"]}</td>	
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
            <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(tax_result["FAddition_Amt"]))}</td>
            <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
          </tr>
          """
      new_data = {
        "user_id":memuser.user_id,
        "strPassword":strPassword,        
        "revenue": "{:,.0f}".format(float(tax_result["revenue"])), 
        "totalfee": "{:,.0f}".format(float(tax_result["totalfee"])),
        "stndfee":"{:,.0f}".format(float(tax_result["stndfee"])),
        "str_stndRange":tax_result["str_stndRange"],
        "str_stndfee":tax_result["str_stndfee"],
        "addingfee":"{:,.0f}".format(float(tax_result["addingfee"])),
        "wcYuptae":tax_result["wcYuptae"],
        "addingRate":tax_result["addingRate"],
        "deductfee":"{:,.0f}".format(float(tax_result["deductfee"])),
        "deductTax":"{:,.0f}".format(float(tax_result["deductTax"])),
        "addition_dc_yj_style":addition_dc_yj_style,
        "addition_dc_yj_in1_style":addition_dc_yj_in1_style,
        "addition_dc_yj_in2_style":addition_dc_yj_in2_style,
        "addition_ddct_style":addition_ddct_style,
        "addition_ddct1_style":addition_ddct1_style,
        "addition_ddct2_style":addition_ddct2_style,
        "str_deductRange":tax_result["str_deductRange"],
        "bookcnt":tax_result["bookcnt"],
        "bookfee":"{:,.0f}".format(float(tax_result["bookfee"])),
        "finalfee":"{:,.0f}".format(float(tax_result["finalfee"])),
        "vat":"{:,.0f}".format(float(tax_result["finalfee"])/10),
        "finalfeePlusVat":"{:,.0f}".format(float(tax_result["finalfee"])*1.1),
        "AdditionDC":AdditionDC,
        "SAddition":SAddition,
        "OAddition":OAddition,
        "FAddition":FAddition,
      }
      tax_data.append(new_data) 
      tax_data = tax_data[0]
  elif mail_class in ('VatIntro','VatResult','VatPrepay'):
    sendmail_class = "Vat"
    tax_quarter_mapping = {
        1: ("1기 예정",f"{work_YY}년 4월",f"{work_YY}년 1기","C17"),
        2: ("1기 확정",f"{work_YY}년 7월",f"{work_YY}년 1기","C07"),
        3: ("2기 예정",f"{work_YY}년 10월",f"{work_YY}년 2기","C17"),
        4: ("2기 확정",f"{int(work_YY)+1}년 1월",f"{work_YY}년 2기","C07")
    } 
    vat_Kigan,vat_MM, KSKG, KSUH = tax_quarter_mapping.get(int(work_qt), ("", "", ""))    
    Subject = f"[{TXT_CorpName}] {work_YY}년 {vat_Kigan} 부가가치세 신고 준비 안내 - {memuser.biz_name}"
    if  mail_class=="VatIntro":
      tax_data.append({"vat_MM":vat_MM})
    elif  mail_class=="VatPrepay":
      Subject = f"[{TXT_CorpName}] {work_YY}년 {vat_Kigan} 부가가치세 예정고지 안내 - {memuser.biz_name}"
      sql = """
        select YN_15 from tbl_vat  where seq_no =  %s and work_yy= %s and work_qt= %s      
      """
      rs = fetch_results(sql, (memuser.seq_no,work_YY,work_qt))
      if rs: 
        rs = rs[0]  # 첫 번째 딕셔너리 가져오기
      else:  
        rs = {}  # 데이터가 없을 경우 빈 딕셔너리로 설정
      if rs:
        TaxReturn = int(rs["YN_15"])
      new_data = {
          "vat_MM":int(work_MM)+1,
          "preTax":"{:,.0f}".format(TaxReturn)
        }
      tax_data.append(new_data) 
    else:
      Subject = f"[{TXT_CorpName}] {work_YY}년 {vat_Kigan} 부가가치세 신고 접수결과 및 납부 안내 - {memuser.biz_name}"
      sql = """
        select 산출세액, 차감합계세액, 예정신고미환급세액,예정고지세액,가산세액계,차감납부할세액
        ,(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액) as 매출세금계산서 
        ,(매출과세세금계산서발급세액 + 매출과세매입자발행세금계산서세액 + 예정누락매출세금계산서세액) as 매출세금계산서세액 
        ,(매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액) as 기타매출 
        ,(매출과세카드현금발행세액 + 매출과세기타세액 + 예정누락매출과세기타세액) as 기타매출세액 
        ,(매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액) as 영세율매출 
        ,(매입세금계산서수취일반금액 + 매입세금계산서수취고정자산금액 + 예정누락매입신고세금계산서금액 + 매입자발행세금계산서매입금액) as 매입세금계산서 
        ,(매입세금계산서수취일반세액 + 매입세금계산서수취고정자산세액 + 예정누락매입신고세금계산서세액 + 매입자발행세금계산서매입세액) as 매입세금계산서세액 
        ,그밖의공제매입명세합계금액 as 기타매입 
        ,그밖의공제매입명세합계세액 as 기타매입세액 
        ,공제받지못할매입합계금액 as 불공제 
        ,공제받지못할매입합계세액 as 불공제세액 
        ,경감공제합계세액 as 경감공제세액 
        ,면세사업합계수입금액 as 면세매출 
        ,계산서수취금액 as 면세매입 
        ,차감납부할세액 as 실제납부할세액 
        from 부가가치세전자신고3  where 사업자등록번호 =  %s and 과세기간= %s and 과세유형= %s      
      """
      rs = fetch_results(sql, (memuser.biz_no,KSKG,KSUH))
      if rs: 
        rs = rs[0]  # 첫 번째 딕셔너리 가져오기
      else:  
        rs = {}  # 데이터가 없을 경우 빈 딕셔너리로 설정
      if rs:
        TaxReturn = int(rs["실제납부할세액"])
        resultmsg2 = resultmsg1 = ""
        if TaxReturn < 0:
          resultmsg1 = " • 금번 부가가치세 신고는 환급할 세액으로 신고접수하였습니다. 부가가치세 환급액은 다음달 말일까지 등록된 사업용계좌로 입금됩니다."
          resultmsg2 = " • 다만, 체납한 국세가 있는 경우 해당 체납세액에서 먼저 충당하고 나머지가 있는 경우 환급됩니다."
        
        # "차감납부세액" 값이 0이면
        elif TaxReturn == 0:
          resultmsg1 = " • 금번 부가가치세 신고는 납부 또는 환급할 세액이 없습니다. "

        # "차감납부세액" 값이 0보다 크면
        else:
          resultmsg1 = " • 첨부된 부가가치세 납부서(200.pdf)를 지참하여 가까운 은행에서 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
          resultmsg2 = " • 홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 부가가치세를 선택하여 납부하시기 바랍니다. "  
        SaleTotal = int(rs["매출세금계산서"]) + int(rs["기타매출"]) + int(rs["영세율매출"]) + int(rs["면세매출"])
        SaleTotal_Vat = int(rs["매출세금계산서세액"]) + int(rs["기타매출세액"])
        CostTotal = int(rs["매입세금계산서"]) + int(rs["기타매입"]) + int(rs["면세매입"])
      
        new_data = {
          "next_YY":int(work_YY)+1,
          "user_id":memuser.user_id,
          "strPassword":strPassword,        
          "resultmsg1":resultmsg1,
          "resultmsg2":resultmsg2,
          "SaleTI": "{:,.0f}".format(float(rs["매출세금계산서"])), 
          "SaleTI_Vat": "{:,.0f}".format(float(rs["매출세금계산서세액"])),
          "SaleKita":"{:,.0f}".format(float(rs["기타매출"])),
          "SaleKita_Vat":"{:,.0f}".format(float(rs["기타매출세액"])),
          "SaleZero":"{:,.0f}".format(float(rs["영세율매출"])),
          "SaleNTI":"{:,.0f}".format(float(rs["면세매출"])),
          "SaleTotal":"{:,.0f}".format(SaleTotal),
          "SaleTotal_Vat":"{:,.0f}".format(SaleTotal_Vat),
          "CostTI":"{:,.0f}".format(float(rs["매입세금계산서"])),
          "CostTI_Vat":"{:,.0f}".format(float(rs["매입세금계산서세액"])),
          "CostKita":"{:,.0f}".format(float(rs["기타매입"])),
          "CostKita_Vat":"{:,.0f}".format(float(rs["기타매입세액"])),
          "CostNTI":"{:,.0f}".format(float(rs["면세매입"])),
          "Bulgong":"{:,.0f}".format(float(rs["불공제"])),
          "Bulgong_Vat":"{:,.0f}".format(float(rs["불공제세액"])),
          "SanchulTax":"{:,.0f}".format(float(rs["산출세액"])),
          "CostTotal":"{:,.0f}".format(CostTotal),
          "CostTotal_Vat":"{:,.0f}".format(float(rs["차감합계세액"])),
          "Deduct_Vat":"{:,.0f}".format(float(rs["경감공제세액"])),
          "PretaxM":"{:,.0f}".format(float(rs["예정신고미환급세액"])),
          "PretaxG":"{:,.0f}".format(float(rs["예정고지세액"])),
          "AdditionalTax":"{:,.0f}".format(float(rs["가산세액계"])),
          "TaxReturn":"{:,.0f}".format(float(rs["실제납부할세액"]))
        }
        tax_data.append(new_data) 
      tax_data = tax_data[0]
        
  html_content = render_to_string(targetUrl, {
      'biz_name': memuser.biz_name,
      'TXT_CorpName': TXT_CorpName,
      'TXT_OfficeAddress': TXT_OfficeAddress,
      'admin_name': memadmin['admin_name'],
      'admin_tel_no': memadmin['admin_tel_no'],
      'TXT_DutyCTA' : '김기현',
      'TXT_DutyCTAHP' : '010-9349-7120',
      'work_YY' : work_YY,
      'work_MM' : work_MM,
      'tax_data': tax_data,
  })
  Content = strip_tags(html_content)  # HTML 제거하여 일반 텍스트 변환
  email = EmailMultiAlternatives(
      subject=Subject,
      body=Content, 
      from_email=MailAddr,
      to=recipient_list  # 리스트로 변환된 수신자 이메일 전달
  )    

  email.attach_alternative(html_content, "text/html")  # HTML 버전 추가
  
  # 파일 첨부
  attached, skipped = [], []
  if isinstance(user_file_names, (str, Path)):
      names: Iterable[str] = [str(user_file_names)]
  elif isinstance(user_file_names, Iterable):
      names = [str(x) for x in user_file_names]
  else:
      raise TypeError("user_file_names must be str, Path, or iterable of those.")

  base = Path(user_path).resolve()

  for raw_name in names:
      name = raw_name.strip()
      if not name:
          skipped.append(f"(빈 문자열) -> 스킵")
          continue

      # OS 구분자 혼합 방지 + 정규화
      candidate = (base / name).resolve()

      # 디렉터리 traversal 방지: base 하위인지 확인
      try:
          candidate.relative_to(base)
      except ValueError:
          skipped.append(f"{candidate} -> base 디렉터리 밖 경로이므로 스킵")
          continue

      # 존재/파일 여부 확인
      if not candidate.exists():
          skipped.append(f"{candidate} -> 존재하지 않음")
          continue
      if not candidate.is_file():
          skipped.append(f"{candidate} -> 파일이 아니라 디렉터리/특수파일")
          continue

      # 읽기 권한 체크
      if not os.access(candidate, os.R_OK):
          skipped.append(f"{candidate} -> 읽기 권한 없음")
          continue

      # MIME 타입 추정 (없으면 octet-stream)
      mime, _ = mimetypes.guess_type(candidate.name)
      mime = mime or "application/octet-stream"

      # 실제 첨부
      try:
          with open(candidate, "rb") as f:
              # 첨부 표시명은 원래 파일명 그대로 사용 (필요 시 변경)
              email.attach(candidate.name, f.read(), mime)
          attached.append(str(candidate))
      except PermissionError:
          skipped.append(f"{candidate} -> PermissionError(권한 오류)")
      except OSError as e:
          skipped.append(f"{candidate} -> OS 오류: {e.__class__.__name__}: {e}")



  # 필수 데이터 검증
  if not (recipient_list and Subject and html_content):
    return JsonResponse({"error": "필수 데이터가 누락되었습니다."}, status=400)
  else:
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(MailAddr, 'zrncmbdvtrphknoa')
    # print('이메일 로그인 성공')    
    email.send()

  # 메일 전송 결과저장
  if memuser.email:
    if mail_class != "NotSave":
      TblMail.objects.create(
          seq_no=seq_no,
          admin_name=memadmin['admin_name'],
          biz_manager=memdeal.biz_manager,
          biz_name=memuser.biz_name,
          mail_subject=Subject,
          mail_content=html_content,
          mail_to=memuser.email,
          mail_from=MailAddr,
          mail_cc="",
          mail_date=now(),  # 현재 시간으로 설정
          file_cnt=len(user_file_names),
          file_path=user_path,
          file_name=user_file_names,
          mail_class=sendmail_class
      )
    return JsonResponse({"status": "success", "message": "Mail sent and DB save successfully"}, status=200)
  else:
    return JsonResponse({"status": "success", "message": "이메일이 없습니다."}, status=500)

# 모달에서 메일내용 미리보기 - 실제 발송내용과 다를 수 있다
from django.http import HttpRequest
@csrf_exempt
def getMailContent(request):

  if isinstance(request, dict):
      request_obj = HttpRequest()
      request_obj.method = request.get("method", "GET")  # 기본값 GET
      request = request_obj  # 원래 request를 변경

  if request.method == "POST":
    seq_no = request.POST.get("seq_no")  
    work_YY = int(request.POST.get("work_YY"))
    work_MM = request.POST.get("work_MM")
    if work_MM: work_MM = int(work_MM)
    work_QT = request.POST.get("work_QT")
    if work_QT: work_QT = int(work_QT)    
    flag = request.POST.get("flag") 
    print(flag)
    recordset = {}
    recordset_adminInfo = {}
    email_content = ""
    memuser = MemUser.objects.get(seq_no=seq_no)
    memdeal = MemDeal.objects.get(seq_no=seq_no)

    biz_no = memuser.biz_no
    admin = MemAdmin.objects.filter(
        admin_id=Subquery(
            MemDeal.objects.filter(seq_no=seq_no).values('biz_manager')[:1]
        )
    ).values('admin_name', 'admin_tel_no','admin_email').first()
    recordset_member = MemUser.objects.filter(seq_no=seq_no).values('biz_name','email','biz_no','ceo_name','hp_no','user_id').first()
    recordset_adminInfo = {
      'admin_name': admin['admin_name'],
      'admin_tel_no': admin['admin_tel_no'],
      'admin_email': admin['admin_email'],
      "TXT_CorpName"  : '세무법인대승',
      "TXT_DutyCTA"  : '김기현',
      "TXT_DutyCTAHP" : '010-9349-7120',
      "TXT_OfficeAddress"  : '서울특별시 강남구 강남대로84길 15, 206호(역삼동, 강남역효성해링턴타워더퍼스트)'
    }
    # 비밀번호 세팅
    half_length = len(memuser.user_pwd) // 2  # 앞 절반의 길이
    strPassword = memuser.user_pwd[:half_length] + '*' * (len(memuser.user_pwd) - half_length)
    if memuser.user_pwd=="1":
      strPassword = "최초 1로 설정되어 있으며 로그인시 임시비밀번호를 이메일로 전달받아 비밀번호를 수정하시기 바랍니다."


    if flag=='goji':
      sql = ("select taxMok,taxAmt,taxNapbuNum,taxOffice,taxDuedate from tbl_goji  "
                  "WHERE seq_no=%s AND work_yy=%s AND work_mm=%s ")
      recordset = fetch_results(sql, (seq_no, work_YY,work_MM))
      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 {work_MM}월 고지세액 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>
            <div class="eamil-body mt-5">
              <h6 class="fw-bold">안녕하세요 세무법인대승입니다.</h6>
              <p> 현재 아래 안내드리는 세목으로 미납세액이 있으니 인터넷 뱅킹의 공과금 납부 메뉴에서 해당 전자납부번호로 조회하여 납부기한까지 고지세액을 납부하여 주시기 바랍니다. </p>
              <p> 납부기한까지 미납할 경우 체납세액으로 분류되며 기간 경과분에 대한 가산세가 추가되어 1개월 경과된 납부서가 재발송됩니다.</p>
              <p class="mb-0">더 궁금한 사항은 업무담당자에게 문의바랍니다. 감사합니다.</p>
              <hr>
              <div class="email-attch">
                <div class="float-center">
                  <p  class="text-teritary"><i class="fe fe-alert-circle" ></i> 고지세액</p>
                </div>
                
                <table class='table table-bordered table-sm mb-0'>
                  <thead>
                    <tr>
                      <th style='text-align:center'>세목</th>
                      <th style='text-align:center'>고지세액</th>
                      <th style='text-align:center'>전자납부번호</th>
                      <th style='text-align:center'>관할<br>세무서</th>
                      <th style='text-align:center'>납부기한</th>
                    </tr>
                  </thead>
                  <tbody >"""
      for tax in recordset:
          email_content += f"""
                    <tr>
                      <td style='text-align:center;width:80px'>{tax["taxMok"]}</td>
                      <td style='text-align:right;width:15%'>{format(tax["taxAmt"], ',')} 원</td>
                      <td style='text-align:center;width:15%'>{tax["taxNapbuNum"]}</td>
                      <td style='text-align:center;width:30px'>{tax["taxOffice"]}</td>
                      <td style='text-align:center;width:45px;'>{tax["taxDuedate"]}</td>
                    </tr>
                """
      email_content += """
                  </tbody>
                </table>
              </div>
              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>고지 및 체납세액에 대하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div>
          </div>      
        </div>
        """
    elif flag=='CorpIntro':
      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 귀속 법인세 신고 및 납부 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>      
            <div class="email-body mt-5">
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p>{int(work_YY)+1}년 {work_MM}월은 법인세 신고납부의 달입니다. 기장보고서를 통해 전달드린 최종 당기순이익으로 {work_YY}년 귀속 법인세를 신고접수할 예정입니다.</p>
              
              <p>
                법인세는 기업의 1년간 순이익에 대해 부과되는 세금으로, 
                모든 법인은 <b>사업연도 종료일이 속하는 달의 말일부터 3개월 이내</b>에 신고 및 납부해야 합니다. 
                전달드리는 국세청 신고도움 안내문을 확인하시어 누락되는 세액감면공제가 없는지 확인하시기 바랍니다.
              </p>

              <h4 class="fw-bold mt-2">📌 국세청 신고도움 안내문 제공 자료</h4>
              <ul>
                <li>✅ 직전 3년간 동종 업종 평균 매출액 및 소득률</li>
                <li>✅ 업무와 무관한 신용카드 사용 내역</li>
                <li>✅ 법인세 신고 시 유의사항 등</li>
              </ul><br>
              <p>당사가 작성하는 최종 결산서 및 납부서는 <b>{work_MM}월 중순부터 제공</b>될 예정입니다.</p>

              <h4 class="fw-bold mt-2 text-danger">🔹 해외법인 보유 기업 필독 🔹</h4>
              <p>
                해외에 <b>지점 또는 자회사(자본 출자 포함)</b>를 보유한 기업은 반드시 해외현지법인명세서 제출하여야 합니다.
              </p>
              <p><b>🚨 당사로 제출 기한: {work_MM}월 15일까지</b></p>
              <p><b>🚨 미제출 시 현지법인 건당 1000만 원의 과태료가 부과됩니다.(국제조세조정에관한 법률 제87조) </b></p>

              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>법인세 신고와 관련하여 궁금한 점이나 해외현지법인명세서 제출에 필요한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div> 
          </div>
        </div>
      """
    elif flag=='CorpResult':
      txtfiscalMM = f"0{memdeal.fiscalmm}" if int(memdeal.fiscalmm) < 10 else str(memdeal.fiscalmm)
      yearEnd = f"{work_YY}{txtfiscalMM}"
      sql = ("select * from tbl_equityeval where 사업자번호=%s and 사업연도말=%s")
      rs = fetch_results(sql, (recordset_member["biz_no"],yearEnd))
      if rs: 
        rs = rs[0]  # 첫 번째 딕셔너리 가져오기
      else:  
        rs = {}  # 데이터가 없을 경우 빈 딕셔너리로 설정
      if rs:
        nongtax = str(rs["농특세"]).strip()  # Trim() -> strip(), 값이 없으면 빈 문자열 반환
        nongtax_bunnap = nongtax_afterChungdang = 0
        dueDate_Corptax = "03.31"; dueDate_wetax = "04.30"; dueDate_bunnap = "05.31"; 
        if txtfiscalMM=="06":
          dueDate_Corptax = "09.30"; dueDate_wetax = "10.31"; dueDate_bunnap = "11.30"; 
        elif txtfiscalMM=="03":
          dueDate_Corptax = "06.30"; dueDate_wetax = "07.31"; dueDate_bunnap = "08.31"; 
        if nongtax and nongtax != "0":  # 빈 문자열과 "0"이 아닌 경우만 실행
          nongtax_bunnap = float(nongtax[15:30])  # Mid(nongtax,16,15) -> 슬라이싱 [15:30]
          nongtax_afterChungdang = float(nongtax[-15:])  # Right(nongtax,15) -> 슬라이싱 [-15:]

        if nongtax_bunnap > 0:
          nts = "{:,.0f}".format(nongtax_bunnap//10*10)
          strBunnap = f"(농특세 : {nts} 별도)    <b>{format(int(rs['분납세액'])//10*10, ',')}</b>"
        else:
          strBunnap = f"<b>{format(int(rs['분납세액'])//10*10, ',')}</b>"
        if nongtax_afterChungdang > 0:
          ntsa = "{:,.0f}".format(nongtax_afterChungdang//10*10)
          strNongtax = f"(농특세 : {ntsa} 별도)    <b>{format(int(rs['차감납부세액'])//10*10, ',')}</b>"
        else:
          strNongtax = f"<b>{format(int(rs['차감납부세액'])//10*10, ',')}</b>"

        resultmsg2 = resultmsg1 = ""
        if int(rs["차감납부세액"]) < 0:
            if int(rs["과세표준_합계"]) > 0:
                resultmsg1 = "금번 법인세는 세액감면 공제를 통하여 납부할 세액 없이 신고 마쳤습니다. "
                resultmsg1 += "당기에 발생한 세액공제를 전액 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
            else:
                resultmsg1 = f"{work_YY}년에 발생된 결손금은 이월되어 향후 10년 내 발생하는 순이익에서 차감되며 납부할 법인세를 감소시킵니다. "
            if int(rs["산출세액_합계"])>0:
                resultmsg1 += "다만, 법인세할 지방소득세는 보내드린 지방세 납부서를 통하여 다음달 말일까지 납부하여 주시기 바랍니다. "
            resultmsg2 = "법인세 환급액은 다음달 말일까지 등록된 사업용계좌로 입금됩니다. "
        
        # "차감납부세액" 값이 0이면
        elif int(rs["차감납부세액"]) == 0:
            if int(rs["과세표준_합계"]) > 0:
                resultmsg1 = "금번 법인세는 세액감면 공제를 통하여 납부할 세액 없이 신고 마쳤습니다. "
                resultmsg2 = "당기에 발생한 세액공제를 전액 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
            else:
                resultmsg1 = f"{work_YY}년에 발생된 결손금은 이월되어 향후 10년 내 발생하는 순이익에서 차감되며 납부할 법인세를 감소시킵니다. "
                resultmsg2 = "당기에 발생한 세액공제를 공제받지 못한 경우 미공제금액은 10년간 이월되어 공제가 가능합니다. "
            if int(rs["산출세액_합계"])>0:
              resultmsg1 += "다만, 법인세할 지방소득세는 보내드린 지방세 납부서를 통하여 다음달 말일까지 납부하여 주시기 바랍니다. "

        # "차감납부세액" 값이 0보다 크면
        else:
            resultmsg1 = "법인세 및 조세특례제한법상 세액감면 공제사항을 모두 검토 반영하여 신고서를 작성하였습니다."
            resultmsg2 = "첨부된 법인세 및 지방세 납부서를 확인하여 가까운 은행에 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
            resultmsg2 += "홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 법인세를 선택하여 납부하시기 바랍니다. "

        email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 귀속 법인세 신고 접수결과 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>       
            <div class="email-body mt-5">   
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{work_YY}년 귀속 법인세 신고가 접수되었으며, 아래와 같이 신고 내역을 안내드립니다.</p>

              <h4 class="fw-bold mt-6">✅ 법인세 신고내역</h4>
              <table width="100%" style="border-collapse: collapse; border: 1px solid #ddd; font-family: Arial, sans-serif;">
                  <tr style="background-color: #f2f2f2;">
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">구분</th>
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">법인세</th>
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">토지 등 법인세</th>
                      <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">합계</th>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;">매출액</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;"  colspan=3>{format(int(rs["수입금액"]),',')}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;">과세표준</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format(int(rs["과세표준_법인세"]),',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format(int(rs["과세표준_토지"]),',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format(int(rs["과세표준_합계"]),',')}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;">세액 감면공제</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format(int(rs["최저한세적용대상"])+int(rs["최저한세적용제외"]),',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">0</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{format(int(rs["최저한세적용대상"])+int(rs["최저한세적용제외"]),',')}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;"><b>총 부담 법인세</b></td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["차감납부세액_법인세"])//10*10,',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["차감납부세액_토지"])//10*10,',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["차감납부세액_합계"])//10*10,',')}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;"><b>지 방 세</b> (납기 {int(work_YY)+1}.{dueDate_wetax})</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["산출세액_법인세"])/10//10*10,',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["산출세액_토지"])/10//10*10,',')}</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{"{:,.0f}".format(int(rs["산출세액_합계"])/10//10*10)}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;"><b>분납세액</b> (납기 {int(work_YY)+1}.{dueDate_bunnap})</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;"  colspan=3>{strBunnap}</td>
                  </tr>
                  <tr>
                      <td style="border: 1px solid #ddd; padding: 8px;"><b>차감납부세액</b> ({int(work_YY)+1}.{dueDate_Corptax})</td>
                      <td style="border: 1px solid #ddd; padding: 8px; text-align: right;"  colspan=3>{strNongtax}</td>
                  </tr>
              </table>

              <br>

              <h4 class="fw-bold mt-4 mb-2">✅ 법인세 신고내역 요약안내</h4>
              <p> • {resultmsg1}</p>
              <p> • {resultmsg2}</p>

              <h4 class="fw-bold mt-6 mb-2">📩 신고서 확인 및 문의 사항</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">접수된 법인세 신고서는 아래 세무법인 대승 인트라넷에서 확인 가능합니다.</p>
              <p> • 접속 주소: https://daeseungtax.co.kr</p>
              <p> • 아이디: {recordset_member["user_id"]}</p>
              <p> • 비밀번호 : {strPassword}</p>
              <br>
              <p  style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">법인세 신고와 관련하여 추가 문의 사항이 있으시면 언제든지 연락 주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div>
          </div>
        </div>
        """
    elif flag=='CorpFee':
      rs = calculate_fees(flag,seq_no,work_YY)
      if rs:            
        finalfee = rs["finalfee"]      
        sql_to_execute = f"UPDATE tbl_corporate2 SET YN_8='{finalfee}' WHERE seq_no={seq_no} AND work_YY={work_YY}"
        # print(sql_to_execute)
        with connection.cursor() as cursor:
          cursor.execute(sql_to_execute)


        addition_dc_yj_style = "padding-left:26px;color:#054059;line-height: 28px;"
        addition_dc_yj_in1_style = "padding-right:12px;color:#000;text-align:right; "
        addition_dc_yj_in2_style = "padding-left:52px;color:#054059;line-height: 28px;"
        if rs["AdditionDC_YJ"] == 1:
            addition_dc_yj_style = "padding-left:26px;text-decoration:line-through;color:#ff0000;line-height: 28px;"
            addition_dc_yj_in1_style = "padding-right:12px;text-align:right;text-decoration:line-through;color:#ff0000;"
            addition_dc_yj_in2_style = "padding-left:52px;line-height: 28px;text-decoration:line-through;color:#ff0000;"
        addition_ddct_style = "padding-left:26px;color:#054059;line-height: 28px;"
        addition_ddct1_style = "padding-right:12px;color:#000;text-align:right; "
        addition_ddct2_style = "padding-left:52px;color:#054059;line-height: 28px;"            
        if rs["AdditionDC_Ddct"] == 1:
            addition_ddct_style = "padding-left:26px;text-decoration:line-through;color:#ff0000;line-height: 28px;"
            addition_ddct1_style = "padding-right:12px;text-align:right;text-decoration:line-through;color:#ff0000;"
            addition_ddct2_style = "padding-left:52px;line-height: 28px;text-decoration:line-through;color:#ff0000;"
        AdditionDC = SAddition = OAddition = FAddition = ""
        if rs["AdditionDC_Stnd"] not in ['','0'] and int(rs["AdditionDC_Stnd"])>0:
           AdditionDC_Amt = "{:,.0f}".format(  int(rs["stndfee"]) * int(rs["AdditionDC_Stnd"])/100  )
           AdditionDC = f"""
            <tr>	
              <td width='180px'  style='padding-left:26px;color:blue;line-height: 28px;'>🔻 기준보수의 {rs["AdditionDC_Stnd"]}% 할인</td>	
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
              <td width='140px'  style='padding-right:12px;color:blue;text-align:right;'> (-) {AdditionDC_Amt}</td>
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
            </tr>
           """           
        if rs["SAddition_Rsn"] not in ['','0'] and int(rs["SAddition_Amt"])>0:
           SAddition = f"""
            <tr>	
              <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {rs["SAddition_Rsn"]}</td>	
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
              <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(rs["SAddition_Amt"]))}</td>
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
            </tr>
           """
        if rs["OAddition_Rsn"] not in ['','0'] and int(rs["OAddition_Amt"])>0:
           OAddition = f"""
            <tr>	
              <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {rs["OAddition_Rsn"]}</td>	
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
              <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(rs["OAddition_Amt"]))}</td>
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
            </tr>
           """
        if rs["FAddition_Rsn"] not in ['','0'] and int(rs["FAddition_Amt"])>0:
           FAddition = f"""
            <tr>	
              <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;'>🔺 {rs["FAddition_Rsn"]}</td>	
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
              <td width='140px'  style='padding-right:12px;color:#000;text-align:right;'> {"{:,.0f}".format(int(rs["FAddition_Amt"]))}</td>
              <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
            </tr>
           """
        email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 귀속 법인세 신고 세무조정료 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>       
            <div class="email-body mt-5">           
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{work_YY}년 귀속 법인세 신고에 대한 결산보수 내역을 아래와 같이 계산하였습니다.</p>

              <h4 class="fw-bold mt-6">✅ 세무조정료 계산내역</h4>

              <table style='border: 1px solid #dadada; font-family: Arial, sans-serif;margin-top:10px;margin-bottom:10px;width: 600px' >
                <tr>	
                  <td width='180px' style='padding:13px;color:#054059;line-height: 28px;'><b>1. 수수료 적용 기준금액</td>
                  <td width='420px' style='text-align:right;color:#000;padding-right:12px;border-bottom-color: #dadada; ' colspan=3><b> {"{:,.0f}".format(int(rs["revenue"]))}</td>
                </tr>
                <tr>	
                  <td width='180px' style='padding:13px;color:#054059;line-height: 28px;'><b>2. 규정 수수료</td>	
                  <td width='140px' style='padding-right:12px; text-align:right;color:#000;' colspan=3><b>{"{:,.0f}".format(int(rs["totalfee"]))}</td>
                </tr>
                <tr>	
                  <td width='180px' style='padding-left:26px;color:#054059;line-height: 28px;'>(1) 구간별 기준보수</td>	
                  <td width='140px' style='color:#000;padding-right:12px;text-align:right;'></td>
                  <td width='140px' align=right style='color:#000;padding-right:12px; '> {"{:,.0f}".format(int(rs["stndfee"]))}</td>
                  <td width='140px' align=right style='color:#000;padding-right:12px; '></td>
                </tr>
                <tr>	
                  <td width='180px'  style='padding-left:52px;color:#054059;line-height: 28px;' colspan=4>* {rs["str_stndRange"]}</td>
                </tr>
                <tr>
                  <td width='180px'  style='padding-left:52px;color:#054059;line-height: 28px;' colspan=4>* {rs["str_stndfee"]}</td>
                </tr>
                <tr>	
                  <td width='180px' style='{addition_dc_yj_style}'>(2) 기준보수 가산액</td>	
                  <td width='140px' style='color:#000;padding-right:12px;text-align:right;'></td>
                  <td width='140px' style='{addition_dc_yj_in1_style}'> {"{:,.0f}".format(int(rs["addingfee"]))}</td>
                  <td width='140px' style='color:#000;padding-right:12px;text-align:right; '></td>
                </tr>
                <tr>
                  <td width='180px'  style='{addition_dc_yj_in2_style}' colspan=4>* {rs["wcYuptae"]} 가산율 {"{:,.0f}".format(float(rs["addingRate"])*100)} %</td>
                </tr>
                <tr>	
                  <td width='180px'  style='{addition_ddct_style}'>(3) 세액 감면공제 가산액</td>	
                  <td width='140px'  style='color:#000;padding-right:12px;text-align:right;'></td>
                  <td width='140px'  style='{addition_ddct1_style}'> {"{:,.0f}".format(int(rs["deductfee"]))}</td>
                  <td width='140px'  style='color:#000;padding-right:12px;text-align:right; '></td>
                </tr>
                <tr>
                  <td width='180px'  style='{addition_ddct2_style}' colspan=4>* 감면세액 : {"{:,.0f}".format(int(rs["deductTax"]))} 원( {rs["str_deductRange"]} 적용)</td>
                </tr>
                <tr>	
                  <td width='180px'  style='padding-left:26px;color:#054059;line-height: 28px;' colspan=2>(4) 조정계산서 인쇄/제본비 ( {rs["bookcnt"]} 권)</td>	
                  <td width='140px' align=right style='color:#000;padding-right:12px; '>{"{:,.0f}".format(int(rs["bookfee"]))}</td>
                  <td width='140px' align=right style='color:#000;padding-right:12px; '></td>
                </tr>
                {AdditionDC}
                {SAddition}
                {OAddition}
                {FAddition}
                <tr>
                  <td width='180px'  style='padding-left:13px;color:#054059;line-height: 28px;'><b>3. 백단위 절사 후 공급가액</b></td>	
                  <td id="finalFee" style='color:#000;padding-right:12px;text-align:right;' colspan=3>{"{:,.0f}".format(int(rs["finalfee"]))}</td>
                </tr>
                <tr>
                  <td width='180px'  style='padding-left:13px;color:#054059;line-height: 28px;'><b>4. 부 가 세 10 %</b></td>	
                  <td style='color:#000;padding-right:12px;text-align:right;' colspan=3> {"{:,.0f}".format(int(rs["finalfee"])*.1)}</td>
                </tr>
                <tr >	
                  <td width='180px'  style='padding-left:13px;color:#054059;line-height: 28px;'><b>5. 공급대가</b></td>	
                  <td width='420px' align=right style='color:#000;padding-right:12px;' colspan=3><b> {"{:,.0f}".format(int(rs["finalfee"])*1.1)} </td>
                </tr>
              </table>
                          
              <br>

              <h4 class="fw-bold mt-4 mb-2">✅ 결재 안내</h4>
              <p> • <font style=color:#1271B5;font-weight:bold;>하나은행(세무법인대승) 581-910019-69904</font>로 금주 중 송금주시기 바랍니다.</p>
              <p> • 송금이 불편하신 경우 <font style=color:#1271B5;font-weight:bold;>[CMS 자동이체]</font> 요청 회신메일 부탁드립니다. </p>
              <p> • 이달 말까지 입금이 확인되지 않으면 등록해 주신 자동이체 계좌를 통해 CMS 출금이 진행될 예정입니다.</p>

              <h4 class="fw-bold mt-6 mb-2">📩 신고서 확인 및 문의 사항</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">접수된 법인세 신고서는 아래 세무법인 대승 인트라넷에서 확인 가능합니다.</p>
              <p> • 접속 주소: https://daeseungtax.co.kr</p>
              <p> • 아이디: {recordset_member["user_id"]}</p>
              <p> • 비밀번호 : {strPassword}</p>
              <p  style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">법인세 신고와 관련하여 추가 문의 사항이 있으시면 언제든지 연락 주시기 바랍니다.</p>
              <br>
              <p class="fw-bold">감사합니다.</p>
            </div>
          </div>
        </div>
        """         
    elif flag=='CorpJungkanIntro':
      sql = f"select ISNULL(총부담세액_합계, 0) total_tax from tbl_equityeval WHERE 사업자번호='{biz_no}' AND left(사업연도말,4)='{work_YY-1}'"
      # print(sql)
      rows = fetch_results(sql,'')
      if not rows:
          total_tax = 0.0
      else:
          first = rows[0]
          if isinstance(first, dict):
              total_tax = float(first.get("total_tax") or 0.0)
          elif isinstance(first, (list, tuple)):
              total_tax = float(first[0] or 0.0)
          else:
              total_tax = float(first or 0.0)

      preTax =total_tax/2
      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 귀속 법인세 중간예납 신고 및 납부 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>      
            <div class="email-body mt-5">
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p>{int(work_YY)}년 {work_MM}월은 법인세 중간예납 신고납부의 달입니다. </p><br>
              
              <h4 class="fw-bold mt-2">📅 중간예납 기간 및 계산</h4>
              <ul>
                <li><b>• 신고대상 : </b>12월 결산 법인</li>
                <li><b>• 계산방법 : </b>직전 사업연도 법인세를 기준으로 절반을 납부. 상반기 영업실적을 중간결산하여 선택납부 가능</li>
              </ul>            
              <p><b>🚨 직전 사업연도에 법인세 산출세액이 없거나 확정되지 않은 경우 반드시 상반기 실적을 중간결산하여 납부해야 합니다.</p><br>

              <h4 class="fw-bold mt-2">📌 귀 법인의 예상 세액</h4>
              <ul>
                <li>• 예상 법인세 중간예납세액 : <b><span style='color:blue;'>{preTax:,.0f} 원</span></b></li>
                <li><b>• 상반기 가결산을 통해 예상납부세액 보다 감소될 수 있음</b></li>
                <li><b>• 납부서는 법인세 중간예납 신고접수시 전달예정</b></li>
              </ul><br>

              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>법인세 중간예납 신고와 관련하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div> 
          </div>
        </div>
      """       
    elif flag=='CorpJungkanResult':
      sql = f"select 중간예납신고방법,법인세  from tbl_equityeval_MID WHERE 사업자번호='{memuser.biz_no}' AND left(사업연도말,4)='{work_YY}'"
      # print(sql)
      rows = fetch_results(sql,'')
      if not rows:
          total_tax = 0.0
          submitWay = ""
      else:
          first = rows[0]
          if isinstance(first, dict):
            total_tax = float(first.get("법인세") or 0.0)
            submitWay = first.get("중간예납신고방법")
      if submitWay=="1":#직전년도 기준
        txt_submitWay = "직전 사업연도 법인세를 기준으로 절반을 납부합니다. 상반기 중간결산 방식보다 유리합니다."
      else:
        if total_tax == 0:
          txt_submitWay = "상반기 중간결산하여 납부할 세액이 없도록 신고하였습니다."
        else:            
          txt_submitWay = "상반기 중간결산하여 납부세액 계산하였습니다. 직전 사업연도 법인세를 기준보다 유리합니다."         
      midTax = format(total_tax, ',')
      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 귀속 법인세 중간예납 신고결과 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>      
            <div class="email-body mt-5">
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p>{int(work_YY)}년 법인세 중간예납 신고결과를 안내드립니다. </p><br>
              
              <h4 class="fw-bold mt-2">📅 중간예납 기간 및 계산</h4>
              <ul>
                <li><b>• 신고방법 : </b>12월 결산 법인</li>
                <li><b>• 계산방법 : </b>{txt_submitWay}</li>
              </ul>            
              <br>
              <h4 class="fw-bold mt-2">📌 귀 법인의 중간예납 세액</h4>
              <ul>
                <li>• 법인세 중간예납세액 : <b><span style='color:blue;'>{midTax} 원</span></b></li>
                <li><b>• 납부기한 : </b></li>
                <li><b>• 납부방법 : </b></li>
              </ul><br>

              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>법인세 중간예납 신고와 관련하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div> 
          </div>
        </div>
      """       
    elif flag=='VatIntro':

      # 기수별 신고 정보 설정
      tax_quarter_mapping = {
          1: ("1기 예정",f"{work_YY}년 4월"),
          2: ("1기 확정",f"{work_YY}년 7월"),
          3: ("2기 예정",f"{work_YY}년 10월"),
          4: ("2기 확정",f"{int(work_YY)+1}년 1월")
      }
      vat_Kigan,vat_MM = tax_quarter_mapping.get(int(work_QT), ("", "", ""))

      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 {vat_Kigan} 부가가치세 신고 준비 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>      
            <div class="email-body mt-5">
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p>{vat_MM}은 부가가치세 신고납부의 달입니다. </p>
              
              <p>
                부가가치세는 세금계산서, 계산서, 신용카드매출전표, 현금영수증 등 적격 증빙에 의해 발생한 매출 부가가치세에서 매입 부가가치세를 차감하여 계산됩니다.
                또한 인건비나 적격 증빙 외의 비용은 부가가치세에서 공제되지 않는 점 유의하시기 바랍니다.
              </p>


              <h4 class="fw-bold mt-2 text-danger">🔹 기장자료 회신요청 🔹</h4>
              <p>
                (1) 전자 세금계산서 이외에도 <b>종이로 발행한 매출 및 매입 세금계산서</b><br>
                (2) 각 사이트 관리자 페이지에서 확인할 수 있는 <b>온라인 판매 대행사의 매출 내역</b><br>
                (3) <b>수출이 있는 경우</b> 인보이스, 수출신고필증, 내국신용장 또는 외화매입증명서<br>
                <b>(🚨 누락시 영세율 매출누락관련 가산세 0.5% 발생)</b><br>
                (4) <b>차량 매입이 있는 경우</b> 자동차 등록증(리스의 경우 계약서 및 상환 스케줄표)<br>
                (5) <b>부동산 등 고정자산 거래가 있는 경우</b> 해당 계약서 및 이체 확인서<br>
                (6) <b>법인인 경우</b> 통장 엑셀 자료 (이전에 보내주셨던 내역에 이어 최신 내역까지)<br>
                (7) 기타 간이영수증 또는 계약서                
              </p>
              <p><b>🚨 당사로 제출 기한: {vat_MM} 15일까지</b></p>
             

              <h4 class="fw-bold mt-2">📌 국세청 신고도움 안내문 제공 첨부자료 참고</h4>
              <ul>
                <li>✅ 직전 4과세기간 부가가치세 신고상황</li>
                <li>✅ 부가가치세 신고 시 확인 및 유의사항</li>
                <li>✅ 부가가치세 성실신고 체크리스트 등</li>
              </ul><br>
    
              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>부가가치세 신고와 관련하여 궁금한 점이나 전달 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div> 
          </div>
        </div>
      """
    elif flag=="VatPrepay":

      # 기수별 신고 정보 설정
      tax_quarter_mapping = {
          1: ("1기 예정",f"{work_YY}년 4월"),
          2: ("1기 확정",f"{work_YY}년 7월"),
          3: ("2기 예정",f"{work_YY}년 10월"),
          4: ("2기 확정",f"{int(work_YY)+1}년 1월")
      }
      vat_Kigan,vat_MM = tax_quarter_mapping.get(int(work_QT), ("", "", ""))

      sql = f"select YN_15  from tbl_vat WHERE seq_no='{memuser.seq_no}' AND work_yy='{work_YY}' and work_qt='{work_QT}'"
      # print(sql)
      rows = fetch_results(sql,'')
      if not rows:
          total_tax = 0
      else:
          first = rows[0]
          if isinstance(first, dict):
            total_tax = int(first.get("YN_15") or 0)
      
      midTax = format(total_tax, ',')

      email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 {vat_Kigan} 부가가치세 예정고지 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>      
            <div class="email-body mt-5">
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p>{vat_MM}은 부가가치세 예정고지분 납부의 달입니다. </p>
              
              <p>
                부가가치세 예정고지는 직전 6개월 납부세액의 절반을 미리 납부하는 것으로 확정신고시 기납부세액으로 차감됩니다.
              </p>

              
              <h4 class="fw-bold mt-2">📅 예정고지세액 금액 및 기한</h4>
              <ul>
                <li>• 고지금액 : <b><span style='color:blue;'>{midTax} 원</span></b></li>
                <li>• 납부기한 : <b>금월 25일</b>(공휴일인 경우 익일)</li>
                <li>• 납부방법 : 첨부드린 납부서상의 가상계좌로 계좌이체</li>
              </ul>            
              <br>            
    
              <h4 class="fw-bold mt-4">📩 문의 사항</h4>
              <p>부가가치세 신고와 관련하여 궁금한 점이나 전달 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div> 
          </div>
        </div>
      """       
    elif flag=='VatResult':
      # 기수별 신고 정보 설정
      tax_quarter_mapping = {
          1: ("1기 예정",f"{work_YY}년 4월",f"{work_YY}년 1기","C17"),
          2: ("1기 확정",f"{work_YY}년 7월",f"{work_YY}년 1기","C07"),
          3: ("2기 예정",f"{work_YY}년 10월",f"{work_YY}년 2기","C17"),
          4: ("2기 확정",f"{int(work_YY)+1}년 1월",f"{work_YY}년 2기","C07")
      }   
      vat_Kigan,vat_MM, KSKG, KSUH = tax_quarter_mapping.get(int(work_QT), ("", "", ""))         
      sql = """
        select 산출세액, 차감합계세액, 예정신고미환급세액,예정고지세액,가산세액계,차감납부할세액
        ,(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액) as 매출세금계산서 
        ,(매출과세세금계산서발급세액 + 매출과세매입자발행세금계산서세액 + 예정누락매출세금계산서세액) as 매출세금계산서세액 
        ,(매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액) as 기타매출 
        ,(매출과세카드현금발행세액 + 매출과세기타세액 + 예정누락매출과세기타세액) as 기타매출세액 
        ,(매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액) as 영세율매출 
        ,(매입세금계산서수취일반금액 + 매입세금계산서수취고정자산금액 + 예정누락매입신고세금계산서금액 + 매입자발행세금계산서매입금액) as 매입세금계산서 
        ,(매입세금계산서수취일반세액 + 매입세금계산서수취고정자산세액 + 예정누락매입신고세금계산서세액 + 매입자발행세금계산서매입세액) as 매입세금계산서세액 
        ,그밖의공제매입명세합계금액 as 기타매입 
        ,그밖의공제매입명세합계세액 as 기타매입세액 
        ,공제받지못할매입합계금액 as 불공제 
        ,공제받지못할매입합계세액 as 불공제세액 
        ,경감공제합계세액 as 경감공제세액 
        ,면세사업합계수입금액 as 면세매출 
        ,계산서수취금액 as 면세매입 
        ,차감납부할세액 as 실제납부할세액 
        from 부가가치세전자신고3  where 사업자등록번호 =  %s and 과세기간= %s and 과세유형= %s      
      """
      rs = fetch_results(sql, (recordset_member["biz_no"],KSKG,KSUH))
      if rs: 
        rs = rs[0]  # 첫 번째 딕셔너리 가져오기
      else:  
        rs = {}  # 데이터가 없을 경우 빈 딕셔너리로 설정
      if rs:
        TaxReturn = int(rs["차감납부할세액"])
        resultmsg2 = resultmsg1 = ""
        if TaxReturn < 0:
          resultmsg1 = " • 금번 부가가치세 신고는 환급할 세액으로 신고접수하였습니다. 부가가치세 환급액은 다음달 말일까지 등록된 사업용계좌로 입금됩니다."
          resultmsg2 = " • 다만, 체납한 국세가 있는 경우 해당 체납세액에서 먼저 충당하고 나머지가 있는 경우 환급됩니다."
        
        # "차감납부세액" 값이 0이면
        elif TaxReturn == 0:
          resultmsg1 = " • 금번 부가가치세 신고는 납부 또는 환급할 세액이 없습니다. "

        # "차감납부세액" 값이 0보다 크면
        else:
          resultmsg1 = " • 첨부된 부가가치세 납부서(200.pdf)를 지참하여 가까운 은행에서 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
          resultmsg2 = " • 홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 부가가치세를 선택하여 납부하시기 바랍니다. "   
               
        email_content = f"""
        <div class="card">
          <div class="card-header border-bottom">
            <h4 class="card-title fw-bold" id = "Subject">[세무법인대승] {work_YY}년 {vat_Kigan} 부가가치세 신고 접수결과 안내 - {memuser.biz_name}</h4>
          </div>
          <div class="card-body">
            <div class="email-media">
              <div class="mt-0 d-sm-flex">
                <img class="me-2 rounded-circle avatar-xl" src="https://daeseungtax.co.kr/static/assets/images/faces/{admin['admin_name']}.png" alt="avatar">
                <div class="media-body">
                  <div class="media-title fw-bold mt-0">업무담당자 {admin['admin_name']} <span class="tx-13 fw-semibold">(<i class="fe fe-phone-call"></i> {admin['admin_tel_no']} )</span></div>
                  <p class="mb-0"> <span class="text-muted">책임세무사 {recordset_adminInfo['TXT_DutyCTA']} (<i class="fe fe-smartphone"></i> {recordset_adminInfo['TXT_DutyCTAHP']} )</span> </p>
                  <p class="mb-0"> <span class="text-muted">{recordset_adminInfo['TXT_OfficeAddress']} </span> </p>
                </div>
              </div>
            </div>       
            <div class="email-body mt-5">   
              <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{work_YY}년 {vat_Kigan} 부가가치세 신고가 접수되었으며, 아래와 같이 신고 내역을 안내드립니다.</p>

              <h4 class="fw-bold mt-6">✅ 부가가치세세 신고내역</h4>
              <table width="580px" style="border-collapse: collapse; border: 1px solid #ddd; font-family: Arial, sans-serif;">
              <tr style="background-color: #f2f2f2;">
                  <th width="165px" style="border: 1px solid #ddd; padding: 8px; text-align: center;" colspan=2><b>구&nbsp;&nbsp;&nbsp;&nbsp;분</th>
                  <th width="100px" style="border: 1px solid #ddd; padding: 8px; text-align: center;"><b>공급가액</th>
                  <th width="100px" style="border: 1px solid #ddd; padding: 8px; text-align: center;"><b>세&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;액</th>
              </tr>
              <tr>
                  <td width="25px;" style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3; padding-left:12px;" rowspan=5><b>매<br>출<br>세<br>액</td>
                  <td width="140px" align=left style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3;padding-left:13px;padding-right:6px;">매출세금계산서</td>
                  <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["매출세금계산서"]),',')}</td>
                  <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["매출세금계산서세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3; padding-left:13px;padding-right:6px;">신용카드 현금영수증 기타</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["기타매출"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["기타매출세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3; padding-left:13px;padding-right:6px;">영세율 매출</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["영세율매출"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">0</td>
              </tr>
              <tr>	
                <td width="125px" align=left style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3; padding-left:13px;padding-right:6px;">면세 매출</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">{format(int(rs["면세매출"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;">0</td>
              </tr>           
              <tr>
                <td width="125px" align=center style="border: 1px solid #ddd; color:#ff0000;background:#f3f3f3;"><b>합&nbsp;&nbsp;&nbsp;&nbsp;계</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;"><b>{format(int(rs["매출세금계산서"])+int(rs["기타매출"])+int(rs["영세율매출"])+int(rs["면세매출"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#ff0000;padding-right:6px;"><b>{format(int(rs["산출세액"]),',')}</td>
              </tr>           
              <tr>
                <td width="25px;" style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3; padding-left:12px;" rowspan=5><b>매<br>입<br>세<br>액</td>
                <td width="140px" align=left style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3;padding-left:13px;padding-right:6px;">매입세금계산서</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["매입세금계산서"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["매입세금계산서세액"]),',')}</td>
              </tr>  
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3; padding-left:13px;padding-right:6px;">신용카드 현금영수증</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["기타매입"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["기타매입세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3; padding-left:13px;padding-right:6px;">불공제 매입세액</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["불공제"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["불공제세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3; padding-left:13px;padding-right:6px;">면세 매입</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">{format(int(rs["면세매입"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;">0</td>
              </tr>
              <tr>
                <td width="125px" align=center style="border: 1px solid #ddd; color:#3366ff;background:#f3f3f3;"><b>합&nbsp;&nbsp;&nbsp;&nbsp;계</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;"><b>{format(int(rs["매입세금계산서"])+int(rs["기타매입"])+int(rs["면세매입"]),',')}</td>
                <td width="100px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;"><b>{format(int(rs["차감합계세액"]),',')}</td>
              </tr>      
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#000;background:#f3f3f3; padding-left:13px;padding-right:6px;" colspan=2>경감 공제세액</td>
                <td width="200px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;" colspan=2>{format(int(rs["경감공제세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#000;background:#f3f3f3; padding-left:13px;padding-right:6px;" colspan=2>예정 고지세액</td>
                <td width="200px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;" colspan=2>{format(int(rs["예정고지세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#000;background:#f3f3f3; padding-left:13px;padding-right:6px;" colspan=2>예정 미환급세액</td>
                <td width="200px" align=right style="border: 1px solid #ddd; color:#3366ff; padding-right:6px;" colspan=2>{format(int(rs["예정신고미환급세액"]),',')}</td>
              </tr>
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#000;background:#f3f3f3; padding-left:13px;padding-right:6px;" colspan=2>가&nbsp;&nbsp;산&nbsp;&nbsp;세</td>
                <td width="200px" align=right style="border: 1px solid #ddd; color:#ff0000; padding-right:6px;" colspan=2>{format(int(rs["가산세액계"]),',')}</td>
              </tr>    
              <tr>
                <td width="125px" align=left style="border: 1px solid #ddd; color:#000;background:#f3f3f3; padding-left:13px;padding-right:6px;" colspan=2><b>납부세액(환급세액)</td>
                <td width="200px" align=right style="border: 1px solid #ddd; padding-right:6px;" colspan=2><b>{format(TaxReturn,',')}</td>
              </tr>                                 
              </table>

              <br>

              <h4 class="fw-bold mt-4 mb-2">✅ 부가가치세 신고내역 요약안내</h4>
              <p>{resultmsg1}</p>
              <p>{resultmsg2}</p>

              <h4 class="fw-bold mt-6 mb-2">📩 신고서 확인 및 문의 사항</h4>
              <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">접수된 부가가치세 신고서는 아래 세무법인 대승 인트라넷에서 확인 가능합니다.</p>
              <p> • 접속 주소: https://daeseungtax.co.kr</p>
              <p> • 아이디: {recordset_member["user_id"]}</p>
              <p> • 비밀번호 : {strPassword}</p>
              <br>
              <p  style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">부가가치세 신고와 관련하여 추가 문의 사항이 있으시면 언제든지 연락 주시기 바랍니다.</p>
              <p class="fw-bold">감사합니다.</p>
            </div>
          </div>
        </div>
        """       
    elif flag=='pay':
      # "YYYY년M월" 형식을 "YYYYMM" 형식으로 변환
      yearAndMonth = f"{work_YY}{work_MM}"
      if len(str(work_MM)) == 1:
        yearAndMonth = f"{work_YY}0{work_MM}"

      folder_path = os.path.join('static/cert_DS/', memuser.biz_name, str(work_YY), "인건비")
      if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # 폴더 내 파일 목록 가져오기
        monthly_files = [file for file in files if file.startswith(f"{work_MM}월")]  # "12월"로 시작하는 파일 필터링
        if monthly_files:
          strPay = resultmsg2 = resultmsg1 = ""
          has_Napbuseo = any("납부서" in file for file in monthly_files)
          sql = ("SELECT * FROM 원천세전자신고 WHERE 사업자등록번호=%s and 과세연월=%s ")
          rs = fetch_results(sql, (recordset_member["biz_no"],yearAndMonth))
          if rs: 
            rs = rs[0]  # 첫 번째 딕셔너리 가져오기
            arrPay = []
            if int(rs["A01"]) > 0:          arrPay.append("근로")
            if int(rs["a03"]) > 0:          arrPay.append("일용")
            if int(rs["A20"]) > 0:          arrPay.append("퇴직")
            if int(rs["A30"]) > 0:          arrPay.append("사업")
            if int(rs["A40"]) > 0:          arrPay.append("기타")
            if int(rs["A50"]) > 0:          arrPay.append("이자")
            if int(rs["A60"]) > 0:          arrPay.append("배당")
            #if int(rs["A80"]) > 0:          arrPay.append("법인원천")
            strPay = ", ".join(arrPay) if arrPay else ""
            
            if has_Napbuseo:
              resultmsg1 = "첨부된 원천세 및 지방세 납부서를 확인하여 가까운 은행에 납부하시거나 납부서에 표시된 가상계좌로 송금하시면 됩니다. "
              resultmsg1 += "홈택스에서는 납부하시는 경우 로그인 하셔서 [신고/납부 > 세금납부 > 국세납부 > 납부할세액 조회납부]에서 원천세를 선택하여 납부하시기 바랍니다."

            # 신고됐는데 납부서가 없는 경우
            else:
              if memdeal.goyoung_banki=="Y":
                resultmsg1 = f"[{memuser.biz_name}]의 경우 반기신고 대상자이므로 원천징수한 소득세등은 반기의 다음달 10일까지 납부서를 발송드릴 예정입니다. "
              else:
                resultmsg1 = "당월은 원천세 및 지방세 납부가 없습니다. 급여대장상 납부금액과 납부서상 납부할 금액이 차이나는 경우 연말정산 환급금과 당월분 납부금액이 상계된 것입니다."
            if int(rs["A01"]) > 0: 
              if int(work_MM)==2:
                resultmsg2 = f"{work_MM}월은 근로자 연말정산 환급(징수)분이 반영되어 차인지급액 변동이 있으니 급여대장상의 차인지급액을 다시 한번 확인하여 주시기 바랍니다."
              elif int(work_MM)==7:
                resultmsg2 = f"{work_MM}월은 국민연금 변경(기준소득월액 결정)분이 반영되어 차인지급액 변동이 있으니 급여대장상의 차인지급액을 다시 한번 확인하여 주시기 바랍니다."
                              
          #신고안됐지만 
          else:  
            rs = {}  # 데이터가 없을 경우 빈 딕셔너리로 설정
            strPay = "근로소득"
            if memdeal.goyoung_banki=="Y":
              resultmsg1 = f"[{memuser.biz_name}]의 경우 반기신고 대상자이므로 원천징수한 소득세등은 반기의 다음달 10일까지 납부서를 발송드릴 예정입니다. "
            else:
              resultmsg1 = "당월은 원천세 및 지방세 납부가 없습니다. 급여대장상 납부금액과 납부서상 납부할 금액이 차이나는 경우 연말정산 환급금과 당월분 납부금액이 상계된 것입니다."

          email_content = f"""
            <h4 class="fw-bold">안녕하세요, 세무법인 대승입니다.</h4>
            <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{work_MM}월 인건비 등 명세서({strPay})를 보내드리니 해당 <b>지급명세서상의 차인지급액</b>을 확인하여 각 소득 귀속자에게 이체하시기 바랍니다. </p>

            
            <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{resultmsg1}</p>
            <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">{resultmsg2}</p>

            <h4 class="fw-bold mt-6 mb-2">📩 지급명세서 확인 및 문의 사항</h4>
            <p style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">현재까지 신고된 원천징수이행상황신고서 등은 아래 세무법인 대승 인트라넷에서 확인 가능합니다.</p>
            <p> • 접속 주소: https://daeseungtax.co.kr</p>
            <p> • 아이디: {recordset_member["user_id"]}</p>
            <p> • 비밀번호 : {strPassword}</p>
            <br>
            <p  style="margin: 10px 0; padding: 5px 0; line-height: 1.8;">원천세 신고와 관련하여 추가 문의 사항이 있으시면 언제든지 연락 주시기 바랍니다.</p>
            <p class="fw-bold">감사합니다.</p>
          """
      else:
        email_content = f"""
            <h4 class="fw-bold">작성된 파일이 없습니다</h4>
        """
    return JsonResponse({
      "recordset": recordset,
      "recordset_adminInfo": recordset_adminInfo,
      "recordset_member": recordset_member,
      "email_content":email_content
    })
  
def get_mail_date(seq_no,  work_YY, work_MM,mailClass):
  with connection.cursor() as cursor:
    search_str = f"[세무법인대승] {work_YY}년 {work_MM}월 고지세액 안내"
    srch_len = len(search_str) 
    if work_MM >= 10:        srch_len += 1

    sql = f"""
        SELECT TOP 1 mail_date 
        FROM tbl_mail 
        WHERE seq_no = {seq_no} 
          AND mail_class = '{mailClass}' 
          AND LEFT(mail_subject, {srch_len}) = '{search_str}'
        ORDER BY mail_date DESC
    """
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0] if row else None

@csrf_exempt
def send_kakao_notification(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
    
    # admins 폴더 내의 .env 파일 로드
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    # ADMINS_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
    load_dotenv(os.path.join(CURRENT_DIR, '.env'))

    # 환경 변수 가져오기
    LinkID = os.getenv("LinkID")
    SecretKey = os.getenv("SecretKey")
    CorpNum = os.getenv("CorpNum")
    senderNumber = os.getenv("senderNumber")
    kakaoService = KakaoService(LinkID, SecretKey)
    kakaoService.IsTest = False#IsTest    

    snd = senderNumber  # 팝빌에 사전 등록된 발신번호  ※ 대체문자를 전송하는 경우에는 사전에 등록된 발신번호 입력 필수
    sndDT = ""    # 예약전송시간, 작성형식:yyyyMMddHHmmss, 공백 기재시 즉시전송
    receiver = ""    # 수신번호
    receiverName = ""    # 수신자 이름
    requestNum = ""      # 전송요청번호 : 팝빌이 접수 단위를 식별할 수 있도록 파트너가 할당하는 식별번호.1~36자리로 구성. 영문, 숫자, 하이픈(-), 언더바(_)를 조합
    btns = []    # 알림톡 버튼정보를 템플릿 신청시 기재한 버튼정보와 동일하게 전송하는 경우 btns를 빈 배열로 처리.
    altSubject = "대체문자 제목"  # - 메시지 길이(90byte)에 따라 장문(LMS)인 경우에만 적용.
    altContent = "알림톡 대체 문자"  # 대체문자 유형(altSendType)이 "A"일 경우, 대체문자로 전송할 내용 (최대 2000byte)
    altSendType = "C"        # None = 미전송, C = 알림톡과 동일 내용 전송 , A = 대체문자 내용(altContent)에 입력한 내용 전송
 
    flag = request.POST.get("flag", "").strip()
    seq_no = request.POST.get('seq_no')
    mem_user = get_object_or_404(MemUser, seq_no=seq_no)
    mem_deal = get_object_or_404(MemDeal, seq_no=seq_no)

    work_YY = int(request.POST.get("work_YY", "").strip())
    work_MM = int(request.POST.get("work_MM", "").strip())
    if work_MM in [1, 2, 3]:
        work_qt = 1
    elif work_MM in [4, 5, 6]:
        work_qt = 2
    elif work_MM in [7, 8, 9]:
        work_qt = 3
    elif work_MM in [10, 11, 12]:
        work_qt = 4    

    rcv_SEQNO = seq_no
    receiver = mem_user.hp_no.replace("-", "").strip()
    rcv_year = request.POST.get("work_YY", "").strip()
    rcv_mon = work_MM
    rcv_work_qt = work_qt 
    rcv_SKGB = request.POST.get("sms_SKGB", "").strip()
    cflag = (
        ZeroConv(mem_user.biz_no.replace("-", "")[-4:], 4, 0) +
        ZeroConv(seq_no, 5, 0) +
        ZeroConv(work_YY - 2000, 3, 0) +
        ZeroConv(work_MM, 2, 0) +
        ZeroConv(rcv_work_qt, 1, 0) + "cY"   #
        #'세목 K:기장보고서, i:	납부서들, 접수증, M:신고결과 + 수수료, N:	신고결과만, c: 신용카드사용내역,v:부가세,F:소득세신고대리수수료,(M,N:소득세신고결과 M:수수료있음)
    )
    # 사업자 정보 조회
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.ceo_name, a.biz_name, a.email, a.biz_no, a.biz_type, 
                   b.biz_manager, a.hp_no, b.kijang_YN
            FROM mem_user a, mem_deal b
            WHERE a.seq_no = b.seq_no AND a.seq_no = %s
        """, [rcv_SEQNO])
        row = cursor.fetchone()

        if row:
            ceo_name, biz_name, email, biz_no, biz_type, biz_manager, hp_no, kijang_YN = row
            rcv_biz_no = biz_no.strip()
            receiver = hp_no.replace("-", "").strip()
            receiverName = ceo_name if biz_manager == "화물" else biz_name.strip()
            rcv_bizMail = email.strip()
        else:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)

    # 담당자 정보 조회
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Admin_Name, admin_tel_no FROM Mem_Admin
            WHERE Admin_ID = (SELECT biz_manager FROM mem_deal WHERE seq_no = %s)
        """, [rcv_SEQNO])
        row = cursor.fetchone()

        if row:
            rcv_Admin_Name, rcv_admin_tel_no = row
        else:
            rcv_Admin_Name, rcv_admin_tel_no = "", ""

    # 기수별 신고 정보 설정
    tax_quarter_mapping = {
        1: (f"{rcv_year}년 1기", "예정(정기)", "C17"),
        2: (f"{rcv_year}년 1기", "확정(정기)", "C07"),
        3: (f"{rcv_year}년 2기", "예정(정기)", "C17"),
        4: (f"{rcv_year}년 2기", "확정(정기)", "C07"),
    }
    ks1, ks2, rcv_SKGB = tax_quarter_mapping.get(int(rcv_work_qt), ("", "", ""))


    # 알림톡 메시지 내용 구성
    content = ""
    templateCode = ""
    strU = ""#버튼링크
    if flag == "VatIntro":
      strU = f"https://daeseungtax.co.kr/kakao?flag=vatNtsHelp&seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={work_MM}&work_qt={rcv_work_qt}&SKGB={rcv_SKGB}"
      btns.append(
        KakaoButton(
            n= "국세청 신고도움 서비스",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )         
      content = "[부가가치세 신고 안내]\n\n"
      content += f"안녕하세요 세무법인 대승입니다. 이번달 25일은 {rcv_year}년도 {ks1[-2:]} {ks2} 부가가치세 신고납부 기한입니다.\n"
      content += "신고시 누락자료가 없도록 아래 해당하는 자료를 준비하여 주시기 바랍니다.\n\n"
      content += "- 종이로 발행한 매출 및 매입 세금계산서\n"
      content += "- 온라인 매출시 대행사의 매출자료\n"
      content += "- 수출시 인보이스, 수출신고필증, 신용장 등\n"
      content += "- 차량거래시 자동차등록증 등\n"

      templateCode = "023070000004"
      if biz_type < 4:
          templateCode = "023070000005"
          content += "- 부동산거래시 매매계약서 등\n"
          content += "- 법인통장 거래내역 엑셀자료\n"

      content += "- 기타 간이영수증 또는 계약서\n\n"
      content += "신고관련 문의사항이 있으시면 담당자에게 연락 바랍니다.\n"
      content += f"■ 대승 담당자 : {rcv_Admin_Name} ☎{rcv_admin_tel_no}\n\n"
      content += "감사합니다.\n"       
    elif flag == "VatResult":
      # strU1 = f"http://www.simplebook.co.kr/kakao/vat_view.asp?seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={rcv_mon}"
      sflag = cflag.replace("cY","vJ")
      strU1 = f"https://daeseungtax.co.kr/kakao?flag=vatResultJupsu&s={sflag}"
      btns.append(
        KakaoButton(
            n= "접수증 조회하기",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU1,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU1 # [앱링크-Android, 웹링크-PC URL]
        )
      )      
      # strU2 = f"http://www.simplebook.co.kr/kakao/vat_Result.asp?seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={rcv_mon}&work_qt={rcv_work_qt}&SKGB={rcv_SKGB}"
      sflag = cflag.replace("cY","vS")
      strU2 = f"https://daeseungtax.co.kr/kakao?flag=vatResultSummit&s={sflag}"
      btns.append(
        KakaoButton(
            n= "신고 결과 확인하기",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU2,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU2 # [앱링크-Android, 웹링크-PC URL]
        )
      )    
      
      # 납부 세액 조회
      with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 차감납부할세액, SUBSTRING(신고시각, 0, 11) 신고시각 
            FROM 부가가치세전자신고3
            WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = %s
            ORDER BY 신고시각 DESC
        """, [rcv_biz_no, ks1, rcv_SKGB])
        row = cursor.fetchone()

        if row:
            차감납부할세액, rcv_RegDt = row
        else:
            차감납부할세액, rcv_RegDt = 0, ""     

        if float(차감납부할세액) > 0:
            #templateCode = "023050000466" if biz_manager != "화물" else "023050000465"#버튼3개
            templateCode = "025090000103"
            # strU3 = f"http://www.simplebook.co.kr/kakao/pdfviewer/viewer.asp?seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={rcv_mon}&work_qt={rcv_work_qt}&SKGB={rcv_SKGB}"
            sflag = cflag.replace("cY","vN")
            strU3 = f"https://daeseungtax.co.kr/kakao?flag=vatResultNapbu&s={sflag}"
            btns.append(
              KakaoButton(
                  n= "납부서 보기",  # 버튼명
                  t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
                  u1=strU3,  # [앱링크-iOS, 웹링크-Mobile]
                  u2=strU3 # [앱링크-Android, 웹링크-PC URL]
              )
            )                
        else:
            #templateCode = "023050000464"#버튼2개
            templateCode = "025090000102"

        content = (
            f"[부가가치세 신고 접수]\n\n"
            f"{receiverName}님 세무법인 대승입니다.\n"
            f"{rcv_year}년도 {ks1[-2:]} {ks2} 부가가치세 신고를 정상 접수하였습니다.\n"
            f"신고 결과는 메일 발송 드렸으며 아래 링크를 참고하시어 상세한 정보를 확인 바랍니다.\n\n"
            f"✅ 접  수  일 : {rcv_RegDt} \n"
            f"✅ 고객 메일 : {rcv_bizMail}\n"
            f"✅ 대승 담당자 : {rcv_Admin_Name}  ☎{rcv_admin_tel_no} \n\n"
            f"확인 후 이상 있으시면 담당자에게 연락 바랍니다. \n"
            f"감사합니다."     
        )
    elif flag =="VatPrepay":
      # 예정고지 세액 조회
      with connection.cursor() as cursor:
        cursor.execute("""
            SELECT YN_15 FROM tbl_vat
            WHERE seq_no = %s AND work_yy = %s AND work_qt = %s
        """, [seq_no, work_YY, work_qt])
        row = cursor.fetchone()  # e.g. (12345,) 또는 (None,)
        prePay = row[0] if row else 0
        try:
            prePay = int(prePay or 0)   # Decimal/str/None 모두 안전 처리
        except (TypeError, ValueError):
            prePay = 0
        vatprePay = "{:,.0f}".format(prePay)
        if prePay > 0:
            templateCode = "025100000115"
            strU3 = f"https://daeseungtax.co.kr/kakao?flag=VatPrepay&s={cflag}"
            btns.append(
              KakaoButton(
                  n= "예정고지 납부서",  # 버튼명
                  t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
                  u1=strU3,  # [앱링크-iOS, 웹링크-Mobile]
                  u2=strU3 # [앱링크-Android, 웹링크-PC URL]
              )
            )      
            content = (
                "안녕하세요, 세무법인 대승입니다.\n"
                f"{int(work_MM)+1}월은 부가가치세 예정고지분 납부의 달입니다.\n\n"
                "부가가치세 예정고지는 직전 6개월 납부세액의 절반을 미리 납부하는 것으로 확정신고시 기납부세액으로 차감됩니다.\n\n"
                "📅 예정고지 금액 및 기한\n"
                f"• 고지금액 : {vatprePay} 원\n"
                "• 납부기한 : 금월 25일(공휴일인 경우 익일)\n"
                "• 납부방법 : 첨부드린 납부서상의 가상계좌로 계좌이체\n\n"
                "📩 문의 사항\n"
                "부가가치세 신고와 관련하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.\n\n"
                "감사합니다.")   
            
    elif flag == "VatFee":
      templateCode = "025070000482"
      rcv_date = "10"
      vatFee = "0"
      with connection.cursor() as cursor:
        cursor.execute("""
            SELECT YN_12 FROM tbl_vat WHERE seq_no=%s AND work_YY=%s and work_QT=%s
        """, [seq_no, work_YY, rcv_work_qt])
        vatFee = "{:,.0f}".format(int(cursor.fetchone()[0])*1.1)
      if vatFee=="0":
        return JsonResponse({"status": "error", "message": "수수료가 작성되지 않았습니다"}, status=500)  # 🔴 오류 발생 시 500 반환   
      ks1ks2 = f"{ks1} {ks2}"
      content = (f"[{ks1ks2} 부가가치세 신고수수료 안내]\n\n"

                f"안녕하세요 세무법인대승입니다. \n"
                f"{ks1ks2} [{receiverName}]님의 부가가치세 신고를 정상 접수하였으며, 이에 대한 신고수수료를 아래와 같이 안내드립니다. \n\n"

                f"📌 신고수수료 : {vatFee}원\n"
                f"📅 결재 기한 : 접수당일\n"
                f"🏦 입금 계좌 : 하나은행 \n"
                f"                       581-910019-69904\n\n"

                f"📩 문의 사항\n"
                f"부가가치세 신고와 관련하여 궁금한 사항은 세무법인대승 채널톡이나 담당자에게 문의주시기 바랍니다.\n\n"

                f"🔸 담 당 자 : {rcv_Admin_Name}\n"
                f"🔸 전화번호 : {rcv_admin_tel_no}\n"

                f"감사합니다.")  
    elif flag == "vatElec":
      import datetime as dt
      from typing import Dict
      # 예외 달만 추가: 키='YYYY-MM', 값='YYYY-MM-DD' (실제 발행기한)
      EXCEPTIONS: Dict[str, str] = {
          # 발송월 :  발급기한
          "2025-10": "2025-10-15",
          "2026-01": "2026-01-12",
          "2026-05": "2026-05-11",
          "2026-10": "2026-10-12",
      }

      def prev_month_einvoice_deadline_day(exceptions: Dict[str, str] = EXCEPTIONS) -> int:
          """
          오늘(KST) 기준 '지난달분' 전자세금계산서 발행기한의 '일(day)' 숫자만 반환.
          - 기본: 이번 달 10일 → 10
          - 예외: exceptions에 이번 달 키('YYYY-MM')가 있으면 그 날짜의 일(day)을 반환
          """
          kst = dt.timezone(dt.timedelta(hours=9))
          today_kst = dt.datetime.now(kst).date()

          # 지난달분의 기한은 '이번 달 10일'이므로 이번 달을 키로 사용
          key = f"{today_kst.year}-{today_kst.month:02d}"

          # 예외가 있으면 해당 일(day)로
          if key in exceptions:
              # 'YYYY-MM-DD' → DD만 추출해 int로
              return int(exceptions[key].split("-")[2])

          # 기본은 10
          return 10
  
      templateCode = "023080000169"
      rcv_date = prev_month_einvoice_deadline_day()
      content = f"[{rcv_mon}월 전자세금계산서 발행안내]\n\n"
      content += f"안녕하세요 세무법인 대승입니다. 이번달 {rcv_date}일은 {rcv_mon}월 귀속분 전자세금계산서 발급기한입니다.\n\n"
      content += "아래 홈택스 전자세금계산서 내역에서 미발행 또는 미수취 세금계산서 유무를 확인하여 주시기 바랍니다. "
      content += "위 발급기한을 경과하여 발행/수취하는 세금계산서는 지연발급가산세가 발생하니 작성일자를 소급하여 발행하지 마시고 "
      content += "당월을 작성일자로 하여 정상발급하시기 바랍니다.\n\n"
      content += "감사합니다. "
      strU = f"https://daeseungtax.co.kr/kakao?flag=vatElec&seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={rcv_mon}&work_qt={rcv_work_qt}&SKGB="
      btns.append(
        KakaoButton(
            n= "홈택스 전자세금계산서 조회",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )        
    elif flag == "Card":
      strU = f"https://daeseungtax.co.kr/kakao?flag=Card&s={cflag}"
      btns.append(
        KakaoButton(
            n= "신용(체크)카드 사용내역",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )         
      if biz_type < 4:
          templateCode = "023090000539"
          content = "[신용(체크)카드 사용내역 안내]\n\n"
          content += "안녕하세요 세무법인대승입니다. \n"
          content +=f"  {rcv_year}년 {rcv_work_qt}분기 현재 홈택스에 등록된 신용카드별 사용내역을 아래와 같이 안내드립니다.\n"
          content += "  해외 사용내역은 홈택스에서 조회되지 않으니 해외 사용내역이 있는 경우 해당 내역을 당사로 전달하여 주시기 바랍니다.\n\n"
          content += "감사합니다."
      else:
          templateCode = "023090000535"
          content = ("[신용(체크)카드 사용내역 안내]\n\n"
                    "안녕하세요 세무법인대승입니다. \n"
                    f"  {rcv_year}년 {rcv_work_qt}분기 현재 홈택스에 등록된 신용카드별 사용내역을 아래와 같이 안내드립니다.\n"
                    "  해외 사용내역은 홈택스에서 조회되지 않으니 해외 사용내역이 있는 경우 해당 내역을 당사로 전달하여 주시기 바랍니다. "
                    "  또한 신규 발급된 카드가 있는 경우 새로이 등록하여야 하니 지연등록되어 미공제분이 발생되지 않도록 조기에 알려주시면 카드등록을 진행드리도록 하겠습니다.\n\n"
                    "감사합니다.")
    elif flag == "goji":
      strU = f"https://daeseungtax.co.kr/kakao?flag={flag}&s={cflag}"
      btns.append(
        KakaoButton(
            n= "고지세액 안내",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )           
      templateCode = "025020000558"
      tmpstr = f"{rcv_year}년 {rcv_mon}월"
      content = ("안녕하세요 세무법인 대승 입니다.\n\n"
                f"  [{tmpstr}] 조회일 현재 아래 안내드리는 세목으로 미납세액이 있으니 인터넷 뱅킹의 공과금 납부 메뉴에서 해당 전자납부번호로 조회하여 납부기한까지 고지세액을 납부하여 주시기 바랍니다. \n"
                "  납부기한까지 미납할 경우 체납세액으로 분류되며 기간 경과분에 대한 가산세가 추가되어 1개월 경과된 납부서가 재발송됩니다.\n\n"
                "감사합니다.")  
    elif flag == "pay":
      has_Napbuseo = False;
      folder_path = os.path.join('static/cert_DS/', mem_user.biz_name, str(work_YY), "인건비")
      if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # 폴더 내 파일 목록 가져오기
        monthly_files = [file for file in files if file.startswith(f"{work_MM}월")]  # "12월"로 시작하는 파일 필터링
        if monthly_files:
          has_Napbuseo = any("납부서" in file for file in monthly_files)      

      strU = f"https://daeseungtax.co.kr/kakao?flag=paysheet&s={cflag}"
      btns.append(
        KakaoButton(
            n= "지급대장 확인하기",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )  
      if has_Napbuseo:
        strU2 = f"https://daeseungtax.co.kr/kakao?flag=paynapbu&s={cflag}"
        btns.append(
          KakaoButton(
              n= "납부서 확인하기",  # 버튼명
              t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
              u1=strU2,  # [앱링크-iOS, 웹링크-Mobile]
              u2=strU2 # [앱링크-Android, 웹링크-PC URL]
          )
        )           
        templateCode = "025030000040"
        tmpstr = f"{rcv_year}년 {rcv_mon}월"
        content = (f"[{tmpstr} 지급대장 및 원천세 납부 안내]\n\n"
                   f"{rcv_mon}월 지급된 인건비 관련 지급명세서 및 소득세와 지방세 납부서를 보내드리니 {int(rcv_mon)+1}월 10일까지 [납부서 확인하기]의 납부서를 확인하여 가상계좌로 송금하시기 바랍니다.\n\n"
                  "📌 납부방법 안내\n\n"
                  "✅ 소득세 : 홈택스 로그인 > 납부\n"
                  "    고지환급 > 납부할 세액 조회납부\n"
                  "✅ 지방세 : 위택스 로그인 >\n"
                  "    세금납부 > 지방소득세 납부\n"
                  "✅ 납부기한 경과시 납부금액의 3% \n"
                  "    가산세 발생\n\n"
                  "📩 문의 사항\n"
                  "원천세 신고와 관련하여 궁금한 사항 있으시면 문의주시기 바랍니다.\n\n"
                  "감사합니다.")      
      #납부서가 없는 경우     
      else:       
        templateCode = "025030000041"
        tmpstr = f"{rcv_year}년 {rcv_mon}월"
        content = (f"[{rcv_year}년 {rcv_mon}월 지급대장 및 원천세 신고 안내]\n\n"
                  f"{rcv_mon}월 지급된 인건비 관련 지급명세서를 보내드리니 지급내역이 이상없는지 확인하여 주시기 바랍니다. \n\n"
                  "📌 신고된 원천세는 연말정산등으로 발생한 환급금과 충당되어 납부할 금액이 없으니 이점 참고하여 주시기 바랍니다.\n\n"
                  "📩 문의 사항\n"
                  "원천세 신고와 관련하여 궁금한 사항 있으시면 문의주시기 바랍니다.\n\n"
                  "감사합니다.")      
    elif flag == "CorpFee":
      templateCode = "025030000169"
      #세무조정료 계산내역 버튼
      strU1 = f"https://daeseungtax.co.kr/kakao?flag=CorpFee&s={cflag}"
      btns.append(
        KakaoButton(
            n= "세무조정료 계산내역",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU1,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU1 # [앱링크-Android, 웹링크-PC URL]
        )
      )  
      #업무 보수기준 버튼
      strU2 = f"https://daeseungtax.co.kr/kakao?flag=CorpFeeRule&s={cflag}"
      btns.append(
        KakaoButton(
            n= "업무 보수기준",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU2,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU2 # [앱링크-Android, 웹링크-PC URL]
        )
      )    
      corporationFee = "0"
      with connection.cursor() as cursor:
        cursor.execute("""
            SELECT YN_8 FROM tbl_corporate2 WHERE seq_no=%s AND work_YY=%s
        """, [seq_no, work_YY])
        corporationFee = "{:,.0f}".format(int(cursor.fetchone()[0])*1.1)
      if corporationFee=="0":
        return JsonResponse({"status": "error", "message": "수수료가 작성되지 않았습니다"}, status=500)  # 🔴 오류 발생 시 500 반환
      tmpDuedate = f"{int(rcv_year)+1}년 {rcv_mon}월말일"
      content = (f"[{rcv_year}년 귀속 법인세 세무조정료 청구 안내]\n\n"
                "안녕하세요 세무법인대승입니다. \n"
                f"귀사의 {rcv_year}년 귀속 법인세 신고가 정상적으로 접수되었으며, 이에 대한 세무조정료를 아래와 같이 안내드립니다. \n\n"
                f"📌 세무조정료 : {corporationFee}원\n"
                f"📅 결재 기한 : {tmpDuedate} \n"
                "🏦 입금 계좌 : 하나은행 \n"
                "                       581-910019-69904\n\n"
                "📩 문의 사항\n"
                "법인세 신고와 관련하여 궁금한 사항은 세무법인대승 채널톡이나 담당자에게 문의주시기 바랍니다.\n\n"
                "감사합니다.")  
    elif flag == "CorpResult":
      #신고내용 요약안내 버튼
      strU1 = f"https://daeseungtax.co.kr/kakao?flag=CorpResult&s={cflag}"
      btns.append(
        KakaoButton(
            n= "신고내용 요약안내",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU1,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU1 # [앱링크-Android, 웹링크-PC URL]
        )
      )  
      #접수증 확인하기 버튼
      strU2 = f"https://daeseungtax.co.kr/kakao?flag=CorpSummit&s={cflag}"
      btns.append(
        KakaoButton(
            n= "접수증 확인하기",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU2,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU2 # [앱링크-Android, 웹링크-PC URL]
        )
      )        
      content = (f"[{work_YY}년 귀속 법인세 신고 접수결과 안내]\n\n"
                "안녕하세요 세무법인대승입니다. \n"
                f"{work_YY}년귀속 법인세 신고 접수결과를 아래와 같이 보내드립니다. \n\n"
                "📩 문의 사항\n"
                "법인세 신고와 관련하여 궁금한 사항은 세무법인대승 채널톡이나 담당자에게 문의주시기 바랍니다.\n\n"
                "감사합니다.")  

      has_Napbuseo = False;
      folder_path = os.path.join('static/cert_DS/', mem_user.biz_name, str(work_YY), "세무조정계산서")
      if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # 폴더 내 파일 목록 가져오기
        has_Napbuseo = any(file.endswith(("200.pdf", "201.pdf", "202.pdf", "203.pdf")) for file in files)

      #납부서 추가        
      if has_Napbuseo:
        strU3 = f"https://daeseungtax.co.kr/kakao?flag=CorpNapbuseo&s={cflag}"
        btns.append(
          KakaoButton(
              n= "납부서 확인하기",  # 버튼명
              t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
              u1=strU3,  # [앱링크-iOS, 웹링크-Mobile]
              u2=strU3 # [앱링크-Android, 웹링크-PC URL]
          )
        )           
        templateCode = "025030000167"
      #납부서가 없는 경우     
      else:       
        templateCode = "025030000168"     
    elif flag == "CorpIntro":
      strU = f"https://daeseungtax.co.kr/kakao?flag=CorpIntro&s={cflag}"
      btns.append(
        KakaoButton(
            n= "국세청 신고도움 안내문",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )           
      templateCode = "025030000267"
      content = (f"[{rcv_year}년 귀속 법인세 신고 및 납부 안내]\n\n"
                f"{int(rcv_year)+1}년 {rcv_mon}월은 법인세 신고납부의 달입니다. 기장보고서를 통해 전달드린 최종 당기순이익으로 {rcv_year}년 귀속 법인세를 신고접수할 예정입니다.\n\n"
                "법인세는 기업의 1년간 순이익에 대해 부과되는 세금으로, 모든 법인은 사업연도 종료일이 속하는 달의 말일부터 3개월 이내에 신고 및 납부해야 합니다. 전달드리는 국세청 신고도움 안내문을 확인하시어 누락되는 세액감면공제가 없는지 확인하시기 바랍니다.\n\n"
                "📌 국세청 신고도움 안내문 내용\n"
                "✅ 직전 3년간 동종 업종 평균 \n"
                "      매출액 및 소득률\n"
                "✅ 업무무관 신용카드 사용내역\n"
                "✅ 법인세 신고 시 유의사항 등\n\n"
                f"당사가 작성하는 최종 결산서 및 납부서는 {rcv_mon}월 중순부터 제공될 예정입니다.\n\n"
                "🔹해외 법인 보유 기업 필독🔹\n"
                "해외에 지점 또는 자회사(자본 출자 포함)를 보유한 기업은 반드시 해외현지법인명세서 제출하여야 합니다.\n\n"
                f"🚨 당사로 제출 기한: {rcv_mon}월 15일까지\n"
                "🚨 미제출 시 현지법인 건당 1000만 원의 과태료가 부과됩니다.(국제조세조정에관한 법률 제87조)\n\n"
                "📩 문의 사항\n"
                "법인세 신고와 관련하여 궁금한 점이나 해외현지법인명세서 제출에 필요한 사항 있으시면 문의주시기 바랍니다.\n\n"
                "감사합니다.")
    elif flag == "CorpJungkanIntro":      
      fiscalMM = mem_deal.fiscalmm
      sql = f"select ISNULL(총부담세액_합계, 0) total_tax from tbl_equityeval WHERE 사업자번호='{biz_no}' AND left(사업연도말,4)='{work_YY-1}'"
      # print(sql)
      rows = fetch_results(sql,'')
      if not rows:
          total_tax = 0.0
      else:
          first = rows[0]
          if isinstance(first, dict):
              total_tax = float(first.get("total_tax") or 0.0)
          elif isinstance(first, (list, tuple)):
              total_tax = float(first[0] or 0.0)
          else:
              total_tax = float(first or 0.0)

      preTax ="{:,.0f}".format(total_tax/2)
      templateCode = "025080000617"
      content = ("안녕하세요, 세무법인 대승입니다."
                f"{rcv_year}년 {rcv_mon}월은 법인세 중간예납 신고납부의 달입니다.\n\n"
                "📅 중간예납 기간 및 계산\n"
                f"• 신고대상 : {fiscalMM}월 결산 법인\n"
                "• 계산방법 : 직전 사업연도 법인세를 기준으로 절반을 납부. 상반기 영업실적을 중간결산하여 선택납부 가능\n"
                "🚨 직전 사업연도에 법인세 산출세액이 없거나 확정되지 않은 경우 반드시 상반기 실적을 중간결산하여 납부해야 합니다.\n\n"
                "📌 귀 법인의 예상 세액\n"
                f"• 예상 중간예납세액 : {preTax} 원\n"
                "• 상반기 가결산을 통해 예상납부세액 보다 감소될 수 있음\n"
                "• 납부서는 법인세 중간예납 신고접수시 전달예정\n\n"
                "📩 문의 사항\n"
                "법인세 중간예납 신고와 관련하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.\n\n"
                "감사합니다.")
    elif flag == "CorpJungkanResult":
      fiscalMM = mem_deal.fiscalmm
      sql = f"select ISNULL(총부담세액_합계, 0) total_tax from tbl_equityeval_MID WHERE 사업자번호='{biz_no}' AND left(사업연도말,4)='{work_YY-1}'"
      # print(sql)
      rows = fetch_results(sql,'')
      if not rows:
          total_tax = 0.0
      else:
          first = rows[0]
          if isinstance(first, dict):
              total_tax = float(first.get("total_tax") or 0.0)
          elif isinstance(first, (list, tuple)):
              total_tax = float(first[0] or 0.0)
          else:
              total_tax = float(first or 0.0)

      preTax ="{:,.0f}".format(total_tax/2)
      templateCode = "025080000617"
      #신고내용 요약안내 버튼
      strU1 = f"https://daeseungtax.co.kr/kakao?flag=CorpResult&s={cflag}"
      btns.append(
        KakaoButton(
            n= "신고내용 요약안내",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU1,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU1 # [앱링크-Android, 웹링크-PC URL]
        )
      )  

      has_Napbuseo = False;
      folder_path = os.path.join('static/cert_DS/', mem_user.biz_name, str(work_YY), "세무조정계산서")
      if os.path.exists(folder_path):
        files = os.listdir(folder_path)  # 폴더 내 파일 목록 가져오기
        has_Napbuseo = any(file.endswith(("204.pdf")) for file in files)

      #납부서 추가        
      if has_Napbuseo:
        strU3 = f"https://daeseungtax.co.kr/kakao?flag=CorpJungkanNapbuseo&s={cflag}"
        btns.append(
          KakaoButton(
              n= "납부서 확인하기",  # 버튼명
              t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
              u1=strU3,  # [앱링크-iOS, 웹링크-Mobile]
              u2=strU3 # [앱링크-Android, 웹링크-PC URL]
          )
        )           
        templateCode = "025030000167"
      #납부서가 없는 경우     
      else:       
        templateCode = "025030000168"        
      content = ("안녕하세요, 세무법인 대승입니다."
                f"{rcv_year}년 {rcv_mon}월은 법인세 중간예납 신고납부의 달입니다.\n\n"
                "📅 중간예납 기간 및 계산\n"
                f"• 신고대상 : {fiscalMM}월 결산 법인\n"
                "• 계산방법 : 직전 사업연도 법인세를 기준으로 절반을 납부. 상반기 영업실적을 중간결산하여 선택납부 가능\n"
                "🚨 직전 사업연도에 법인세 산출세액이 없거나 확정되지 않은 경우 반드시 상반기 실적을 중간결산하여 납부해야 합니다.\n\n"
                "📌 귀 법인의 예상 세액\n"
                f"• 예상 중간예납세액 : {preTax} 원\n"
                "• 상반기 가결산을 통해 예상납부세액 보다 감소될 수 있음\n"
                "• 납부서는 법인세 중간예납 신고접수시 전달예정\n\n"
                "📩 문의 사항\n"
                "법인세 중간예납 신고와 관련하여 궁금한 사항 있으시면 업무 담당자에게 문의주시기 바랍니다.\n\n"
                "감사합니다.")
             
    try:
      tmparr = [          CorpNum,
          templateCode,
          snd,
          content,
          altContent,
          altSendType,
          sndDT,
          receiver,
          receiverName,
          LinkID,
          requestNum,
          btns,
          altSubject]
      # print(tmparr)
      receiptNum = kakaoService.sendATS(
          CorpNum,
          templateCode,
          snd,
          content,
          altContent,
          altSendType,
          sndDT,
          receiver,
          receiverName,
          LinkID,
          requestNum,
          btns,
          altSubject,
      )
      # 전송 결과 저장 (DB Insert)
      time.sleep(5)
      KakaoSentInfo =  kakaoService.getMessages(CorpNum, receiptNum, LinkID)   
      # 1️⃣ Popbill API 응답이 None인지 확인
      if KakaoSentInfo is None:
          print("Popbill API에서 응답이 없습니다.")
          KakaoSentInfo = {}  # 빈 딕셔너리로 기본값 설정

      # 2️⃣ `JsonObject`를 `dict`로 변환
      if hasattr(KakaoSentInfo, 'to_json') and callable(KakaoSentInfo.to_json):
          KakaoSentInfo = KakaoSentInfo.to_json()
      elif hasattr(KakaoSentInfo, '__dict__'):
          KakaoSentInfo = KakaoSentInfo.__dict__
      sendCnt = KakaoSentInfo.get("sendCnt")
      successCnt = KakaoSentInfo.get("successCnt")
      if successCnt=='1':successCnt = "Y"
      kktMsg = ""
      # print(f"보낸카톡:{sendCnt},성공카톡:{successCnt}")
      re_content = content.replace("년도","년")
      strSql = f" Insert into Tbl_OFST_KAKAO_SMS VALUES ('{rcv_SEQNO}','{biz_name}','{receiver}','{re_content}','{strU}','{templateCode}','{successCnt}','{receiptNum}', convert(varchar(20),getdate(),121) ) "
      # print(strSql)
      connection.cursor().execute(strSql)        
      if successCnt=="Y":
        kktMsg = "카톡으로 전송완료"
        return JsonResponse({"status": "success", "message": rcv_SEQNO}, status=200)
      else:
        kktMsg = "문자로 전송됨. 채널톡 전송실패하니 채널톡 친구추가 요청하기"  # 전송결과 DB에 저장
        return JsonResponse({"status": "error", "message": kktMsg}, status=500)  # 🔴 오류 발생 시 500 반환

    except PopbillException as PE:
        return JsonResponse({"status": "error", "message": f"{PE.code}:{PE.message}"}, status=500)  # 🔴 오류 발생 시 500 반환
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return JsonResponse({"status": "error", "message": "Internal Server Error"}, status=500)  # 🔴 예기치 않은 오류 500 반환

def sendKakao_Bulk(request):
  # admins 폴더 내의 .env 파일 로드
  CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  
  load_dotenv(os.path.join(CURRENT_DIR, '.env'))

  LinkID = os.getenv("LinkID")
  SecretKey = os.getenv("SecretKey")
  CorpNum = os.getenv("CorpNum")
  senderNumber = os.getenv("senderNumber")
  kakaoService = KakaoService(LinkID, SecretKey)
  kakaoService.IsTest = False#IsTest  
  snd = senderNumber
  sndDT = ""    # 수신번호
  receiver = ""    # 수신자 이름
  receiverName = ""    # 전송요청번호
  requestNum = ""    # 팝빌이 접수 단위를 식별할 수 있도록 파트너가 할당하는 식별번호.
  altSubject = "대체문자 제목"
  altContent = "알림톡 대체 문자"
  altSendType = "C"    

  work_YY = request.POST.get("work_YY")
  work_MM = request.POST.get("work_MM")
  work_YY = int(request.POST.get("work_YY", "").strip())
  work_MM = int(request.POST.get("work_MM", "").strip())   
  work_qt = 0
  if work_MM in [1, 2, 3]:
      work_qt = 1
  elif work_MM in [4, 5, 6]:
      work_qt = 2
  elif work_MM in [7, 8, 9]:
      work_qt = 3
  elif work_MM in [10, 11, 12]:
      work_qt = 4     
  flag = request.POST.get("flag")
  seq_nos = request.POST.get("seq_nos")
  seq_nos = json.loads(seq_nos)
  print(seq_nos)

  # 수신정보 배열 (최대 1000개 가능)
  KakaoMessages = []
  x = 0  # Add counter variable
  for seq_no in seq_nos:
    mem_user = get_object_or_404(MemUser, seq_no=seq_no)
    rcv_SEQNO = seq_no
    receiver = mem_user.hp_no.replace("-", "").strip()
    rcv_year = request.POST.get("work_YY", "").strip()
    rcv_mon = work_MM
    rcv_work_qt = work_qt
    rcv_SKGB = request.POST.get("sms_SKGB", "").strip()
    cflag = (
        ZeroConv(mem_user.biz_no.replace("-", "")[-4:], 4, 0) +
        ZeroConv(seq_no, 5, 0) +
        ZeroConv(work_YY - 2000, 3, 0) +
        ZeroConv(work_MM, 2, 0) +
        ZeroConv(work_qt, 1, 0) + "cY"
    )      
    # 사업자 정보 조회
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT a.ceo_name, a.biz_name, a.email, a.biz_no, a.biz_type, 
                  b.biz_manager, a.hp_no, b.kijang_YN
            FROM mem_user a, mem_deal b
            WHERE a.seq_no = b.seq_no AND a.seq_no = %s
        """, [rcv_SEQNO])
        row = cursor.fetchone()

        if row:
            ceo_name, biz_name, email, biz_no, biz_type, biz_manager, hp_no, kijang_YN = row
            rcv_biz_no = biz_no.strip()
            receiver = hp_no.replace("-", "").strip()
            receiverName = ceo_name if biz_manager == "화물" else biz_name.strip()
            rcv_bizMail = email.strip()
        else:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)

    # 담당자 정보 조회
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Admin_Name, admin_tel_no FROM Mem_Admin
            WHERE Admin_ID = (SELECT biz_manager FROM mem_deal WHERE seq_no = %s)
        """, [rcv_SEQNO])
        row = cursor.fetchone()

        if row:
            rcv_Admin_Name, rcv_admin_tel_no = row
        else:
            rcv_Admin_Name, rcv_admin_tel_no = "", ""

    # 알림톡 메시지 내용 구성
    content = ""
    templateCode = ""
    btns = []
    strU = ""#버튼링크
    if flag == "Card":
      strU = f"https://daeseungtax.co.kr/kakao?flag=Card&s={cflag}"
      btns.append(
        KakaoButton(
            n= "신용(체크)카드 사용내역",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )         
      if biz_type < 4:
          templateCode = "023090000539"
          content = "[신용(체크)카드 사용내역 안내]\n\n"
          content += "안녕하세요 세무법인대승입니다. \n"
          content +=f"  {rcv_year}년 {rcv_work_qt}분기 현재 홈택스에 등록된 신용카드별 사용내역을 아래와 같이 안내드립니다.\n"
          content += "  해외 사용내역은 홈택스에서 조회되지 않으니 해외 사용내역이 있는 경우 해당 내역을 당사로 전달하여 주시기 바랍니다.\n\n"
          content += "감사합니다."
      else:
          templateCode = "023090000535"
          content = ("[신용(체크)카드 사용내역 안내]\n\n"
                    "안녕하세요 세무법인대승입니다. \n"
                    f"  {rcv_year}년 {rcv_work_qt}분기 현재 홈택스에 등록된 신용카드별 사용내역을 아래와 같이 안내드립니다.\n"
                    "  해외 사용내역은 홈택스에서 조회되지 않으니 해외 사용내역이 있는 경우 해당 내역을 당사로 전달하여 주시기 바랍니다. "
                    "  또한 신규 발급된 카드가 있는 경우 새로이 등록하여야 하니 지연등록되어 미공제분이 발생되지 않도록 조기에 알려주시면 카드등록을 진행드리도록 하겠습니다.\n\n"
                    "감사합니다.")
    elif flag == "vatElec":
      templateCode = "023080000169"
      rcv_date = "10"
      content = f"[{rcv_mon}월 전자세금계산서 발행안내]\n\n"
      content += f"안녕하세요 세무법인 대승입니다. 이번달 {rcv_date}일은 {rcv_mon}월 귀속분 전자세금계산서 발급기한입니다.\n\n"
      content += "아래 홈택스 전자세금계산서 내역에서 미발행 또는 미수취 세금계산서 유무를 확인하여 주시기 바랍니다. "
      content += "위 발급기한을 경과하여 발행/수취하는 세금계산서는 지연발급가산세가 발생하니 작성일자를 소급하여 발행하지 마시고 "
      content += "당월을 작성일자로 하여 정상발급하시기 바랍니다.\n\n"
      content += "감사합니다. "
      strU = f"https://daeseungtax.co.kr/kakao?flag=vatElec&seq={rcv_SEQNO}&work_yy={rcv_year}&work_mm={rcv_mon}&work_qt={rcv_work_qt}&SKGB="
      btns.append(
        KakaoButton(
            n= "홈택스 전자세금계산서 조회",  # 버튼명
            t="WL",  # 버튼유형 [DS-배송조회, WL-웹링크, AL-앱링크, MD-메시지전달, BK-봇키워드]
            u1=strU,  # [앱링크-iOS, 웹링크-Mobile]
            u2=strU # [앱링크-Android, 웹링크-PC URL]
        )
      )             
    KakaoMessages.append(
        KakaoReceiver(
            rcv=receiver,  # 수신번호
            rcvnm=receiverName,  # 수신자 이름
            msg=content,  # 알림톡 내용 (최대 400자)
            interOPRefKey=seq_no,  # 파트너 지정키, 수신자 구분용 메모
        )
    ) 
    KakaoMessages[x].btns = btns   
    x += 1  # Increment counter
  receiptNum = kakaoService.sendATS_multi(
    CorpNum,
    templateCode,
    snd,
    "",
    "",
    altSendType,
    sndDT,
    KakaoMessages,
    LinkID,
    requestNum,
    btns,
  )        
  time.sleep(x*0.5+5)

  MAX_RETRY = 5  # 최대 재시도 횟수
  retry_count = 0
  KakaoSentInfo = None

  while retry_count < MAX_RETRY:
      KakaoSentInfo = kakaoService.search(
          CorpNum,
          datetime.today().strftime("%Y%m%d"),
          datetime.today().strftime("%Y%m%d"),
          "2", "", "0", False, 1, 500, "D", LinkID, None
      )

      # None 응답 처리
      if KakaoSentInfo is None:
          print("Popbill API에서 응답이 없습니다.")
      # code == 1 (성공) 시 루프 탈출
      elif hasattr(KakaoSentInfo, 'code') and KakaoSentInfo.code == 1:
          print("✅ API 응답 성공. 이후 코드 실행합니다.")
          break
      else:
          code = getattr(KakaoSentInfo, 'code', '알 수 없음')
          message = getattr(KakaoSentInfo, 'message', '메시지 없음')
          print(f"❌ API 응답 실패 (code: {code}, message: {message}) - {retry_count + 1}번째 시도")

      retry_count += 1
      time.sleep(2)  # 2초 대기 후 재시도 (서버 부담 방지)

  # 최종 확인
  if retry_count == MAX_RETRY:
    print("⚠️ 최대 재시도 횟수 도달. 중단합니다.")
      
    return JsonResponse({"status": "fail", "message": []})
  else:
    if KakaoSentInfo is None:
      print("Popbill API에서 응답이 없습니다.")
      KakaoSentInfo = {}  # 빈 딕셔너리로 기본값 설정
      return JsonResponse({"status": "fail", "message": []})
    elif hasattr(KakaoSentInfo, 'code') and KakaoSentInfo.code == 1:
      print(f"응답 코드 확인 후 진행 : {KakaoSentInfo.code}")
      if hasattr(KakaoSentInfo, 'to_json') and callable(KakaoSentInfo.to_json):
          KakaoSentInfo = KakaoSentInfo.to_json()
      elif hasattr(KakaoSentInfo, '__dict__'):
          KakaoSentInfo = KakaoSentInfo.__dict__
      kakao_list = KakaoSentInfo.get("list")

      sent_seqNos = []
      for idx, item in enumerate(kakao_list, 1):
        if hasattr(item, 'to_json') and callable(item.to_json):
            data = item.to_json()
        elif hasattr(item, '__dict__'):
            data = item.__dict__
        else:
            continue

        # 조건에 맞는 항목 필터링
        if data.get("receiptNum") ==receiptNum:
          seqNo = data.get("interOPRefKey")
          bizName = data.get("receiveName")
          receiveNum = data.get("receiveNum")
          content = data.get("content")
          print(f"seq_no:{seqNo},업체명:{bizName}")
          strSql = f" Insert into Tbl_OFST_KAKAO_SMS VALUES ('{seqNo}','{bizName}','{receiveNum}','{content}','','{templateCode}','Y','{receiptNum}', convert(varchar(20),getdate(),121) ) "
          # print(strSql)
          connection.cursor().execute(strSql)  
          sent_seqNos.append(seqNo)
      return JsonResponse({"status": "success", "message": sent_seqNos})        

# 기장 회원 팝업정보
def kijang_member_popup(request):
    if request.method == 'GET':
        seq_no = request.GET.get('seq_no')
        # 해당 seq_no를 가진 사용자가 존재하는지 확인
        mem_user = get_object_or_404(MemUser, seq_no=seq_no)
        mem_deal = get_object_or_404(MemDeal, seq_no=seq_no)
        userprofile = userProfile.objects.filter(title=mem_user.seq_no)
        if userprofile.exists():
            userprofile = userprofile.latest('description')
            userprofile_data = {
                "description": userprofile.description,
                "image": userprofile.image.url if userprofile.image else None, 
            }
        else:
            userprofile_data = None  # userProfile이 없을 경우

        mem_user_dict = {
            'seq_no': mem_user.seq_no,
            'biz_no': mem_user.biz_no,
            'biz_name': mem_user.biz_name,
            'ceo_name': mem_user.ceo_name,
            'email': mem_user.email,
            'hp_no': mem_user.hp_no,
            'biz_tel': mem_user.biz_tel,
            'biz_fax': mem_user.biz_fax,
            'ssn': mem_user.ssn[:6]+"-"+mem_user.ssn[6:13],
            'hometaxid':mem_deal.hometaxid,
            'hometaxpw':mem_deal.hometaxpw,
            'user_id':mem_user.user_id,
            'user_pwd':mem_user.user_pwd,
            "taxmgr_name":mem_deal.taxmgr_name,
            "taxmgr_tel":mem_deal.taxmgr_tel,
            'etc':mem_user.etc,
            'userprofile':userprofile_data,
            # 필요한 필드만 추가
        }
        return JsonResponse(mem_user_dict)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

@csrf_exempt
def send_sms_popbill(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(CURRENT_DIR, ".env"))

    LinkID = os.getenv("LinkID")
    SecretKey = os.getenv("SecretKey")
    CorpNum = os.getenv("CorpNum")
    defaultSender = os.getenv("senderNumber", "")

    seq_no = request.POST.get("seq_no")
    content = (request.POST.get("content") or "").strip()
    receiver_input = (request.POST.get("receiver") or "").strip()
    reserve_date = (request.POST.get("reserve_date") or "").strip()  # yyyy-mm-dd
    reserve_hour = (request.POST.get("reserve_hour") or "").strip()  # HH
    reserve_min = (request.POST.get("reserve_min") or "").strip()    # mm

    if not seq_no:
        return JsonResponse({"status": "error", "message": "seq_no is required"}, status=400)
    if not content:
        return JsonResponse({"status": "error", "message": "문자 내용을 입력하세요."}, status=400)

    mem_user = get_object_or_404(MemUser, seq_no=seq_no)
    mem_deal = get_object_or_404(MemDeal, seq_no=seq_no)

    # 발신번호: 담당 관리자 번호 우선, 없으면 .env 기본값
    senderNumber = ""
    admin_id = mem_deal.biz_manager
    if admin_id:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT admin_tel_no FROM Mem_Admin WHERE admin_id = %s",
                [admin_id],
            )
            row = cursor.fetchone()
            if row and row[0]:
                senderNumber = row[0].replace("-", "").strip()
    if not senderNumber:
        senderNumber = defaultSender.replace("-", "").strip()

    receiver = receiver_input or mem_user.hp_no or ""
    receiver = receiver.replace("-", "").strip()
    if not receiver:
        return JsonResponse({"status": "error", "message": "수신번호를 확인하세요."}, status=400)

    reserveDT = ""
    if reserve_date and reserve_hour and reserve_min:
        reserveDT = f"{reserve_date.replace('-', '')}{reserve_hour.zfill(2)}{reserve_min.zfill(2)}00"

    try:
        messageService = MessageService(LinkID, SecretKey)
        messageService.IsTest = False

        # 메시지 길이에 따라 SMS/LMS 자동 선택 (90바이트 초과 시 LMS)
        byte_len = fn_str_length(content)
        receiverName = mem_user.ceo_name or mem_user.biz_name or ""

        if byte_len > 90:
            # LMS는 제목이 필요하므로 40바이트 이내로 잘라 사용
            subject = fn_str_length_cut(content, 40)
            print(f"[send_sms_popbill] byte_len={byte_len} -> sendLMS, subject={subject}")
            receiptNum = messageService.sendLMS(
                CorpNum,
                senderNumber,
                receiver,
                receiverName,
                subject,
                content,
                reserveDT,
                False,
                None,
            )
        else:
            print(f"[send_sms_popbill] byte_len={byte_len} -> sendSMS")
            receiptNum = messageService.sendSMS(
                CorpNum,
                senderNumber,
                receiver,
                receiverName,
                content,
                reserveDT,
                False,
                None,
            )
        return JsonResponse({"status": "success", "receiptNum": receiptNum})
    except PopbillException as pe:
        return JsonResponse({"status": "error", "message": f"{pe.code}: {pe.message}"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

@csrf_exempt
def get_sms_prefill(request):
    """
    seq_no로 수신번호(mem_user.hp_no)와 발신번호(담당자 or 기본 발신번호)를 반환
    """
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(CURRENT_DIR, ".env"))
    defaultSender = os.getenv("senderNumber", "")

    seq_no = request.GET.get("seq_no")
    if not seq_no:
        print("[get_sms_prefill] missing seq_no")
        return JsonResponse({"status": "error", "message": "seq_no is required"}, status=400)

    mem_user = get_object_or_404(MemUser, seq_no=seq_no)
    mem_deal = get_object_or_404(MemDeal, seq_no=seq_no)

    senderNumber = ""
    admin_id = mem_deal.biz_manager
    if admin_id:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT admin_tel_no FROM Mem_Admin WHERE admin_id = %s",
                [admin_id],
            )
            row = cursor.fetchone()
            if row and row[0]:
                senderNumber = row[0].replace("-", "").strip()
    if not senderNumber:
        senderNumber = defaultSender.replace("-", "").strip()

    receiver = (mem_user.hp_no or "").replace("-", "").strip()

    print(
        "[get_sms_prefill]",
        f"seq_no={seq_no}, admin_id={admin_id}, sender={senderNumber}, receiver={receiver}",
    )

    return JsonResponse(
        {
            "status": "success",
            "sender": senderNumber,
            "receiver": receiver,
        }
    )
@csrf_exempt
def get_popbill_balance(request):
    """
    팝빌 계정의 잔여 포인트를 조회하고 SMS 전송 가능 건수로 환산하여 반환
    """
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

    # 1. 환경 변수 로드
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(CURRENT_DIR, ".env"))

    LinkID = os.getenv("LinkID")
    SecretKey = os.getenv("SecretKey")
    CorpNum = os.getenv("CorpNum")

    try:
        if not LinkID or not SecretKey or not CorpNum:
            return JsonResponse({"status": "error", "message": "Popbill env missing"}, status=400)

        # 2. 서비스 객체 생성 및 설정 (가이드 준수)
        messageService = MessageService(LinkID, SecretKey)
        messageService.IsTest = False             # 운영(Production) 환경
        messageService.IPRestrictOnOff = True     # 인증토큰 IP 검증 사용
        messageService.UseLocalTimeYN = True      # 로컬시스템 시간 사용

        # 3. SMS 단가 확인 (건수 계산용)
        # 가이드의 getUnitCost API를 활용하여 실제 과금 단가 확인
        unitCost = messageService.getUnitCost(CorpNum, "SMS")
        print(f"unitCost:{unitCost}")
        # 4. 잔여포인트 확인
        # 가이드의 getBalance API 호출
        remainPoint = messageService.getPartnerBalance(CorpNum)
        print(f"remainPoint:{remainPoint}")
        # 5. 건수 환산 (잔여포인트 / 단가)
        # 단가가 0일 경우를 대비한 예외처리 포함
        available_count = int(remainPoint / unitCost) if unitCost > 0 else 0
        
        return JsonResponse({
            "status": "success",
            "remainPoint": remainPoint,
            "unitCost": unitCost,
            "availableCount": available_count
        })

    except PopbillException as pe:
        print(f"[get_popbill_balance][error] {pe.code}: {pe.message}")
        return JsonResponse({"status": "error", "message": f"{pe.code}: {pe.message}"}, status=400)
    except Exception as e:
        print(f"[get_popbill_balance][exception] {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=400)

# 문자 발송 내역 조회
@csrf_exempt
def get_sent_sms_list(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    seq_no = request.POST.get("seq_no")
    print(f"[get_sent_sms_list] seq_no={seq_no}")
    
    # 제공해주신 쿼리를 바탕으로 작성 (DB 환경에 따라 ISNULL/COALESCE 선택)
    query = """
        SELECT 
            CASE  
                WHEN b.sms_class = 'ilyoung' THEN '일용직' 
                WHEN b.sms_class = 'pay' THEN '급여신고' 
                WHEN b.sms_class = 'vat' THEN '부가세신고' 
                WHEN b.sms_class = 'nonvat' THEN '면세신고' 
                WHEN b.sms_class = 'younmal' THEN '연말정산'  
                WHEN b.sms_class = 'corptax' THEN '법인세신고'
                WHEN b.sms_class = 'incometax' THEN '종소세신고' 
                WHEN b.sms_class = 'holiday' THEN '명절인사'  
                WHEN b.sms_class = 'ext' THEN '기타'
                ELSE '일반'
            END as sms_class_nm, 
            CONVERT(varchar, b.sms_send_dt, 120) as sms_send_dt, 
            ISNULL(b.sms_contents, '') as sms_contents, 
            ISNULL(b.sms_tel_no, '') as sms_tel_no 
        FROM mem_user a 
        INNER JOIN tbl_sms b ON a.seq_no = b.seq_no 
        WHERE a.seq_no = %s
        ORDER BY b.sms_send_dt DESC
    """
    # print(query)
    try:
        results = fetch_results(query, [seq_no]) # 기존에 정의된 fetch_results 활용
        print(f"[get_sent_sms_list] fetched rows={len(results)} : seq_no : {seq_no}")
        return JsonResponse({"status": "success", "data": results})
    except Exception as e:
        print(f"[get_sent_sms_list][error] {e}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


#메일 리스트 가져오기 flag에 따라
@csrf_exempt
def getSentMails(request):
  if request.method == "POST":
    seq_no = request.POST.get("seq_no")  
    flag = request.POST.get("flag") 
    recordset_mail = []
    recordset_content = []
    sql = f"select admin_name, biz_manager, biz_name, mail_subject, mail_content, mail_to, mail_from, mail_cc, mail_date, file_cnt, file_path, file_name   "
    sql += f"from tbl_mail  WHERE seq_no={seq_no} AND "
    if flag=="Pay" or flag=="pay":
      sql += f"mail_class in('pay','mail')  order by mail_date desc "
    else:
      sql += f"mail_class='{flag}'  order by mail_date desc "
    
    # print(sql)
    with connection.cursor() as cursor:
      cursor.execute(sql)
      rows = cursor.fetchall()
      columns = [col[0] for col in cursor.description]  # 컬럼명 가져오기    
      for i, row in enumerate(rows):
        row_dict = dict(zip(columns, row))  # 컬럼명과 값 매핑

        # isclip = '<img src="/script/ext411/examples/shared/icons/fam/clip.gif">' if row_dict['file_cnt'] and row_dict['file_cnt'] > 0 else ''

        recordset_mail.append([
            i,
            row_dict['mail_subject'],
            row_dict['mail_to'].strip(),
            row_dict['mail_cc'],
            row_dict['mail_date'],
            row_dict['file_cnt'],
            row_dict['admin_name']
        ])

        recordset_content.append([
            i,
            row_dict['mail_content'].replace("'", "\\'"),  # 작은따옴표 이스케이프 처리
            row_dict['file_cnt'],
            row_dict['file_path'],
            row_dict['file_name'],
            row_dict['mail_subject']
        ])
    # print(recordset_content)
    return JsonResponse({
        "recordset_mail": recordset_mail,
        "recordset_content": recordset_content
    }, safe=False)

#자료테이블 업데이트
def tbl_mng_jaroe_update(request):
  if request.method == "POST":
    seq_no = request.POST.get("seq_no")
    target = request.POST.get("target")
    work_YY = request.POST.get("work_YY")
    work_MM = request.POST.get("work_MM", None)  # work_MM이 없으면 None으로 설정
    val = request.POST.get("val") 


    #print(f"{target}:{seq_no}:{work_YY}:{val}")
    with connection.cursor() as cursor:
      if target == "bigo":
        txt_bigo = unquote(val)
        # ✅ `bigo` 값이 변경된 경우: work_MM을 빈 문자열 ''로 처리
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_mng_jaroe WHERE seq_no = %s AND work_YY = %s AND work_MM = ''
        """, [seq_no, work_YY])
        row_count = cursor.fetchone()[0]

        if row_count > 0:
            # 기존 데이터가 존재하면 UPDATE 실행
            cursor.execute("""
                UPDATE tbl_mng_jaroe 
                SET bigo = %s
                WHERE seq_no = %s AND work_YY = %s AND work_MM = ''
            """, [txt_bigo, seq_no, work_YY])

            return JsonResponse({"status": "success", "message": "bigo 업데이트"}, status=200)
        else:
            # 기존 데이터가 없으면 INSERT 실행
            cursor.execute("""
                INSERT INTO tbl_mng_jaroe (seq_no, work_YY, work_MM, bigo)
                VALUES (%s, %s, '', %s)
            """, [seq_no, work_YY, txt_bigo])
            return JsonResponse({"status": "success", "message": "bigo 신규생성"}, status=200)
      else:

        # Boolean 변환 (JS에서 true/false로 올 수도 있으므로 대비)
        val = "1" if val in ["1", "true", True] else "0"
        # ✅ `YN_1 ~ YN_14` 값이 변경된 경우
        cursor.execute("""
            SELECT COUNT(*) FROM tbl_mng_jaroe WHERE seq_no = %s AND work_YY = %s AND work_MM = %s
        """, [seq_no, work_YY, work_MM])
        row_count = cursor.fetchone()[0]

        if row_count > 0:
            # 기존 데이터가 존재하면 UPDATE 실행
            target_field = f"YN_{int(target) + 1}"
            sql = f"""
                UPDATE tbl_mng_jaroe 
                SET {target_field} = %s
                WHERE seq_no = %s AND work_YY = %s AND work_MM = %s
            """
            cursor.execute(sql, [val, seq_no, work_YY, work_MM])
            return JsonResponse({"status": "success", "message": "업데이트"}, status=200)

        else:
            # 기존 데이터가 없으면 INSERT 실행
            sql = """
                INSERT INTO tbl_mng_jaroe (seq_no, work_YY, work_MM, YN_1, YN_2, YN_3, YN_4, YN_5, YN_6, 
                YN_7, YN_8, YN_9, YN_10, YN_11, YN_12, YN_13, YN_14, bigo)
                
                VALUES (%s, %s, %s, %s, %s,   %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s,  %s, '')
            """
            #VALUES (%s, %s, %s, %s, '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '0', '')
            yn_values = ['0'] * 14  # YN_1 ~ YN_14 기본값 '0' 설정
            yn_index = int(target)  # target 값을 인덱스로 변환
            yn_values[yn_index] = val  # 해당 YN 값만 업데이트
            cursor.execute(sql, [seq_no, work_YY, work_MM] + yn_values)
            return JsonResponse({"status": "success", "message": "신규생성"}, status=200)

  return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def mem_deal_update(request):
  if request.method == "POST":
    seq_no = request.POST.get("seq_no")
    field = request.POST.get("field")
    val = request.POST.get("val") 

    if not seq_no or not field:
        return JsonResponse({"error": "seq_no 또는 field 값이 누락되었습니다."}, status=400)
    
    try:
        # 특정 `seq_no`에 해당하는 객체 가져오기
        obj = MemDeal.objects.get(seq_no=seq_no)
        
        # 동적으로 필드 값 업데이트
        setattr(obj, field, val)
        obj.save()
        
        return JsonResponse({"success": True, "message": f"{field} 필드가 성공적으로 업데이트되었습니다."})
    except MemDeal.DoesNotExist:
        return JsonResponse({"error": "해당 seq_no에 대한 데이터가 없습니다."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def PDF_Merge(fileName,directory):
  merger = PyPDF2.PdfMerger()
  filst = os.listdir(directory)
  for file in natsort.natsorted(filst):
    merger.append(os.path.join(directory,file))
  merger.write(f"{directory}/{fileName}.pdf")
  merger.close()
  print(directory+" 폴더에 "+fileName+".PDF로 병합 성공")
  return True

#조정료 계산기
def calculate_fees(flag,seq_no,work_YY):
  memuser = MemUser.objects.get(seq_no=seq_no)
  memdeal = MemDeal.objects.get(seq_no=seq_no)
  txtfiscalMM = f"0{memdeal.fiscalmm}" if int(memdeal.fiscalmm) < 10 else str(memdeal.fiscalmm)
  yearEnd = f"{work_YY}{txtfiscalMM}"      
  sql = ("select 업태,수입금액,산출세액_합계,총부담세액_합계"
         ",isnull(AdditionDC_YJ,0) AdditionDC_YJ,isnull(AdditionDC_Ddct,0) AdditionDC_Ddct,isnull(AdditionDC_Stnd,0) AdditionDC_Stnd,isnull(AdditionDC_JBCnt,0) AdditionDC_JBCnt"
         ",isnull(SAddition_Rsn,'') SAddition_Rsn,isnull(SAddition_Amt,0) SAddition_Amt,isnull(OAddition_Rsn,'') OAddition_Rsn"
         ",isnull(OAddition_Amt,0) OAddition_Amt,isnull(FAddition_Rsn,'') FAddition_Rsn,isnull(FAddition_amt,0) FAddition_amt "
         "from tbl_equityeval a "
         "left join tbl_Discount b on b.seq_no=(select seq_no from mem_user where biz_no=%s) "
         "where 사업자번호=%s and 사업연도말=%s")
  rs = fetch_results(sql, (memuser.biz_no,memuser.biz_no,yearEnd))
  if rs: 
    rs = rs[0]  # 첫 번째 딕셔너리 가져오기
    # 기본값 설정
    stndfee = 0
    str_stndRange = ""
    str_stndfee = ""
    revenue = int(rs["수입금액"])
    wcYuptae = rs["업태"]
    wcLocalTax = int(rs["산출세액_합계"]) - int(rs["총부담세액_합계"])
    bookcnt = int(rs["AdditionDC_JBCnt"])
    SAddition_Rsn = rs["SAddition_Rsn"]   #(4) 수수료추가 1
    OAddition_Rsn = rs["OAddition_Rsn"]   #(5) 수수료추가 2
    FAddition_Rsn = rs["FAddition_Rsn"]   #(6) 수수료추가 3
    SAddition_Amt = int(rs.get("SAddition_Amt") or rs.get("SAddition_Amt", Decimal(0)))
    OAddition_Amt = int(rs.get("OAddition_Amt") or rs.get("OAddition_Amt", Decimal(0)))
    FAddition_Amt = int(rs.get("FAddition_Amt") or rs.get("faddition_amt", Decimal(0)))
    AdditionDC_YJ = int(rs["AdditionDC_YJ"])
    AdditionDC_Ddct = int(rs["AdditionDC_Ddct"])
    AdditionDC_Stnd = int(rs["AdditionDC_Stnd"])
    # 수수료 적용 기준금액 계산
    if revenue < 100_000_000:
        stndfee = 300_000
        str_stndRange = "1억원 미만"
        str_stndfee = "300,000 원"
    elif revenue < 200_000_000:
        stndfee = 300_000 + (revenue - 100_000_000) * 20 / 10_000
        str_stndRange = "1억원 이상 2억원 미만"
        str_stndfee = "300,000 원 + 1억원 초과금액 × 20/10000"
    elif revenue < 300_000_000:
        stndfee = 500_000 + (revenue - 200_000_000) * 15 / 10_000
        str_stndRange = "2억원 이상 3억원 미만"
        str_stndfee = "500,000 원 + 2억원 초과금액 × 15/10000"
    elif revenue < 500_000_000:
        stndfee = 650_000 + (revenue - 300_000_000) * 12 / 10_000
        str_stndRange = "3억원 이상 5억원 미만"
        str_stndfee = "650,000 원 + 3억원 초과금액 × 12/10000"
    elif revenue < 1_000_000_000:
        stndfee = 890_000 + (revenue - 500_000_000) * 10 / 10_000
        str_stndRange = "5억원 이상 10억원 미만"
        str_stndfee = "890,000 원 + 5억원 초과금액 × 10/10000"
    elif revenue < 2_000_000_000:
        stndfee = 1_390_000 + (revenue - 1_000_000_000) * 8 / 10_000
        str_stndRange = "10억원 이상 20억원 미만"
        str_stndfee = "1,390,000 원 + 10억원 초과금액 × 8/10000"
    elif revenue < 5_000_000_000:
        stndfee = 2_190_000 + (revenue - 2_000_000_000) * 5 / 10_000
        str_stndRange = "20억원 이상 50억원 미만"
        str_stndfee = "2,190,000 원 + 20억원 초과금액 × 5/10000"
    elif revenue < 10_000_000_000:
        stndfee = 3_690_000 + (revenue - 5_000_000_000) * 2 / 10_000
        str_stndRange = "50억원 이상 100억원 미만"
        str_stndfee = "3,690,000 원 + 50억원 초과금액 × 2/10000"
    elif revenue < 50_000_000_000:
        stndfee = 4_690_000 + (revenue - 10_000_000_000) * 1 / 10_000
        str_stndRange = "100억원 이상 500억원 미만"
        str_stndfee = "4,690,000 원 + 100억원 초과금액 × 1/10000"
    elif revenue < 100_000_000_000:
        stndfee = 8_690_000 + (revenue - 50_000_000_000) * 0.5 / 10_000
        str_stndRange = "500억원 이상 1,000억원 미만"
        str_stndfee = "8,690,000 원 + 500억원 초과금액 × 0.5/10000"
    else:
        stndfee = 10_000_000 + (revenue - 100_000_000_000) * 0.25 / 10_000
        str_stndRange = "1,000억원 이상"
        str_stndfee = "10,000,000 원 + 1,000억원 초과금액 × 0.25/10000"

    # 업종별 가산율 설정
    if wcYuptae[:1] in ["도", "소"]:
        addingRate = 0.1
    elif wcYuptae[:1] in ["체", "교", "부"]:
        addingRate = 0.2
    else:
        addingRate = 0.3
    addingfee = stndfee * addingRate

    # 세액 감면공제 계산
    str_deductRange = ""
    deductTax = max(0, wcLocalTax)  # 음수 방지
    if deductTax < 10_000_000:
        deductfee = deductTax * 0.05
        str_deductRange = "1천만원 미만 5%"
    elif deductTax < 50_000_000:
        deductfee = deductTax * 0.06
        str_deductRange = "5천만원 미만 6%"
    else:
        deductfee = deductTax * 0.07
        str_deductRange = "5천만원 이상 7%"

    # 책 인쇄/제본비 계산
    bookfee = 5_000 * bookcnt

    # 총 수수료 계산
    totalfee = stndfee + addingfee + deductfee + bookfee + SAddition_Amt + OAddition_Amt + FAddition_Amt

    # 업종별 할인 적용
    if AdditionDC_YJ == 1:
        totalfee -= addingfee
    if AdditionDC_Ddct == 1:
        totalfee -= deductfee
    if AdditionDC_Stnd > 0:
        totalfee -= stndfee * AdditionDC_Stnd / 100

    # 백 단위 절사 (100원 단위로 내림)
    finalfee = math.floor(totalfee / 1000) * 1000

    return {
        "revenue":revenue,
        "stndfee": stndfee,
        "wcYuptae":wcYuptae,
        "str_stndRange": str_stndRange,
        "str_stndfee": str_stndfee,
        "addingRate": addingRate,
        "addingfee": addingfee,
        "deductTax": deductTax,
        "deductfee": deductfee,
        "str_deductRange": str_deductRange,
        "OAddition_Rsn":OAddition_Rsn,
        "FAddition_Rsn":FAddition_Rsn,
        "SAddition_Rsn":SAddition_Rsn,
        "OAddition_Amt":OAddition_Amt,
        "FAddition_Amt":FAddition_Amt,
        "SAddition_Amt":SAddition_Amt,
        "bookcnt": bookcnt,
        "bookfee": bookfee,
        "totalfee": totalfee,
        "finalfee": finalfee,
        "AdditionDC_YJ":AdditionDC_YJ,
        "AdditionDC_Ddct":AdditionDC_Ddct,
        "AdditionDC_Stnd":AdditionDC_Stnd,
      }
  else:  
    return {}  # 데이터가 없을 경우 빈 딕셔너리로 설정    

#자리수변환
def ZeroConv(temp, t_len, d_len):
    # 기본값 처리
    if temp == "" or temp is None:
        temp = 0
    temp = str(temp)

    # 소수점이 없으면 추가
    if "." not in temp:
        temp += ".0"

    # 소수부 처리
    if d_len > 0:
        s_float = f"{float(temp):.{d_len}f}".split(".")[1]
    else:
        s_float = ""

    # 정수부 처리
    temp_int = temp.split(".")[0]
    s_zero = ""

    # 필요한 0의 개수 계산
    j = t_len - d_len - len(temp_int)
    if float(temp) < 0:
        j += 1

    # 앞에 0 채우기
    for i in range(j):
        if i == 0 and float(temp) < 0:
            s_zero += "-"
        else:
            s_zero += "0"

    # 최종 변환 문자열 생성
    result = (s_zero + temp_int.replace("-", "") + s_float).replace(",", "")

    return result[:t_len]  # 지정된 길이만큼 반환

#컬럼명과 일치시켜서 Dict구조 만든다
def fetch_results(query, params):
  with connection.cursor() as cursor:
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

#전자신고 파일 업로드용 한글 글자수 계산로직
def fn_str_length(s):
    """문자열의 바이트 길이를 계산 (VBScript 스타일: 한글 2바이트, 영문 1바이트)"""
    str_byte = 0
    for char in s:
        # 한글은 Asc < 0로 판별, 2바이트로 계산
        if ord(char) > 127:  # UTF-8에서 한글은 127 이상
            str_byte += 2
        else:
            str_byte += 1
    return str_byte

def fn_str_length_cut(s, max_bytes):
    """문자열을 최대 max_bytes까지 자르는 함수 (VBScript 스타일)"""
    str_byte = 0
    result = ""
    
    if fn_str_length(s) > max_bytes:
        for char in s:
            char_bytes = 2 if ord(char) > 127 else 1
            if str_byte + char_bytes > max_bytes:
                break
            str_byte += char_bytes
            result += char
        return result
    return s

def mid_union(str_string, start_int, end_int):
    """VBScript MidUnion을 Python으로 구현 (바이트 단위)"""
    total_str = fn_str_length_cut(str_string, start_int - 1 + end_int)
    left_str = fn_str_length_cut(str_string, start_int - 1)
    right_str = total_str.replace(left_str, "", 1)  # 첫 번째 매칭만 제거
    return right_str
