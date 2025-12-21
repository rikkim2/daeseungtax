from __future__ import print_function 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
from app.models import userProfile
import os
import natsort

from app.models import MemUser
from app.models import MemAdmin
from app.models import MemDeal
from pdf2image import convert_from_path

import glob
from PIL import Image
from decimal import Decimal
from django.db.models import F, Subquery
from admins.utils import getMailContent

def index(request):
  context = {}
  flag = request.GET.get('flag')
  sflag = request.GET.get('s')
  sqno = request.GET.get('seq')
  work_yy = request.GET.get('work_yy')
  work_qt = request.GET.get('work_qt')
  work_mm = request.GET.get('work_mm')
  work_YY = request.GET.get('work_YY')  
  work_MM = request.GET.get('work_MM')  
  SKGB = "" 

  if sflag:
    sqno = int(sflag[4:9])
    work_yy = str(int(sflag[9:12]) + 2000)
    work_mm = str(int(sflag[12:14]))
    # print(f"work_mm:{work_mm}")
    work_qt = sflag[14:15]
    rcv_semok = sflag[15] #'세목 K:기장보고서, i:	납부서들, 접수증, M:신고결과 + 수수료, N:	신고결과만, c: 신용카드사용내역,v:부가세,F:소득세신고대리수수료,(M,N:소득세신고결과 M:수수료있음)
    rcv_semok2 = sflag[16] # 세목이 부가세(v)인 경우 N:납부서, S:신고결과, J:접수증
    SKGB = sflag[18:21].replace("0", "")

  if work_mm and ( work_qt=="" or work_qt==None):
    if int(work_mm) <= 3:        work_qt = "1"
    elif int(work_mm) <= 6:      work_qt = "2"
    elif int(work_mm) <= 9:      work_qt = "3"
    elif int(work_mm) <= 12:     work_qt = "4"
  
  strKi = "1"
  txtSKGB = SKGB
  if work_qt and int(work_qt)> 2:strKi = "2"
  memuser = MemUser.objects.get(seq_no=sqno)
  memdeal = MemDeal.objects.get(seq_no=sqno)
  memAdmin = MemAdmin.objects.get(admin_id=memdeal.biz_manager)
  context.update({
      "seq_no" : sqno,
      "work_yy" : work_yy,
      "work_mm" : work_mm,
      "work_qt" : work_qt,
      "flag":flag,
      "biz_name" : memuser.biz_name,
      'admin_tel' :  memAdmin.admin_tel_no,
    })  
  if flag[:3]=="vat":
    strsql_f = "SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = 'C17'"#c17은 고정임 수정말 것
    with connection.cursor() as cursor:
      cursor.execute(strsql_f, (memuser.biz_no, work_yy+"년 "+strKi+"기"))
      result_f = cursor.fetchall()
    connection.commit()     
    
    napbuDate = napbuDate2 = "조회일 ";workPeriod2 = "작성일자 >='";titlePeriod=work_yy+"년 ";titlePeriod2=work_yy+"년 "
    if   work_mm=="1": 
      txtSKGB = "1기예정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-01-31'";napbuDate += work_yy+"년 2월 10일";napbuDate2 += work_yy+"년 2월 15일"
      titlePeriod +="1월 1일부터 1월 31일";titlePeriod2=str(int(work_yy)-1)+"년 1월 1일부터 1월 31일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}01'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0131'"
    elif work_mm=="2": 
      txtSKGB = "1기예정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-02-28'";napbuDate += work_yy+"년 3월 10일";napbuDate2 += work_yy+"년 3월 15일"
      titlePeriod +="1월 1일부터 2월 28일";titlePeriod2 +="1월 1일부터 2월 28일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}02'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0229'"
    elif work_mm=="3": 
      txtSKGB = "1기예정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-03-31'";napbuDate += work_yy+"년 4월 10일";napbuDate2 += work_yy+"년 4월 15일"
      titlePeriod +="1월 1일부터 3월 31일";titlePeriod2 +="1월 1일부터 3월 31일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}03'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0331'"
    elif work_mm=="7": 
      txtSKGB = "2기예정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-07-31'";napbuDate += work_yy+"년 8월 10일";napbuDate2 += work_yy+"년 8월 15일"
      titlePeriod +="7월 1일부터 7월 31일";titlePeriod2 +="6월 1일부터 6월 30일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}07'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}0731'"
    elif work_mm=="8": 
      txtSKGB = "2기예정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-08-31'";napbuDate += work_yy+"년 9월 10일";napbuDate2 += work_yy+"년 9월 15일"
      titlePeriod +="7월 1일부터 8월 31일";titlePeriod2 +="7월 1일부터 7월 31일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}08'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}0831'"
    elif work_mm=="9": 
      txtSKGB = "2기예정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-09-30'";napbuDate += work_yy+"년 10월 10일";napbuDate2 += work_yy+"년 10월 15일"
      titlePeriod +="7월 1일부터 9월 30일";titlePeriod2 +="7월 1일부터 8월 31일";      
      cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}09'"
      cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}0930'"
    elif work_mm=="4": 
      if result_f:
        txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-04-01' and 작성일자<='"+str(work_yy)+"-04-30'";napbuDate += work_yy+"년 5월 10일";napbuDate2 += work_yy+"년 5월 15일"
        titlePeriod +="4월 1일부터 4월 30일";titlePeriod2 +="3월 1일부터 3월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}04' and Tran_MM<='{work_yy}04'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0401' and Tran_Dt<='{work_yy}0430'"
      else:
        work_qt=5;txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-04-30'";napbuDate += work_yy+"년 5월 10일";napbuDate2 += work_yy+"년 5월 15일"
        titlePeriod +="1월 1일부터 4월 30일";titlePeriod2 +="1월 1일부터 3월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}04'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0430'"
    elif work_mm=="5": 
      if result_f:
        txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-04-01' and 작성일자<='"+str(work_yy)+"-05-31'";napbuDate += work_yy+"년 6월 10일";napbuDate2 += work_yy+"년 6월 15일"
        titlePeriod +="4월 1일부터 5월 31일";titlePeriod2 +="4월 1일부터 5월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}04' and Tran_MM<='{work_yy}05'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0401' and Tran_Dt<='{work_yy}0531'"
      else:
        work_qt=5;txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-05-31'" ;napbuDate += work_yy+"년 6월 10일";napbuDate2 += work_yy+"년 6월 15일"       
        titlePeriod +="1월 1일부터 5월 31일";titlePeriod2 +="1월 1일부터 5월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}05'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0531'"
    elif work_mm=="6": 
      if result_f:
        txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-04-01' and 작성일자<='"+str(work_yy)+"-06-30'";napbuDate += work_yy+"년 7월 10일";napbuDate2 += work_yy+"년 7월 15일"
        titlePeriod +="4월 1일부터 6월 30일";titlePeriod2 +="4월 1일부터 6월 30일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}04' and Tran_MM<='{work_yy}06'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0401' and Tran_Dt<='{work_yy}0630'"
      else:
        work_qt=5;txtSKGB = "1기확정";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-06-30'";napbuDate += work_yy+"년 7월 10일";napbuDate2 += work_yy+"년 7월 15일"
        titlePeriod +="1월 1일부터 6월 30일";titlePeriod2 +="1월 1일부터 6월 30일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}01' and Tran_MM<='{work_yy}06'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0101' and Tran_Dt<='{work_yy}0630'"
    elif work_mm=="10": 
      if result_f:
        txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-10-01' and 작성일자<='"+str(work_yy)+"-10-31'";napbuDate += work_yy+"년 11월 10일";napbuDate2 += work_yy+"년 11월 15일"
        titlePeriod +="10월 1일부터 10월 31일";titlePeriod2 +="9월 1일부터 9월 30일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}10' and Tran_MM<='{work_yy}10'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}1001' and Tran_Dt<='{work_yy}1031'"
      else:
        work_qt=6;txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-10-31'";napbuDate += work_yy+"년 11월 10일";napbuDate2 += work_yy+"년 11월 15일"      
        titlePeriod +="7월 1일부터 10월 31일";titlePeriod2 +="7월 1일부터 10월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}10'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}1031'"
    elif work_mm=="11": 
      if result_f:
        txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-10-01' and 작성일자<='"+str(work_yy)+"-11-30'";napbuDate += work_yy+"년 12월 10일";napbuDate2 += work_yy+"년 12월 15일"
        titlePeriod +="10월 1일부터 11월 30일";titlePeriod2 +="10월 1일부터 11월 30일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}10' and Tran_MM<='{work_yy}11'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}1001' and Tran_Dt<='{work_yy}1130'"
      else:
        work_qt=6;txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-11-30'";napbuDate += work_yy+"년 12월 10일";napbuDate2 += work_yy+"년 12월 15일"          
        titlePeriod +="7월 1일부터 11월 30일";titlePeriod2 +="7월 1일부터 11월 30일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}11'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}1130'"
    elif work_mm=="12": 
      if result_f:
        txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-10-01' and 작성일자<='"+str(work_yy)+"-12-31'";napbuDate += str(int(work_yy)+1)+"년 1월 10일";napbuDate2 += str(int(work_yy)+1)+"년 1월 15일"
        titlePeriod +="10월 1일부터 12월 31일";titlePeriod2 +="10월 1일부터 12월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}10' and Tran_MM<='{work_yy}12'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}1001' and Tran_Dt<='{work_yy}1231'"
      else:
        work_qt=6;txtSKGB = "2기확정";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-12-31'";napbuDate += str(int(work_yy)+1)+"년 1월 10일";napbuDate2 += str(int(work_yy)+1)+"년 1월 15일"          
        titlePeriod +="7월 1일부터 12월 31일";titlePeriod2 +="7월 1일부터 12월 31일";        
        cardSalePeriod = f"Tran_MM>='{work_yy}07' and Tran_MM<='{work_yy}12'"
        cardCostPeriod = f"Tran_Dt>='{work_yy}0701' and Tran_Dt<='{work_yy}1231'"

    context.update({
      "titlePeriod" : titlePeriod,
      "napbuDate2": napbuDate2,
    })

  templateMenu =""
  if flag == 'vatNtsHelp' or flag=='kjReport' or flag=='fProof':
    templateMenu = 'kakao/pdfViewer.html';
    fileName = getFileName(flag,memuser,work_yy,work_qt,txtSKGB)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})  
  elif flag == "vatAnaly":
    templateMenu = 'kakao/vatAnaly.html'; 
  elif flag == 'vatElec':
    templateMenu = 'kakao/vatElec.html'; 
    context = vatElecList(context,txtSKGB,workPeriod2,cardSalePeriod,cardCostPeriod)
  elif flag == 'vatResultSummit':#부가세 신고결과
    templateMenu = 'kakao/vatResultSummit.html'; 
    context.update({
       "totalWidth": 370,
        "txtfontFamily": "Roboto, Helvetica, Arial, Tahoma, Verdana, sans-serif;",
        "coverBGColor": "#ffffff",
        "titleColor": "#ffffff",
        "navi3pxBottom": "border-bottom-color:#004c6c; border-bottom-style:solid; border-bottom-width:2px;",
        "navi1pxBottom": "border-bottom-color:#004c6c; border-bottom-style:solid; border-bottom-width:0.5px;",
        "navi1pxRight": "border-right-color:#004c6c; border-right-style:solid; border-right-width:0.5px;",
    })
    context = vatResult(context,flag)  
  elif flag == 'vatResultJupsu':#부가세 신고 접수증
    templateMenu = 'kakao/vatResultJupsu.html';   
    context.update({
       "totalWidth": 400,
        "txtfontFamily": "Roboto, Helvetica, Arial, Tahoma, Verdana, sans-serif;",
        "coverBGColor": "#ffffff",
        "titleColor": "#ffffff",
        "navi3pxBottom": "border-bottom-color:#004c6c; border-bottom-style:solid; border-bottom-width:2px;",
        "navi1pxBottom": "border-bottom-color:#004c6c; border-bottom-style:solid; border-bottom-width:0.5px;",
        "navi1pxRight": "border-right-color:#004c6c; border-right-style:solid; border-right-width:0.5px;",
    })
    context = vatResult(context,flag)
  elif flag == 'vatResultNapbu' or flag == 'VatPrepay':#부가세 납부서 / 예정고지
    fileName = getFileName(flag,memuser,work_yy,work_qt,txtSKGB)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})     
  elif flag == "Card":
    templateMenu = 'kakao/vatCard.html';
    context = vatCardList(context)
  elif flag == "goji":  
    templateMenu = 'kakao/index.html';
    getMailContent(context)          
  elif flag == "CorpIntro"  or  flag == "CorpFeeRule":
    fileName = getFileName(flag,memuser,work_yy,work_MM,"")
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})
  elif flag == "CorpResult" or  flag == "CorpFee":  
    templateMenu = 'kakao/index.html';
    getMailContent(context)       
  elif flag == "CorpSummit":  
    fileName = getMultiPDFtoImgFileName(flag,memuser,work_yy,work_mm)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})    
  elif flag == "CorpNapbuseo":  
    fileName = getMultiPDFtoImgFileName(flag,memuser,work_yy,work_mm)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})      
  elif flag == "paysheet" or flag == "paynapbu" :
    fileName = getMultiPDFtoImgFileName(flag,memuser,work_yy,work_mm)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})    
  return render(request, templateMenu,context)

def taxGojiList(context):
  seq_no = context.get("seq_no")
  work_yy = context.get("work_yy")
  work_mm = context.get("work_mm")  

  admin = MemAdmin.objects.filter(
      admin_id=Subquery(
          MemDeal.objects.filter(seq_no=seq_no).values('biz_manager')[:1]
      )
  ).values('admin_name', 'admin_tel_no','admin_email').first()
  recordset_member = MemUser.objects.filter(seq_no=seq_no).values('biz_name','email','biz_no','ceo_name','hp_no').first()
  recordset_adminInfo = {
    'admin_name': admin['admin_name'],
    'admin_tel_no': admin['admin_tel_no'],
    'admin_email': admin['admin_email'],
    "TXT_CorpName"  : '세무법인대승',
    "TXT_DutyCTA"  : '김기현',
    "TXT_DutyCTAHP" : '010-9349-7120',
    "TXT_OfficeAddress"  : '서울특별시 강남구 강남대로84길 15, 206호(역삼동, 강남역효성해링턴타워더퍼스트)'
  }
  sql = ("select taxMok,taxAmt,taxNapbuNum,taxOffice,taxDuedate from tbl_goji  "
              "WHERE seq_no=%s AND work_yy=%s AND work_mm=%s ")  
  recordset = fetch_results(sql, (seq_no, work_yy,work_mm))
  print(recordset)
  context.update({
    "tax_data": recordset,
    "recordset_member":recordset_member,
    "recordset_adminInfo":recordset_adminInfo
  })  
  return context

def vatResult(context,flag):
  seq_no = context.get("seq_no")
  work_yy = context.get("work_yy")
  work_qt = context.get("work_qt")
  work_mm = int(context.get("work_mm"))
  memuser = MemUser.objects.get(seq_no=seq_no)
  memdeal = MemDeal.objects.get(seq_no=seq_no)

  def is_leap_year(year: int) -> bool:
      """윤년 판정 (정확한 그레고리력 규칙)"""
      return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
  wcWhanKB = ""
  if work_mm in (4, 10):
      wcCorpGB_txt = "C05"
      wcJong = "부가가치세 확정(일반) 4,10월조기 신고서"
      wcWhanKB = "시설투자환급"
      if work_mm == 4:
          txtPeriod = f"{work_yy}년 4월 1일 ~ 4월 30일"
      else:
          txtPeriod = f"{work_yy}년 10월 1일 ~ 10월 31일"
  # 5, 11월 조기 신고서
  elif work_mm in (5, 11):
      wcCorpGB_txt = "C06"
      wcJong = "부가가치세 확정(일반) 5,11월조기 신고서"
      wcWhanKB = "시설투자환급"
      if work_mm == 5:
          txtPeriod = f"{work_yy}년 5월 1일 ~ 5월 31일"
      else:
          txtPeriod = f"{work_yy}년 11월 1일 ~ 11월 30일"
  # 확정 신고서 (6, 12월)
  elif work_mm in (6, 12):
      wcCorpGB_txt = "C07"
      wcJong = "부가가치세 확정(일반) 신고서"
      if memdeal.biz_manager != "오피스텔":
          if memuser.biz_type >= 4:
              # 법인/일반 등: 반기 기준
              if work_mm == 6:
                  txtPeriod = f"{work_yy}년 1월 1일 ~ 6월 30일"
              else:
                  txtPeriod = f"{work_yy}년 7월 1일 ~ 12월 31일"
          else:
              # 간이/기타 구분: 분기 일부
              if work_mm == 6:
                  txtPeriod = f"{work_yy}년 4월 1일 ~ 6월 30일"
              else:
                  txtPeriod = f"{work_yy}년 10월 1일 ~ 12월 31일"
      else:
          # 오피스텔 특례: 월 단위
          if work_mm == 6:
              txtPeriod = f"{work_yy}년 6월 1일 ~ 6월 30일"
          else:
              txtPeriod = f"{work_yy}년 12월 1일 ~ 12월 31일"
  # 예정 조기 신고서 (1, 7월)
  elif work_mm in (1, 7):
      wcCorpGB_txt = "C15"
      wcJong = "부가가치세 예정(일반) 1,7월조기 신고서"
      wcWhanKB = "시설투자환급"
      if work_mm == 1:
          txtPeriod = f"{work_yy}년 1월 1일 ~ 1월 31일"
      else:
          txtPeriod = f"{work_yy}년 7월 1일 ~ 7월 31일"
  # 예정 조기 신고서 (2, 8월) — 2월은 윤년 처리
  elif work_mm in (2, 8):
      wcCorpGB_txt = "C16"
      wcJong = "부가가치세 예정(일반) 2,8월조기 신고서"
      wcWhanKB = "시설투자환급"
      if work_mm == 2:
          last_day = 29 if is_leap_year(work_yy) else 28
          txtPeriod = f"{work_yy}년 2월 1일 ~ 2월 {last_day}일"
      else:
          txtPeriod = f"{work_yy}년 8월 1일 ~ 8월 31일"
  # 예정 신고서 (3, 9월)
  elif work_mm in (3, 9):
      wcCorpGB_txt = "C17"
      wcJong = "부가가치세 예정(일반) 신고서"
      if memdeal.biz_manager != "오피스텔":
          if work_mm == 3:
              txtPeriod = f"{work_yy}년 1월 1일 ~ 3월 31일"
          else:
              txtPeriod = f"{work_yy}년 7월 1일 ~ 9월 30일"
      else:
          if work_mm == 3:
              txtPeriod = f"{work_yy}년 3월 1일 ~ 3월 31일"
          else:
              txtPeriod = f"{work_yy}년 9월 1일 ~ 9월 30일"

  if flag=="vatResultJupsu":
    strsql = f"""
      select 신고시각,과세기간,신고구분,신고번호,접수여부,과세유형,환급구분,환급구분코드,과세표준금액,차감납부할세액 from 부가가치세전자신고3   
      where 사업자등록번호='{memuser.biz_no}' 
      and left(과세기간,4)={work_yy}
      and 과세유형='{wcCorpGB_txt}'
    """
    # print(strsql)
    with connection.cursor() as cursor:
        cursor.execute(strsql)
        r = cursor.fetchone()
    if not r:
        return None

    신고시각 = r[0] or ""
    과세기간 = r[1] or ""
    신고구분 = r[2] or ""
    신고번호 = r[3] or ""
    접수여부 = r[4]  # 필요시 사용
    과세유형 = wcJong#r[5] or ""         # 코드 (예: C05)
    환급구분 = r[6] or ""
    # 환급구분코드 = r[7]          # 필요시 사용
    과세표준금액 = r[8] or 0
    차감납부할세액 = r[9] or 0
    tmpDesc = f"{신고구분} / {환급구분}"

    context.update({
        "majorBizName": memuser.biz_name,
        "majorBizNo": memuser.biz_no,
        "majorFlag": wcJong,            # 신고서종류
        "majorIssue": 접수여부,          # 접수방법
        "majorChumbu": "2종",        # 첨부서류 몇종
        "majorDesc": tmpDesc,              # 신고구분(설명)
        "major0": 과세기간,                 # 신고년기
        "major1": txtPeriod,               # 신고기간(계산값)
        "major2": 과세유형,                 # 과세유형(코드)  <-- 기존 r[10] 오류 수정
        "major3": 환급구분,                 # 환급구분
        "major4": 과세표준금액,             # 과세표준
        "major5": 차감납부할세액,           # 차가감납부세액
        "majorNum": 신고번호,               # 접수번호
        "majorDate": 신고시각            # 접수일시
    })
  else:

    sql = """
    SELECT TOP 1
        *,
        (매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액) AS 매출세금계산서,
        (매출과세세금계산서발급세액 + 매출과세매입자발행세금계산서세액 + 예정누락매출세금계산서세액) AS 매출세금계산서세액,
        (매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액) AS 기타매출,
        (매출과세카드현금발행세액 + 매출과세기타세액 + 예정누락매출과세기타세액) AS 기타매출세액,
        (매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액) AS 영세율매출,
        (매입세금계산서수취일반금액 + 매입세금계산서수취고정자산금액 + 예정누락매입신고세금계산서금액 + 매입자발행세금계산서매입금액) AS 매입세금계산서,
        (매입세금계산서수취일반세액 + 매입세금계산서수취고정자산세액 + 예정누락매입신고세금계산서세액 + 매입자발행세금계산서매입세액) AS 매입세금계산서세액,
        그밖의공제매입명세합계금액 AS 기타매입,
        그밖의공제매입명세합계세액 AS 기타매입세액,
        공제받지못할매입합계금액     AS 불공제,
        공제받지못할매입합계세액     AS 불공제세액,
        경감공제합계세액             AS 경감공제세액,
        면세사업합계수입금액         AS 면세매출,
        계산서수취금액               AS 면세매입,
        차감납부할세액               AS 실제납부할세액
    FROM [부가가치세전자신고3]
    WHERE 사업자등록번호 = %s
      AND LEFT(과세기간, 4) = %s
      AND 과세유형 = %s
    ORDER BY 과세기간 DESC, 신고구분 DESC, 신고시각 DESC, 과세유형 ASC;
    """

    with connection.cursor() as cursor:
        cursor.execute(sql, [memuser.biz_no, work_yy, wcCorpGB_txt])
        rs1 = dictfetchone(cursor) or {}
    면세합계 = rs1.get("매입세금계산서", 0) + rs1.get("기타매입", 0) + rs1.get("면세매입", 0)
    context = {
        "biz_name": memuser.biz_name,
        "work_mm": work_mm,
        "rs1": rs1,
        "면세합계": 면세합계
    }     
  return context

def vatCardList(context):
  seq_no = context.get("seq_no")
  work_yy = context.get("work_yy")
  work_qt = context.get("work_qt")
  Htx_TotSum_ddct = Htx_CntSum_ddct = Htx_TotSum_Nddct = Htx_CntSum_Nddct= 0
  issue_TotSum_ddct = issue_CntSum_ddct = issue_TotSum_Nddct = issue_CntSum_Nddct = 0

  if int(work_qt)==1  :workPeriod = "stnd_GB = '1' "
  elif int(work_qt)==2:workPeriod = "stnd_GB = '2' "
  elif int(work_qt)==3:workPeriod = "stnd_GB = '3' "
  elif int(work_qt)==4:workPeriod = "stnd_GB = '4' "
  elif int(work_qt)==5:workPeriod = "stnd_GB in ('1','2') "
  elif int(work_qt)==6:workPeriod = "stnd_GB in ('3','4') "
  str_card = f"select ddcYnNm,File_DdctGB,totaTrsAmt from tbl_hometax_scrap where seq_no='{seq_no}' and tran_yy={work_yy} and {workPeriod}"
  with connection.cursor() as cursor:
      cursor.execute(str_card)
      results = cursor.fetchall()
  connection.commit()
  if results:
    for rs_r in results:
      if rs_r[0].strip() == "공제":        Htx_TotSum_ddct += int(rs_r[2]);        Htx_CntSum_ddct += 1
      elif rs_r[0].strip() == "불공제":    Htx_TotSum_Nddct += int(rs_r[2]);       Htx_CntSum_Nddct += 1
      if rs_r[1].strip() == "공제":        issue_TotSum_ddct += int(rs_r[2]);      issue_CntSum_ddct += 1
      elif rs_r[1].strip() == "불공제":    issue_TotSum_Nddct += int(rs_r[2]);     issue_CntSum_Nddct += 1

    diff_TotSum_Tot = issue_TotSum_ddct - Htx_TotSum_ddct
    diff_CntSum_Tot = issue_CntSum_ddct - Htx_CntSum_ddct 

    context.update({
      "Htx_TotSum_ddct": Htx_TotSum_ddct,
      "Htx_CntSum_ddct": Htx_CntSum_ddct,
      "Htx_TotSum_Nddct": Htx_TotSum_Nddct,
      "Htx_CntSum_Nddct": Htx_CntSum_Nddct,
      "issue_TotSum_ddct": issue_TotSum_ddct,
      "issue_CntSum_ddct": issue_CntSum_ddct,
      "issue_TotSum_Nddct": issue_TotSum_Nddct,
      "issue_CntSum_Nddct": issue_CntSum_Nddct,
      "diff_TotSum_Tot": diff_TotSum_Tot,
      "diff_CntSum_Tot": diff_CntSum_Tot,
      "TotalSum": Htx_TotSum_ddct + Htx_TotSum_Nddct,
      "commentCard" : "조회일까지 취합된 자료이며 카드사용내역은 1개월 후 확인됩니다. 카드공제는 사용처에 따라 불공제로 재분류될 수 있습니다."
    })
  return context

def vatElecList(context,txtSKGB,workPeriod2,cardSalePeriod,cardCostPeriod):
  seq_no = context.get("seq_no")
  work_yy = context.get("work_yy")
  work_qt = context.get("work_qt")
  memuser = MemUser.objects.get(seq_no=seq_no)
  memdeal = MemDeal.objects.get(seq_no=seq_no)

  tax1 = 0;tax2 = 0;tax3 = 0;tax4 = 0;tax5 = 0;tax6 = 0;tax7 = 0;tax8=0;tax9 = 0;tax10 = 0;tax11=0;tax12=0;taxResult=0
  kkke1 = 0;kkke2=0;kkke3=0;kkke4=0;kkke5 = 0;kkke6 = 0;    kkke7=0;kkke8=0;kkke9=0;kkke10=0;kkke11=0;kkke12=0;

  strsql = "Select 매입매출구분,sum(공급가액),sum(세액),sum(합계금액) from 전자세금계산서 	 "                    
  strsql += "WHERE 사업자번호='"+memuser.biz_no+"'  and  "+workPeriod2+"   group by 매입매출구분 ";print(strsql)
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  for r in result:
    if r[0]=='1':kkke1 = r[1];tax1=r[2];print(r[0])
    elif r[0]=='2':kkke2 = r[1];tax2=r[2]
    elif r[0]=='3':kkke3 = r[1]
    elif r[0]=='4':kkke4 = r[1]

  strsql = "Select 매입매출구분,sum(공급가액),sum(세액),sum(합계금액) from 전자세금계산서 	 "                    
  strsql += "WHERE 사업자번호='"+memuser.biz_no+"'  and  "+workPeriod2+" and  매입매출구분=2 "
  strsql += " and (공급자상호 like '%자동차%' or 공급자상호 like '%모터스%')  group by 매입매출구분";print(strsql)
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  for r in result:
    if str(r[0])=='2':tax10=r[2];print(f'tax10:{tax10}')

  kwasekisu = work_yy+"년 " + txtSKGB[:2]
  # if SKGB:#스크래핑(분기)에서 팝업 띄우는 경우
  #   str_nm = "select 예정고지세액일반,예정미환급세액일반,예정부과세액간이,예정신고세액간이,매입자납부특례기납부세액"
  #   str_nm += " ,매출신용카드공급가액,매출신용카드세액, 매출현금영수증공급가액, 매출현금영수증세액"
  #   str_nm += " , 매입신용카드공급가액, 매입신용카드세액, 매입현금영수증공급가액, 매입현금영수증세액, 매입복지카드공급가액, 매입복지카드세액"
  #   str_nm += " , 매출전자세금계산서공급가액,매출전자세금계산서세액,매출전자계산서공급가액"
  #   str_nm += " , 매입전자세금계산서공급가액,매입전자세금계산서세액,매입전자계산서공급가액"
  #   str_nm += " from 부가가치세통합조회 where 과세기수='"+kwasekisu+"' and 신고구분='"+txtSKGB[-2:]+"' and 사업자등록번호='"+memuser.biz_no+"'" 
  #   with connection.cursor() as cursor:
  #       cursor.execute(str_nm)
  #       result = cursor.fetchall()
  #   connection.commit()
  #   if result:
  #     tax8 = (result[0][0]) - (result[0][1]) + (result[0][4])                                 #예정세액
  #     tax5 = int(Decimal(result[0][5]) / Decimal('1.1') * Decimal('0.1')) + result[0][8]
  #     kkke5 = result[0][5] + result[0][7]
  #     tax6 = result[0][10] + result[0][12]
  #     kkke6 = result[0][9] + result[0][11]  
  # else:#스크래핑(월별)에서 팝업 띄우는 경우
  str_5 = f"select isnull(sum(Tot_StlAmt),0),isnull(sum(Etc_StlAmt),0),isnull(sum(PurcEuCardAmt),0) from Tbl_HomeTax_SaleCard where  Seq_No='{memuser.seq_no}'  and {cardSalePeriod}";print(str_5)
  with connection.cursor() as cursor:
      cursor.execute(str_5)
      result = cursor.fetchall()
  connection.commit()
  if result and result[0]:
    tax5 = int(Decimal(result[0][0]) / Decimal('1.1') * Decimal('0.1'))
    kkke5 = int(Decimal(result[0][0]) / Decimal('1.1'))
  str_6 = f"select isnull(sum(totaTrsAmt),0), isnull(sum(splCft),0), isnull(sum(vaTxamt),0) from tbl_hometax_scrap where  Seq_No='{memuser.seq_no}'  and {cardCostPeriod} and File_DdctGB in ('공제','Y')";print(str_6)
  with connection.cursor() as cursor:
      cursor.execute(str_6)
      result = cursor.fetchall()
  connection.commit()
  if result and result[0]:
    tax6 = result[0][2]
    kkke6 = result[0][1]
  str_7 = f"select isnull(sum(totaTrsAmt),0), isnull(sum(splCft),0), isnull(sum(vaTxamt),0) from Tbl_HomeTax_CashCost where  Seq_No='{memuser.seq_no}'  and {cardCostPeriod} and File_DdctGB in ('공제','Y')";print(str_7)
  with connection.cursor() as cursor:
      cursor.execute(str_7)
      result = cursor.fetchall()
  connection.commit()
  if result and result[0]:
    tax6 = int(tax6) + int(result[0][2])
    kkke6 = int(kkke6) + int(result[0][1])
  if int(work_qt)==1  :workPeriod = "work_qt = '1' "
  elif int(work_qt)==2:workPeriod = "work_qt = '2' "
  elif int(work_qt)==3:workPeriod = "work_qt = '3' "
  elif int(work_qt)==4:workPeriod = "work_qt = '4' "
  elif int(work_qt)==5:workPeriod = "work_qt = '2' "
  elif int(work_qt)==6:workPeriod = "work_qt = '4' "
  str_8 = f"select yn_15 from tbl_vat where seq_no={memuser.seq_no} and work_yy={work_yy} and {workPeriod}";print(str_8)
  with connection.cursor() as cursor:
      cursor.execute(str_8)
      result = cursor.fetchall()
  connection.commit()
  if result:
    tax8 = result[0][0]
      
  if memuser.uptae[:2]=='음식':
    if memuser.biz_type<4:tax9 = int(kkke4*6/106)
    else:tax9 = int(kkke4*9/109)
  taxResult = tax1 - tax2 + tax5 - tax6 - tax9 - tax8 + tax10;

  context.update({
    "tax1": tax1,
    "tax2": tax2,
    "tax5": tax5,
    "tax6": tax6,
    "tax8": tax8,
    "tax9": tax9,
    "tax10": tax10,
    "kkke1": kkke1,
    "kkke2": kkke2,
    "kkke3": kkke3,
    "kkke4": kkke4,
    "kkke5": kkke5,
    "kkke6": kkke6,
    "taxResult": taxResult,
    "comment" : "현재까지 취합된 자료를 기준으로 계산된 예상 부가세액이며 서면자료 및 불공제매입, 공제한도 등으로 실제 신고금액과 다를 수 있습니다."
  })
  return context

def kakao_view(request):

  flag = request.GET.get('flag')
  sflag = request.GET.get('s')
  sqno = request.GET.get('seq')
  work_yy = request.GET.get('work_yy')
  work_mm = request.GET.get('work_mm')
  # today  = datetime.now().day
  # if today<13:work_mm = str(int(work_mm) -1)
  work_qt = request.GET.get('work_qt')
  SKGB = request.GET.get('SKGB') ########################## 스크래핑(HTX) - 분기별인 경우 값이 나온다, 월별인 경우는 work_mm으로 구분
  if sflag:
    sqno = int(sflag[4:9])
    work_yy = str(int(sflag[9:12]) + 2000)
    work_mm = str(int(sflag[12:14]))
    work_qt = sflag[14:15]
    rcv_semok = sflag[15]
    SKGB = sflag[18:21].replace("0", "")
  memuser = MemUser.objects.get(seq_no=sqno)
  txtSKGB="";napbuDate = napbuDate2 = "납부기한 ";cardSalePeriod = cardCostPeriod = "";workPeriod2 = "작성일자 >='";titlePeriod=work_yy+"년 ";titlePeriod2=work_yy+"년 "
  commentCard = ""
  comment = "현재까지 취합된 자료를 기준으로 계산된 예상 부가세액이며 서면자료 및 불공제매입, 공제한도 등으로 실제 신고금액과 다를 수 있습니다."

  if work_qt=="" or work_qt==None:
    if int(work_mm) <= 3:        work_qt = "1"
    elif int(work_mm) <= 6:      work_qt = "2"
    elif int(work_mm) <= 9:      work_qt = "3"
    elif int(work_mm) <= 12:     work_qt = "4"
  
  strKi = "1"
  if int(work_qt)> 2:strKi = "2"
  strsql_f = "SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = 'C17'"#c17은 고정임 수정말 것
  with connection.cursor() as cursor:
    cursor.execute(strsql_f, (memuser.biz_no, work_yy+"년 "+strKi+"기"))
    result_f = cursor.fetchall()
  connection.commit()     
  if SKGB:#부가세 신고기간에 보내는 경우
    if      work_qt == "1" :     
      txtSKGB = "1기예정";napbuDate += work_yy+"년 4월 25일"; titlePeriod +="1월 1일부터 3월 31일"; titlePeriod2 +="1월 1일부터 3월 31일";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-03-31'"
    elif    work_qt == "2":    
      txtSKGB = "1기확정"
      if result_f: titlePeriod +="4월 1일부터 6월 30일";titlePeriod2 +="4월 1일부터 6월 30일";napbuDate += work_yy+"년 7월 25일";workPeriod2 += str(work_yy)+"-04-01' and 작성일자<='"+str(work_yy)+"-06-30'"
      else        :titlePeriod +="1월 1일부터 6월 30일";titlePeriod2 +="1월 1일부터 6월 30일";napbuDate += work_yy+"년 7월 25일";workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-06-30'"       
    elif    work_qt == "3":      
      txtSKGB = "2기예정";titlePeriod +="7월 1일부터 9월 30일";titlePeriod2 +="7월 1일부터 9월 30일";napbuDate += work_yy+"년 10월 25일";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-09-30'"
    elif    work_qt == "4":      
      txtSKGB = "2기확정"
      if result_f: titlePeriod +="10월 1일부터 12월 31일";titlePeriod2 +="10월 1일부터 12월 31일";napbuDate += str(int(work_yy)+1)+"년 1월 25일";workPeriod2 += str(work_yy)+"-10-01' and 작성일자<='"+str(work_yy)+"-12-31'"
      else        :titlePeriod +="7월 1일부터 12월 31일" ;titlePeriod2 +="7월 1일부터 12월 31일" ;napbuDate += str(int(work_yy)+1)+"년 1월 25일";workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-12-31'"
  
  context = {}
  # =============================================================================== vatAnaly
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if memuser.biz_type<4:
      context['isCorp'] = True
  if userprofile:
      userprofile = userprofile.latest('description')
  if userprofile is not None:
      context['userProfile'] = userprofile
  
  context['memuser'] = memuser
  context['work_yy'] = work_yy
  context['work_mm'] = work_mm
  context['work_qt'] = work_qt
  context['titlePeriod'] = titlePeriod
  context['napbuDate'] = napbuDate
  context['comment'] = comment

  getTotalIssueList(memuser,context)

  if flag == 'vatNtsHelp' or flag=='kjReport' or flag=='fProof':
    fileName = getFileName(flag,memuser,work_yy,work_qt,txtSKGB)
    return render(request, 'kakao/pdfViewer.html', {'fileName': fileName})
  elif flag == 'vatAnaly':
    return render(request, 'kakao/vatAnaly.html', context)
  elif flag == 'vatElec':
    return render(request, 'kakao/vatElec.html', context)
  elif flag=='Card':
    return render(request, 'kakao/vatCard.html', context)

#PDF만 보여주는 카톡 웹링크
def getFileName(flag,memuser,work_yy,work_qt,txtSKGB):
  memdeal = MemDeal.objects.get(seq_no=memuser.seq_no)
  if work_qt==5:
    work_qt=2
  elif work_qt==6:
    work_qt=4
  print(work_yy)
  print(work_qt)
  print(txtSKGB)
  fiscalMM = memdeal.fiscalmm
  if len(fiscalMM)==1 : fiscalMM = "0"+fiscalMM
  root_dir = 'static/cert_DS/'+memuser.biz_name
  totalFileName = f"{root_dir}/{work_yy}"
  if flag == 'vatNtsHelp':
    totalFileName +=  f"/부가세/{txtSKGB}/300.pdf" 
  elif flag=='vatResultNapbu':
    totalFileName +=  f"/부가세/{txtSKGB}/200.pdf" 
  elif flag=='kjReport':
    totalFileName +=  f"/기장보고서/{work_qt}분기/300.pdf" 
  elif flag=='fProof':
    totalFileName +=  f"/홈택스민원서류/표준재무제표증명원({(int(work_yy)-1)}{fiscalMM}).pdf" 
  elif flag=='CorpIntro':
    totalFileName +=  f"/세무조정계산서/98.pdf" 
  elif flag=='CorpFeeRule':
    totalFileName =  "static/cert_DS/AAA/보수청구서/보수기준_세무조정료.pdf"     
  FRAMES = []
  FIRST_SIZE = None
  print(totalFileName)
  pureFilewithext = list(reversed(totalFileName.split('/')))[0]
  fileNameWithoutExt = pureFilewithext.split('.')[0]
  pathName = totalFileName.replace(pureFilewithext,"")
  if "jpg" in totalFileName or "png" in totalFileName:
    return totalFileName
  elif "pdf" in totalFileName:
    fileName = "static/pdfImage/"+pathName.replace("/","@")+fileNameWithoutExt+".jpg"
    if not os.path.exists(fileName): 
      images = convert_from_path(totalFileName,poppler_path='C:\\poppler-22.04.0\\Library\\bin')
      y_sum=0
      x_size=0
      y_size=0
      for i,page in enumerate(images):
        page.save("static/pdf2Image/"+pathName.replace("/","##")+fileNameWithoutExt+"@"+str(i)+".jpg","JPEG")
        x_size = page.size[0] #원래 사이즈 1653
        y_size = page.size[1] #원래 사이즈 2339
        y_sum = y_sum + y_size

      filelist = glob.glob("static/pdf2Image/*.jpg")
      new_Image = Image.new("RGB",(x_size,y_sum),(256,256,256))
      for fn in natsort.natsorted(filelist):
        img = Image.open(fn)
        resized_file = img.resize((x_size,y_size))
        FRAMES.append(resized_file)

      for index in range(len(FRAMES)):
        area = (0,(index*y_size),x_size,y_size*(index+1))
        print ("Adding:", area)
        new_Image.paste(FRAMES[index],area)
      new_Image.save(fileName)

      [os.remove(f) for f in glob.glob("static/pdf2Image/*.jpg")]
    return  fileName  

#여러개의 PDF파일을 하나의 이미지파일로 합쳐서 리턴하기
def getMultiPDFtoImgFileName(flag, memuser, work_YY, work_MM):
    root_dir = f"static/cert_DS/{memuser.biz_name}"
    base_dir = f"{root_dir}/{work_YY}"
    totalFileNames = []
    LASTFOLDER = ""
    if flag == 'paysheet' or  flag == 'paynapbu': 
      LASTFOLDER = "인건비"
    elif flag=="CorpNapbuseo" or flag =="CorpSummit":
      LASTFOLDER = "세무조정계산서"
    
    folder_path = f"{base_dir}/{LASTFOLDER}/"
    os.makedirs(folder_path, exist_ok=True)
    if os.path.exists(folder_path):
        files = os.listdir(folder_path)
        if flag == 'paysheet':
            monthly_files = [
                os.path.join(folder_path, file) for file in files 
                if file.startswith(f"{work_MM}월") and  file.endswith("pdf") and "납부" not in file and "원천징수이행상황신고서" not in file
            ]
        elif flag == 'paynapbu':
            monthly_files = [
                os.path.join(folder_path, file) for file in files 
                if file.startswith(f"{work_MM}월") and  file.endswith("pdf") and "납부" in file
            ]
        elif flag == 'CorpSummit':
            monthly_files = [
                os.path.join(folder_path, file) for file in files 
                if any(sub in file for sub in ["198.pdf", "199.pdf"])
            ]    
        elif flag == 'CorpNapbuseo':
            monthly_files = [
                os.path.join(folder_path, file) for file in files 
                if any(sub in file for sub in ["200.pdf", "201.pdf","202.pdf", "203.pdf"])
            ]                     
        else:
            print(f"⚠️ 잘못된 flag 값: {flag}")
            return None
        totalFileNames.extend(monthly_files)

    if not totalFileNames:
        return None

    fileName = f"static/pdfImage/{folder_path.replace('/', '@')}{work_MM}{flag}_merged.jpg"
    if os.path.exists(fileName):
        return fileName

    FRAMES = []
    max_x_size, y_sum = 0, 0  # 최대 너비와 총 높이
    pdf_index = 0

    poppler_path = os.getenv("POPPLER_PATH", "C:\\poppler-22.04.0\\Library\\bin")
    for pdf_file in totalFileNames:
        if not os.path.exists(pdf_file):
            print(f"❌ PDF 파일 없음: {pdf_file}")
            continue
        
        print(f"📄 PDF 변환 중: {pdf_file}")
        try:
            images = convert_from_path(pdf_file, poppler_path=poppler_path)
        except Exception as e:
            print(f"⚠️ PDF 변환 실패: {pdf_file}, 오류: {e}")
            continue

        if not images:
            print(f"⚠️ 변환된 이미지가 없습니다: {pdf_file}")
            continue
        
        print(f"✅ 변환된 이미지 개수: {len(images)}개")

        for i, page in enumerate(images):
            img_path = f"static/pdf2Image/{folder_path.replace('/', '##')}@{pdf_index}_{i}.jpg"
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            page.save(img_path, "JPEG")

            if not os.path.exists(img_path):
                print(f"❌ 이미지 저장 실패: {img_path}")
                continue
            
            print(f"✅ 이미지 저장 완료: {img_path}")

            max_x_size = max(max_x_size, page.size[0])  # 최대 너비 갱신
            y_sum += page.size[1]
            FRAMES.append(img_path)
        pdf_index += 1

    if not FRAMES:
        print("❌ 최종 변환된 이미지가 없습니다.")
        return None

    # 최대 너비로 새 이미지 생성
    new_Image = Image.new("RGB", (max_x_size, y_sum), (255, 255, 255))  # 흰색 배경
    y_offset = 0

    for img_path in natsort.natsorted(FRAMES):
        if not os.path.exists(img_path):
            print(f"❌ 이미지 파일 없음 (스킵됨): {img_path}")
            continue

        with Image.open(img_path) as img:
            new_Image.paste(img, (0, y_offset))  # 왼쪽 정렬
            y_offset += img.size[1]
        
        try:
            os.remove(img_path)
        except OSError as e:
            print(f"⚠️ 파일 삭제 실패: {img_path}, 오류: {e}")

    os.makedirs(os.path.dirname(fileName), exist_ok=True)
    new_Image.save(fileName)
    print(f"✅ 최종 병합된 이미지 저장 완료: {fileName}")

    return fileName

def getTotalIssueList(memuser,context):

  sql = "  with STT As   "
  sql +=	  " (          " 
  sql +=	  " Select top 8 a.사업자등록번호, A.과세기간, LTRIM(a.과세유형) 과세유형 "

  if memuser.biz_type<4:
    sql +=	  "     ,  Sum(( CASE	WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' then "
    sql +=	  "							CASE when b.stnd_gb  = '1' then splCft else 0 end "
    sql +=	  "						WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' then "
    sql +=	  "							CASE when b.stnd_gb  = '2' then splCft else 0 end    "
    sql +=	  "						WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' then "
    sql +=	  "							CASE when b.stnd_gb  = '3' then splCft else 0 end    "
    sql +=	  "						WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' then "
    sql +=	  "							CASE when b.stnd_gb  = '4' then splCft else 0 end    "
    sql +=	  "						END  )) as 카드합계 "

  else:
    sql +=	  "     ,  Sum(( CASE   WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' then "
    sql +=	  "							CASE WHEN b.stnd_gb  = '1' or b.stnd_gb  = '2' then splCft else 0 end  "
    sql +=	  "						WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' then "
    sql +=	  "							CASE WHEN b.stnd_gb  = '3' or b.stnd_gb  = '4' then splCft else 0 end  "
    sql +=	  "						END  )) as 카드합계  "

                
  sql +=	  " From 부가가치세전자신고3  A WITH (NOLOCK)  "
  sql +=	  " LEFT OUTER JOIN  TBL_HOMETAX_SCRAP   B WITH (NOLOCK)  "
  sql +=	  "   ON a.사업자등록번호 = b.biz_no AND left(a.과세기간,4) = b.tran_YY   "
  sql +=	  "Where a.사업자등록번호 =  '" + memuser.biz_no + "'  And  a.과세유형<>''    " 

  if memuser.biz_type<4:
    sql +=	  "  And a.사업자등록번호 in ( Select biz_no From mem_user C WITH (NOLOCK) Where a.사업자등록번호 = c.biz_no And c.biz_type < 4 ) "
  else:
    sql +=	  "  And a.사업자등록번호 in ( Select biz_no From mem_user C WITH (NOLOCK) Where a.사업자등록번호 = c.biz_no And c.biz_type > 3 ) "

  sql +=	  " Group by a.사업자등록번호, a.과세기간, LTRIM(a.과세유형) order by a.과세기간 desc "
  sql +=	  "  )  "
  sql +=	  "     "
  sql +=	  " select top 8 "
  sql +=	  "   a.과세기간,a.과세유형 "
  sql +=	  " ,(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액) as 매출세금계산서      "
  sql +=	  " ,(매출과세세금계산서발급세액 + 매출과세매입자발행세금계산서세액 + 예정누락매출세금계산서세액) as 매출세금계산서세액  "
  sql +=	  " ,매출과세카드현금발행금액 as 카드매출     "
  sql +=	  " ,(매출과세기타금액 + 예정누락매출과세기타금액) as 기타매출     "  
  sql +=	  " ,(매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액) as 영세율매출     "
  sql +=	  " ,(매입세금계산서수취일반금액 + 매입세금계산서수취고정자산금액 + 예정누락매입신고세금계산서금액 + 매입자발행세금계산서매입금액) as 매입세금계산서    "  
  sql +=	  " ,(매입세금계산서수취일반세액 + 매입세금계산서수취고정자산세액 + 예정누락매입신고세금계산서세액 + 매입자발행세금계산서매입세액) as 매입세금계산서세액   "
  sql +=	  " ,그밖의공제매입명세합계금액 as 기타매입     "
  sql +=	  " ,그밖의공제매입명세합계세액 as 기타매입세액   "
  sql +=	  " ,공제받지못할매입합계금액 as 불공제   "
  sql +=	  " ,공제받지못할매입합계세액 as 불공제세액    "
  sql +=	  " ,경감공제합계세액 as 경감공제세액  ,면세사업합계수입금액 as 면세매출   "
  sql +=	  " ,계산서수취금액 as 면세매입  "
  sql +=	  " ,(차감납부할세액+매입자납부특례기납부세액) as 실제납부할세액   "
  sql +=	  " ,(예정신고미환급세액+예정고지세액) as 예정세액  ,매입세금계산서수취고정자산금액    "
  sql +=	  " ,과세표준금액 as 매출합계 ,매입세액합계금액 as 매입합계   "
  sql +=	  " ,신용카드수취기타카드,신용카드수취현금영수증,신용카드수취화물복지,신용카드수취사업용카드   "
  sql +=	  " ,공제받지못할매입세액명세,의제매입세액공제,재활용폐자원등매입세액  ,납부환급세액,매입세금계산서수취고정자산세액,산출세액,가산세액계  "
  sql +=	  " , 카드합계 as 카드현영사용총액    "
  sql +=	  "  from 부가가치세전자신고3 A , STT  B   "
  sql +=	  "   WHERE A.사업자등록번호 = B.사업자등록번호   "
  sql +=	  "  AND A.과세기간 = B.과세기간   "
  sql +=	  "  AND A.과세유형 = B.과세유형   "
  sql +=	  "  order by a.과세기간 desc, a.신고구분 desc,a.신고시각 desc, a.과세유형   "

  with connection.cursor() as cursor:
      cursor.execute(sql)
      result = cursor.fetchall()
  connection.commit()
  totalList = []
  if result:
    for r in result:
      wcCorpGB_txt=""
      if r[1] == "C03" :        wcCorpGB_txt = "확정"
      elif r[1] == "C07" :      wcCorpGB_txt = "확정"
      elif r[1] == "C13" :      wcCorpGB_txt = "예정"
      elif r[1] == "C17" :      wcCorpGB_txt = "예정"
      startDt="";endDt=""
      tmpKi = r[0][6:7];work_qt=""
      if   r[1] == "C03" :      startDt = "1월 1일";endDt="12월 31일"   #간이확정
      elif r[1] == "C13" :      startDt = "1월 1일";endDt="6월 30일" #간이 예정    
      elif r[1] == "C07" :      #확정
        if memuser.biz_type<4:
          if tmpKi=="1":  startDt = "4월 1일";endDt="6월 30일";work_qt="2"
          else:           startDt = "10월 1일";endDt="12월 31일";work_qt="4"
        elif  memuser.biz_type>=4:
          if tmpKi=="1":  startDt = "1월 1일";endDt="6월 30일";work_qt="2"
          else:           startDt = "7월 1일";endDt="12월 31일";work_qt="4"
      elif r[1] == "C17" :      #예정
        if tmpKi=="1":  startDt = "1월 1일";endDt="3월 31일";work_qt="1"
        else:           startDt = "7월 1일";endDt="9월 30일";work_qt="3"    
      row={
        '과세기간':r[0] + wcCorpGB_txt,
        '과세유형':r[1],
        '매출세금계산서':r[2],
        '매출세금계산서세액':r[3],
        '카드매출':r[4],
        '기타매출':r[5],
        '영세율매출':r[6],
        '매입세금계산서':r[7],
        '매입세금계산서세액':r[8],
        '기타매입':r[9],
        '기타매입세액':r[10],
        '불공제':r[11],
        '불공제세액':r[12],
        '경감공제세액':r[13],
        '면세매출':r[14],
        '면세매입':r[15],
        '실제납부할세액':r[16],
        '예정세액':r[17],
        '납부세액':int(r[16])+int(r[17]),
        '매입세금계산서수취고정자산금액':r[18],
        '매출합계':r[19],
        '매입합계':r[20],
        '신용카드수취기타카드':r[21][60:73],
        '신용카드수취현금영수증':r[22][60:73],
        '신용카드수취화물복지':r[23][60:73],
        '신용카드수취사업용카드':r[24][60:73],
        '공제받지못할매입세액명세':r[25],
        '의제매입세액공제':r[26][40:54],
        '재활용폐자원등매입세액':r[27][40:54],
        '납부환급세액':r[28],
        '매입세금계산서수취고정자산세액':r[29],
        '산출세액':r[30],
        '가산세액계':r[31],
        '카드현영사용총액':str(r[32]),
        'startDt':startDt,
        'endDt':endDt,
      }
      totalList.append(row)
  context['totIssueList'] = totalList

@csrf_exempt
def getKKOTraderList(request):
  sqno = request.GET.get('sqno')
  memuser = MemUser.objects.get(seq_no=sqno)
  period = request.GET.get('period',False)
  youhyung = request.GET.get('youhyung',False)
    #   print(period)
  tmpKi = period[6:7]
  # print(tmpKi)
  startDt="";endDt=""
  if   youhyung == "C03" :      startDt = "01-01";endDt="12-31"   #간이확정
  elif youhyung == "C13" :      startDt = "01-01";endDt="06-30" #간이 예정    
  elif youhyung == "C07" :      #확정
    if memuser.biz_type<4:
      if tmpKi=="1":  startDt = "04-01";endDt="06-30"
      else:           startDt = "10-01";endDt="12-31"
    elif  memuser.biz_type>=4:
      if tmpKi=="1":  startDt = "01-01";endDt="06-30"
      else:           startDt = "07-01";endDt="12-31"
  elif youhyung == "C17" :      #예정
    if tmpKi=="1":  startDt = "01-01";endDt="03-31"
    else:           startDt = "07-01";endDt="09-30"    

  strsql = " select trader_code,max(trader_name),sum(tranamt_cr),sum(tranamt_dr) from DS_SlipLedgr2 "
  strsql += " where seq_no ="+memuser.seq_no+" and work_yy="+period[0:4]+" and tran_dt>='"+startDt+"' and tran_dt<='"+endDt+"' and tran_stat='매입매출전표' "
  strsql += " and acnt_cd>=401 and acnt_cd<=430 "
  strsql += " group by trader_code order by sum(tranamt_dr) desc "
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  totSaleArr = []
  if result:
    for r in result:
      row = {
        '거래처명':r[1],
        '금액':r[3],
      }
      totSaleArr.append(row)
  strsql = " select trader_code,max(trader_name),sum(tranamt_cr),sum(tranamt_dr)/1.1 from DS_SlipLedgr2 "
  strsql += " where seq_no ="+memuser.seq_no+" and work_yy="+period[0:4]+" and tran_dt>='"+startDt+"' and tran_dt<='"+endDt+"' and tran_stat='매입매출전표' "
  strsql += " and (acnt_cd=251 or acnt_cd=101)"
  strsql += " and tranamt_dr>0"
  strsql += " and trader_name not like '%카드%'"
  strsql += " group by trader_code order by sum(tranamt_dr) desc "
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  totCostArr = []
  if result:
    for r in result:
      row = {
        '거래처명':r[1],
        '금액':r[3],
      }
      totCostArr.append(row)
  strsql = " with ST As  "
  strsql += " (	select *  from DS_SlipLedgr2 with (nolock)  "
  strsql += " where seq_no ="+memuser.seq_no+" and work_yy="+period[0:4]+" and tran_dt>='"+startDt+"' and tran_dt<='"+endDt+"' and tran_stat='매입매출전표'  "
  strsql += " and acnt_cd=253		) "
  strsql += " select a.trader_code, max(a.trader_name), sum(a.tranamt_cr), sum(a.tranamt_dr)"
  strsql += " from DS_SlipLedgr2   a, ST b"
  strsql += " where a.seq_no = b.seq_no "
  strsql += " and a.work_yy = b.work_yy "
  strsql += " and a.tran_dt = b.tran_dt"
  strsql += " and a.slip_no = b.slip_no"
  strsql += " and a.acnt_cd <> 253 "
  strsql += "  group by a.trader_code"
  strsql += "  order by sum(a.tranamt_cr) desc"
  print(strsql)  
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  totCardArr = []
  if result:
    for r in result:
      row = {
        '거래처명':r[1],
        '금액':r[2],
      }
      totCardArr.append(row)      
  rtnJson = {"current":1}
  rtnJson["sale"]=totSaleArr          
  rtnJson["cost"]=totCostArr          
  rtnJson["card"]=totCardArr          
  return JsonResponse(rtnJson,safe=False)


@csrf_exempt
def getTiTrderSumGrid(request):

  memuser = MemUser.objects.get(seq_no=request.GET.get('sqno',False))
  work_yy = request.GET.get('work_yy',False)
  work_qt = request.GET.get('work_qt',False)
  SaleCost = request.GET.get('SaleCost',False)

  strsql_f = "SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = 'C17'"
  read_qt = work_qt;workPeriod2 = "작성일자 >='"
  if work_qt=='1' :   workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-03-31'"
  elif work_qt=='2':  workPeriod2 += str(work_yy)+"-04-01' and 작성일자<='"+str(work_yy)+"-06-30'"
  elif work_qt=='3' :   workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-09-30'"
  elif work_qt=='4': workPeriod2 += str(work_yy)+"-10-01' and 작성일자<='"+str(work_yy)+"-12-31'"
  elif work_qt=='5': workPeriod2 += str(work_yy)+"-01-01' and 작성일자<='"+str(work_yy)+"-06-30'"
  elif work_qt=='6': workPeriod2 += str(work_yy)+"-07-01' and 작성일자<='"+str(work_yy)+"-12-31'"

  totfileArr = []
  tmpColumnName = "공급받는자사업자등록번호,공급받는자상호,공급받는자대표자명"
  if SaleCost=='2,4':tmpColumnName = "공급자사업자등록번호,공급자상호,공급자대표자명"
  strsql = " select "+tmpColumnName+",count(공급가액) 건수,sum(공급가액),sum(세액),sum(합계금액) from 전자세금계산서  "
  strsql += " WHERE 사업자번호='"+memuser.biz_no+"' and 매입매출구분 in ("+SaleCost+") and   "+workPeriod2
  strsql += " group by "+tmpColumnName+" order by sum(합계금액) desc "
  print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = []
  cnt=1  
  if result:
    for r in result:
      row={
        'Trd_No':r[0],
        'CompanyName':r[1],
        'CeoName':r[2],
        'TCnt':r[3],
        'TKKKE':r[4],
        'TVAT':r[5],
        'TKKDK':r[6]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  # rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr 
  rtnJson["read_qt"]=workPeriod2  
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getTIDetailGrid(request):
  sqno = request.GET.get('sqno')
  memuser = MemUser.objects.get(seq_no=sqno)
  SaleCost = request.GET.get('SaleCost',False)
  read_qt = request.GET.get('read_qt',False)
  trdBizno = request.GET.get('trdBizno',False)
  tmpColumnName = "공급받는자사업자등록번호"
  if SaleCost=='2,4':tmpColumnName = "공급자사업자등록번호"
  #print('read_qt:'+str(read_qt))
  strsql = "Select 작성일자,품목명,공급가액,세액,매입매출구분,공급자상호 from 전자세금계산서 	 "                    
  strsql += "WHERE 사업자번호=%s and 매입매출구분 in ("+SaleCost+") and  "+read_qt+"  and "+tmpColumnName+"=%s order by 작성일자 "
  print(strsql)
  with connection.cursor() as cursor:
      cursor.execute(strsql, (memuser.biz_no, trdBizno))
      result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = []
  cnt=1 ;tax10 = 0
  if result:
    for r in result:
      row={
        'tran_dt':r[0][-5:],
        'remk':r[1],
        'KKKE':r[2],
        'Tax':r[3]
      }
      totfileArr.append(row)
      cnt = cnt + 1

      if r[5].find('자동차') != -1 or r[5].find('모터스') != -1: tax10 += r[3]

  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr
  rtnJson["tax10"]=tax10 

  print(f'불공제:{tax10}')
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getCardTrderSumGrid(request):
  memuser = MemUser.objects.get(seq_no=request.GET.get('sqno',False))
  work_yy = request.GET.get('work_yy',False)
  work_qt = request.GET.get('work_qt',False)

  strsql_f = "SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = %s AND 과세기간 = %s AND 과세유형 = 'C17'"
  read_qt = work_qt;workPeriod2 = "Aprvdt >='"
  if work_qt=='1' :   workPeriod2 += str(work_yy)+"-01-01' and Aprvdt<='"+str(work_yy)+"-03-31'"
  elif work_qt=='2':  workPeriod2 += str(work_yy)+"-04-01' and Aprvdt<='"+str(work_yy)+"-06-30'"
  elif work_qt=='3' :   workPeriod2 += str(work_yy)+"-07-01' and Aprvdt<='"+str(work_yy)+"-09-30'"
  elif work_qt=='4':  workPeriod2 += str(work_yy)+"-10-01' and Aprvdt<='"+str(work_yy)+"-12-31'"
  elif work_qt=='5':  workPeriod2 += str(work_yy)+"-01-01' and Aprvdt<='"+str(work_yy)+"-06-30'"                 
  elif work_qt == "6":  workPeriod2 += str(work_yy)+"-07-01' and Aprvdt<='"+str(work_yy)+"-12-31'"    
  # if work_qt=='1' :   workPeriod2 += str(work_yy)+"-01-01' and Aprvdt<='"+str(work_yy)+"-03-31'"
  # elif work_qt=='2':  
  #   with connection.cursor() as cursor:
  #       cursor.execute(strsql_f, (memuser.biz_no, work_yy+"년 1기"))
  #       result_f = cursor.fetchall()
  #   connection.commit()
  #   if result_f:   workPeriod2 += str(work_yy)+"-04-01' and Aprvdt<='"+str(work_yy)+"-06-30'"
  #   else        :  read_qt = "5";  workPeriod2 += str(work_yy)+"-01-01' and Aprvdt<='"+str(work_yy)+"-06-30'"               
  # elif work_qt=='3' :   workPeriod2 += str(work_yy)+"-07-01' and Aprvdt<='"+str(work_yy)+"-09-30'"
  # elif work_qt=='4':  
  #   with connection.cursor() as cursor:
  #       cursor.execute(strsql_f, (memuser.biz_no, work_yy+"년 2기"))
  #       result_f = cursor.fetchall()
  #   connection.commit()  
  #   if result_f:   workPeriod2 += str(work_yy)+"-10-01' and Aprvdt<='"+str(work_yy)+"-12-31'"
  #   else        :  read_qt = "6";  workPeriod2 += str(work_yy)+"-07-01' and Aprvdt<='"+str(work_yy)+"-12-31'"       

  totfileArr = []
  strsql = " select busnCrdCardNoEncCntn,max(CrcmClNm),count(*),sum(totaTrsAmt) from tbl_hometax_scrap  "
  strsql += " WHERE seq_no='"+memuser.seq_no+"' and Tran_YY="+str(work_yy)+" and  "+workPeriod2
  strsql += " group by busnCrdCardNoEncCntn order by max(CrcmClNm) ";print(work_qt);print(strsql)
  with connection.cursor() as cursor:
      cursor.execute(strsql)
      result = cursor.fetchall()
  connection.commit()
  totfileArr = []
  cnt=1  
  if result:
    for r in result:
      row={
        'Card_No':r[0],
        'CompanyName':r[1],
        'Count':r[2],
        'TotalAmt':r[3]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  # rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr 
  rtnJson["read_qt"]=workPeriod2  
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getCardDetailGrid(request):

  sqno = request.GET.get('sqno',False)
  read_qt = request.GET.get('read_qt',False)
  Card_No = request.GET.get('Card_No',False)

  strsql = "Select AprvDt,mrntTxprNm,splCft,vaTxamt,trim(File_DdctGb) from tbl_hometax_scrap 	 "                    
  strsql += "WHERE seq_no=%s and   "+read_qt+"  and busnCrdCardNoEncCntn=%s order by Tran_Dt "
  with connection.cursor() as cursor:
      cursor.execute(strsql, (sqno, Card_No))
      result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = []
  cnt=1 ;
  if result:
    for r in result:
      row={
        'tran_dt':r[0][-5:],
        'trdName':r[1],
        'KKKE':r[2],
        'Tax':r[3],
        'DdctGb':r[4]
      }
      totfileArr.append(row)
      cnt = cnt + 1

  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr

  return JsonResponse(rtnJson,safe=False)

def fetch_results(query, params):
  with connection.cursor() as cursor:
    cursor.execute(query, params)
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
  
def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return {columns[i]: row[i] for i in range(len(columns))}  