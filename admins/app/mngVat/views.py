import json
import datetime
import copy
import math
import os
import natsort
import traceback
from datetime import timedelta
from django.db import connection
from urllib.parse import unquote
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from app.models import MemAdmin
from app.models import MemDeal
from app.models import MemUser  # KijangMember는 "기장회원관리"와 관련된 모델이라고 가정합니다.

from django.db import models,transaction

from django.db.models import Q
from decimal import Decimal, InvalidOperation
from typing import Dict, Any


from admins.utils import send_kakao_notification,kijang_member_popup,tbl_mng_jaroe_update,getSentMails,sendMail,mid_union

GB_KA = "01,02,05,10,12,13,14,50,51,52".split(",")
GB_NA = "15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,40,41,45,55,60,61,62,63,64,65,66,67".split(",")
GB_DA = "70,71,72,73,74,80,85,90,92,93,94,95".split(",")

@login_required(login_url="/login/")
def index(request):
  context = {}
  admin_grade     = request.session.get('Admin_Grade')
  admin_biz_level = request.session.get('Admin_Biz_Level')
  admin_biz_area  = request.session.get('Admin_Area')
  ADID = request.session.get('ADID')#request.GET.get("ADID")
  flag = request.GET.get("flag")

  arr_ADID = []

  if admin_grade != "SA":
      if admin_biz_level == "세무사":
          # Query for admin_id
          arr_ADID = MemAdmin.objects.filter(
              ~Q(grade="SA"),
              ~Q(biz_level="세무사"),
              ~Q(del_yn="y"),
              admin_biz_area = admin_biz_area
          ).order_by('admin_id').values_list('admin_id', flat=True)
  else:  # admin_grade == "SA"
      arr_ADID = list(MemAdmin.objects.filter(
          ~Q(grade="SA"),
          ~Q(biz_level="세무사"),
          ~Q(del_yn="y")
      ).order_by("admin_id").values_list('admin_id', flat=True))
      arr_ADID.insert(0, "전체")
  if not ADID:
    ADID = arr_ADID[0] if arr_ADID else ""


  work_YY = request.GET.get('work_YY', '')
  work_MM = request.GET.get('work_MM', '')
  today = datetime.datetime.now()
  cur_date = today.strftime("%Y%m%d")
  if not work_MM:
    work_MM = request.session.get('workmonth')
    if not work_MM:
      work_MM = today.month
  corpYear = today.year
  if int(work_MM) <= 2 :
    corpYear = today.year-1
  if not work_YY:
    work_YY = request.session.get('workyearVat')
    if not work_YY:
      if int(work_MM) <= 2 :
        work_YY = today.year - 1
      else:
        work_YY = today.year
    else:
      work_YY = int(work_YY)

  work_QT = request.session.get("work_QT") 
  if not work_QT:
      if f"{work_YY}0301" <= cur_date <= f"{work_YY}0430":
        work_QT = 1
      elif f"{work_YY}0501" <= cur_date <= f"{work_YY}0731":
        work_QT = 2
      elif f"{work_YY}0801" <= cur_date <= f"{work_YY}1031":
        work_QT = 3
      elif f"{work_YY}1101" <= cur_date <= f"{int(work_YY) + 1}0229":
        work_QT = 4
      else:
        work_QT = 4
  else:
      work_QT = int(work_QT)

  request.session['work_QT'] = work_QT
  request.session['workyearVat'] = work_YY
  request.session['workmonth'] = work_MM
  
  vatYears = list(range(corpYear, corpYear - 6, -1))
  # print(corpYears)
  context['vatYears'] = vatYears
  context['admin_grade'] = admin_grade
  context['admin_biz_level'] = admin_biz_level
  context['arr_ADID'] = json.dumps(list(arr_ADID))
  context['flag'] = flag
  context['ADID'] = ADID
  request.session['ADID'] = ADID  

  request.session.save()

  templateMenu = gridTitle=""
  if flag == "Vat":
    templateMenu = 'admin/mng_vat.html'; gridTitle="부가가치세 신고"
  elif flag == "noneVat":
    templateMenu = 'admin/mng_noneVat.html'; gridTitle="사업장현황신고"        
  context['gridTitle'] = gridTitle  
  return render(request, templateMenu,context)

def mng_vat(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')#전체 선택시 ADID=""상태가 된다
  request.session['ADID'] = ADID  
  
  work_YY = request.GET.get('work_YY', '')
  work_QT = request.GET.get('work_QT', '')
  if work_QT:
    work_QT = int(work_QT)
  else:
    work_QT = request.session['work_QT']
  request.session['workyearVat'] = work_YY
  request.session['work_QT'] = work_QT
  request.session.save()
  kwasekikan,ks2,SKGB = setKwasekikan(int(work_YY),int(work_QT))

  # 수수료 연도/월 설정
  feelyear = str(int(work_YY) + 1) if work_QT == 4 else work_YY
  feelMM = 1 if work_QT == 4 else work_QT * 3 + 1

  # 통합 신고 구분코드 설정
  if work_QT in [1, 3]:
    strSKGB = "C17"
  elif work_QT in [2, 4]:
    strSKGB = "C07"

  if request.method == 'GET':
    s_sql = ""
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"
    # work_QT 기준 biz_type 조건 추가
    if work_QT in [1, 3]:
      s_sql += " and a.biz_type IN ('1', '4')  "
    elif work_QT == 2:
      s_sql += " and a.biz_type < '5'  "
    elif work_QT == 4:
      s_sql += " and a.biz_type < '6'  "
    sql_query = f"""
      SELECT 
          b.biz_manager as groupManager,a.seq_no,a.ceo_name ,a.biz_name,biz_type,YN_7, YN_8, Tel_sincaSale, YN_15, ISNULL(E.차감납부할세액, 0) AS YN_18, YN_10, ISNULL(YN_14, -1) AS YN_14,
          ISNULL((
              SELECT TOP 1 mail_subject   FROM tbl_mail 
              WHERE seq_no = a.seq_no 
                  AND YEAR(mail_date) = '{feelyear}' 
                  AND MONTH(mail_date) IN ({feelMM}, {feelMM+1})
                  AND mail_class = 'vat'
                  AND (LEFT(mail_subject, 8) = '[세무법인대승]' 
                      OR LEFT(mail_subject, 9) = '[세무법인 대승]')
              ORDER BY LEN(mail_subject) DESC
          ), '') AS mailSent,
          ISNULL((
              SELECT TOP 1 LEFT(CAST(contents AS VARCHAR(MAX)), 34)   FROM Tbl_OFST_KAKAO_SMS 
              WHERE seq_user = a.seq_no   AND send_result = 'Y' 
                  AND REPLACE(CAST(contents AS VARCHAR(MAX)), '년도 ', '년 ') LIKE '%{kwasekikan} {ks2}%'
          ), '') AS kakao,
          ISNULL((
              SELECT TOP 1 seq_no   FROM Tbl_SMS 
              WHERE seq_no = a.seq_no 
                  AND sms_contents LIKE '%{kwasekikan} {ks2}%'
                  AND sms_contents LIKE '%수수료%'
          ), '') AS SMS,
          TRIM(YN_13) AS YN_13,
          ISNULL(E.inspect_issue, 0) AS inspect_issue,
          ISNULL(E.inspect_elec, 0) AS inspect_elec,
          ISNULL(E.inspect_labor, 0) AS inspect_labor,
          ISNULL(E.신고시각, '') AS isIssue,
          ISNULL(E.제출자, '') AS JupsuID,
          YN_12, YN_11, YN_1, YN_2,YN_3, YN_4, YN_5, YN_6,
          ISNULL(( SELECT TOP 1 과세기수   FROM 부가가치세통합조회   WHERE 사업자등록번호 = a.biz_no  AND 과세기수 = '{kwasekikan}'   AND 신고구분 = '{ks2[:2]}' ), '') AS YN_Kisu
      FROM mem_user a
      INNER JOIN mem_deal b ON a.seq_no = b.seq_no
      INNER JOIN mem_admin c ON b.biz_manager = c.admin_id
      LEFT JOIN tbl_vat d 
          ON d.seq_no = a.seq_no 
          AND d.work_YY = '{work_YY}' 
          AND d.work_QT = '{work_QT}'
      LEFT JOIN 부가가치세전자신고3 E 
          ON E.사업자등록번호 = a.biz_no 
          AND E.과세기간 = '{kwasekikan}' 
          AND E.과세유형 = '{strSKGB}'
      WHERE 
          b.biz_manager != '오피스텔' AND a.duzon_ID <> ''  AND a.Del_YN <> 'Y'  AND b.keeping_YN = 'Y'  {s_sql}
      ORDER BY  a.biz_name ASC;
    """
    #print(sql_query)
    recordset = []
    with connection.cursor() as cursor:
      cursor.execute(sql_query)
      columns = [col[0] for col in cursor.description]  # 컬럼명 가져오기
      results = cursor.fetchall()
      for row in results:
        # 문자열 값이면 strip() 적용, 아니면 그대로 유지
        row_dict = {columns[i]: (value.strip() if isinstance(value, str) else value) for i, value in enumerate(row)}
        recordset.append(row_dict)
    #print(recordset) 
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

#전자신고 접수증 가져오기
def mng_vat_jupsuSummit(request):
  seq_no = request.POST.get('seq_no')
  work_YY = request.POST.get('work_YY')  
  work_QT = request.POST.get('work_QT')  
  strKi = '1기' if int(work_QT) <= 2 else '2기'
  if seq_no:
    memuser = get_object_or_404(MemUser, seq_no=seq_no)

    sql_query = f"""
      SELECT 과세기간,신고구분,과세유형,환급구분,상호,사업자등록번호,접수여부,신고번호,신고시각 FROM 부가가치세전자신고3
      WHERE 사업자등록번호 = '{memuser.biz_no}' AND 과세기간 = '{work_YY}년 {strKi}'
    """  
    # print(sql_query)
    with connection.cursor() as cursor:
      cursor.execute(sql_query)
      rows = dict_fetchall(cursor)
      # print(rows)
      rows[0].update({"biz_name":memuser.biz_name,"ceo_name": memuser.ceo_name})
      return JsonResponse(rows[0], safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

#전자신고 파일 업로드 - 정기/기한후
def parse_vat_file(file_path, ext):
    with open(file_path, 'r',encoding='cp949') as f:
        lines = f.readlines()

    record_11 = []
    record_17 = []
    CardSaleSheet = []
    CardCost1 = []
    CardCost2 = []
    CardCost3 = []
    CardCost4 = []
    PretendPurchase = []
    PretendPurchase2 = []
    BullGongSheet = []
    PaperSalesTaxInvoice = []
    PaperExpTaxInvoice = []
    PaperSalesTaxInvoiceSum = []
    PaperExpTaxInvoiceSum = []

    j = 0
    for sr in lines:
        sr = sr.strip()

        if sr.startswith("11I") or sr.startswith("12I"):
            record_11.append(sr)
            record_17.append("")
            CardSaleSheet.append("")
            CardCost1.append("")
            CardCost2.append("")
            CardCost3.append("")
            CardCost4.append("")
            PretendPurchase.append("")
            PretendPurchase2.append("")
            BullGongSheet.append("")
            PaperSalesTaxInvoice.append("")
            PaperExpTaxInvoice.append("")
            PaperSalesTaxInvoiceSum.append("")
            PaperExpTaxInvoiceSum.append("")
            j += 1

        elif sr.startswith("17I103200"):
            record_17[j - 1] = sr

        elif sr.startswith("17I103400"):
            CardSaleSheet[j - 1] = sr

        elif sr.startswith("DL"):
            card_type = mid_union(sr, 19, 1)
            if card_type == "1":
                CardCost1[j - 1] = sr
            elif card_type == "2":
                CardCost2[j - 1] = sr
            elif card_type == "3":
                CardCost3[j - 1] = sr
            elif card_type == "4":
                CardCost4[j - 1] = sr

        elif sr.startswith("14I103200230"):
            PretendPurchase[j - 1] = sr

        elif sr.startswith("14I103200270"):
            PretendPurchase2[j - 1] = sr

        elif sr.startswith("18I103300"):
            BullGongSheet[j - 1] += mid_union(sr, 10, 39)

        elif sr.startswith("1" + mid_union(record_11[j - 1], 10, 10)):
            PaperSalesTaxInvoice[j - 1] += sr

        elif sr.startswith("2" + mid_union(record_11[j - 1], 10, 10)):
            PaperExpTaxInvoice[j - 1] += sr

        elif sr.startswith("3" + mid_union(record_11[j - 1], 10, 10)):
            if ext != "105":
                PaperSalesTaxInvoiceSum[j - 1] += sr

        elif sr.startswith("4" + mid_union(record_11[j - 1], 10, 10)):
            PaperExpTaxInvoiceSum[j - 1] += sr

    return {
        'record_11': record_11,
        'record_17': record_17,
        'CardSaleSheet': CardSaleSheet,
        'CardCost1': CardCost1,
        'CardCost2': CardCost2,
        'CardCost3': CardCost3,
        'CardCost4': CardCost4,
        'PretendPurchase': PretendPurchase,
        'PretendPurchase2': PretendPurchase2,
        'BullGongSheet': BullGongSheet,
        'PaperSalesTaxInvoice': PaperSalesTaxInvoice,
        'PaperExpTaxInvoice': PaperExpTaxInvoice,
        'PaperSalesTaxInvoiceSum': PaperSalesTaxInvoiceSum,
        'PaperExpTaxInvoiceSum': PaperExpTaxInvoiceSum
    }

def extract_biz_info(rec11):
    biz_no = f"{rec11[9:12]}-{rec11[12:14]}-{rec11[14:19]}"
    work_yy = rec11[28:32]
    txt_ki = rec11[32:34].replace("0", "")
    work_qt = int(txt_ki)
    upjong_code = mid_union(rec11, 423, 7).strip()
    wc_corp_gb = rec11[34:37]
    issue_id = rec11[37:57].strip()

    wc_corp_gb_txt = {
        "C03": "부가가치세 확정(간이)신고서",
        "C05": "부가가치세 확정(일반) 4,10월조기 신고서",
        "C06": "부가가치세 확정(일반) 5,11월조기 신고서",
        "C07": "부가가치세 확정(일반) 신고서",
        "C13": "부가가치세 예정(간이)신고서",
        "C15": "부가가치세 예정(일반) 1,7월조기 신고서",
        "C16": "부가가치세 예정(일반) 2,8월조기 신고서",
        "C17": "부가가치세 예정(일반) 신고서",
    }.get(wc_corp_gb, "기타")

    # work_qt 보정
    if wc_corp_gb in ["C03", "C07", "C05", "C06"]:
        work_qt = 4 if txt_ki == "2" else 2
    elif wc_corp_gb in ["C13", "C15", "C16", "C17"]:
        work_qt = 3 if txt_ki == "2" else 1

    return biz_no, work_yy,txt_ki, work_qt, upjong_code, wc_corp_gb, wc_corp_gb_txt, issue_id

def parse_record_17(record_17):
  length_17 = 0
  mainIssue_17 = [None] * 86  # 인덱스 1부터 사용하기 위해 크기 86의 리스트 생성

  for m in range(1, 86):
      if m == 1 or m == 74:
          mainIssue_17[m] = record_17[length_17:length_17 + 2]
          length_17 += 2
      elif m in [3, 7, 8, 12, 24, 25, 26, 44, 56, 59, 60, 67, 69, 71, 72, 73, 82, 85]:
          mainIssue_17[m] = record_17[length_17:length_17 + 15]
          length_17 += 15
      elif m in [75, 80]:
          mainIssue_17[m] = record_17[length_17:length_17 + 3]
          length_17 += 3
      elif m == 76:
          mainIssue_17[m] = record_17[length_17:length_17 + 20]
          length_17 += 20
      elif m == 77:
          mainIssue_17[m] = record_17[length_17:length_17 + 9]
          length_17 += 9
      elif m == 78:
          mainIssue_17[m] = record_17[length_17:length_17 + 30]		#MidUnion(record_17, length_17, 30)
          length_17 += 30
      elif m == 79:
          mainIssue_17[m] = record_17[length_17:length_17 + 8]
          length_17 += 8
      elif m in [81, 83, 84]:
          mainIssue_17[m] = record_17[length_17:length_17 + 1]
          length_17 += 1
      elif m == 2:
          mainIssue_17[m] = record_17[length_17:length_17 + 7]
          length_17 += 7
      else:
          mainIssue_17[m] = record_17[length_17:length_17 + 13]
          length_17 += 13
  return mainIssue_17

def save_elecfile_Vat(request):
  if request.method != "POST":
    return HttpResponse("Invalid request method.")
  
  # 파일 업로드 처리 (폼 필드 이름: "uploadFile")
  uploaded_file = request.FILES.get("uploadFile")
  if not uploaded_file:
    return HttpResponse("No file uploaded.")

  # 파일명에서 경로 제거 후 파일명 추출
  user_file_name = os.path.basename(uploaded_file.name)
  # 파일명과 확장자 분리 (예: "example.01" -> ("example", ".01"))
  file_name, file_ext = os.path.splitext(user_file_name)
  ext = file_ext[1:]  # 앞의 '.' 제거
  # 파일 확장자가 "01" 또는 "03"이 아니면 경고 후 중단
  if ext not in ['101', '103', '105']:
      return HttpResponse(
          "<script language='javascript'>"
          "alert('부가가치세 전자신고 파일이 아닙니다.');"
          "location.href='about:blank';"
          "</script>"
      )

  # settings를 사용하지 않고 static 폴더 내 upload 폴더를 사용
  upload_dir = os.path.join("static", "upload")
  if not os.path.exists(upload_dir):
      os.makedirs(upload_dir)

  # 파일 중복 방지를 위해 파일명이 존재하면 [숫자]를 추가
  save_file_name = os.path.join(upload_dir, user_file_name)
  i = 1
  while os.path.exists(save_file_name):
    new_name = f"{file_name}[{i}].{ext}"
    save_file_name = os.path.join(upload_dir, new_name)
    user_file_name = new_name
    i += 1

  # 업로드 파일 저장 (바이너리 모드)
  with open(save_file_name, "wb") as destination:
      for chunk in uploaded_file.chunks():
          destination.write(chunk)

  # 전자신고 파일 파싱
  records = parse_vat_file(save_file_name, ext)

  # 각 신고 레코드에 대해 반복 처리
  for k, rec11 in enumerate(records['record_11']):
      biz_no, work_yy,txt_ki, work_qt, upjong_code, wc_corp_gb, wc_corp_gb_txt, issue_id = extract_biz_info(rec11)
      kwasekikan = f"{work_yy}년 {txt_ki}기"

      try:
          mem_user = MemUser.objects.get(biz_no=biz_no)
          biz_type = mem_user.biz_type
      except MemUser.DoesNotExist:
          continue

      record_17_line = records['record_17'][k]
      if not record_17_line:
          continue

      mainIssue_17 = parse_record_17(record_17_line)

      PaperSalesTaxInvoice = records['PaperSalesTaxInvoice'][k]
      PaperSalesTaxInvoiceSum = records['PaperSalesTaxInvoiceSum'][k]
      PaperExpTaxInvoice = records['PaperExpTaxInvoice'][k]
      PaperExpTaxInvoiceSum = records['PaperExpTaxInvoiceSum'][k]
      CardSaleSheet = records['CardSaleSheet'][k]
      CardCost1 = records['CardCost1'][k]
      CardCost2 = records['CardCost2'][k]
      CardCost3 = records['CardCost3'][k]
      CardCost4 = records['CardCost4'][k]
      BullGongSheet = records['BullGongSheet'][k]
      PretendPurchase = records['PretendPurchase'][k]
      PretendPurchase2 = records['PretendPurchase2'][k]
      with connection.cursor() as cursor:
        merge_query = f"""
          MERGE 부가가치세전자신고3 AS A
          USING (
              SELECT '{biz_no}' AS biz_no, '{kwasekikan}' AS wcKwase, '{wc_corp_gb}' AS wcCorpGB_txt
          ) AS B
          ON A.과세기간 = B.wcKwase AND A.사업자등록번호 = B.biz_no AND A.과세유형 = B.wcCorpGB_txt

          WHEN MATCHED THEN
          UPDATE SET 
          		매출과세세금계산서발급금액 = '{mainIssue_17[3]}',
              매출과세세금계산서발급세액 = '{mainIssue_17[4]}',
              매출과세매입자발행세금계산서금액 = '{mainIssue_17[5]}',
              매출과세매입자발행세금계산서세액 = '{mainIssue_17[6]}',
              매출과세카드현금발행금액 = '{mainIssue_17[7]}',
              매출과세카드현금발행세액 = '{mainIssue_17[8]}',
              매출과세기타금액 = '{mainIssue_17[9]}',
              매출과세기타세액 = '{mainIssue_17[10]}',
              매출영세율세금계산서발급금액 = '{mainIssue_17[11]}',
              매출영세율기타금액 = '{mainIssue_17[12]}',
              매출예정누락합계금액 = '{mainIssue_17[13]}',
              매출예정누락합계세액 = '{mainIssue_17[14]}',
              예정누락매출세금계산서금액 = '{mainIssue_17[15]}',
              예정누락매출세금계산서세액 = '{mainIssue_17[16]}',
              예정누락매출과세기타금액 = '{mainIssue_17[17]}',
              예정누락매출과세기타세액 = '{mainIssue_17[18]}',
              예정누락매출영세율세금계산서금액 = '{mainIssue_17[19]}',
              예정누락매출영세율기타금액 = '{mainIssue_17[20]}',
              예정누락매출명세합계금액 = '{mainIssue_17[21]}',
              예정누락매출명세합계세액 = '{mainIssue_17[22]}',
              매출대손세액가감세액 = '{mainIssue_17[23]}',
              과세표준금액 = '{mainIssue_17[24]}',
              산출세액 = '{mainIssue_17[25]}',
              매입세금계산서수취일반금액 = '{mainIssue_17[26]}',
              매입세금계산서수취일반세액 = '{mainIssue_17[27]}',
              매입세금계산서수취고정자산금액 = '{mainIssue_17[28]}',
              매입세금계산서수취고정자산세액 = '{mainIssue_17[29]}',
              매입예정누락합계금액 = '{mainIssue_17[30]}',
              매입예정누락합계세액 = '{mainIssue_17[31]}',
              예정누락매입신고세금계산서금액 = '{mainIssue_17[32]}',
              예정누락매입신고세금계산서세액 = '{mainIssue_17[33]}',
              예정누락매입기타공제금액 = '{mainIssue_17[34]}',
              예정누락매입기타공제세액 = '{mainIssue_17[35]}',
              예정누락매입명세합계금액 = '{mainIssue_17[36]}',
              예정누락매입명세합계세액 = '{mainIssue_17[37]}',
              매입자발행세금계산서매입금액 = '{mainIssue_17[38]}',
              매입자발행세금계산서매입세액 = '{mainIssue_17[39]}',
              매입기타공제매입금액 = '{mainIssue_17[40]}',
              매입기타공제매입세액 = '{mainIssue_17[41]}',
              그밖의공제매입명세합계금액 = '{mainIssue_17[42]}',
              그밖의공제매입명세합계세액 = '{mainIssue_17[43]}',
              매입세액합계금액 = '{mainIssue_17[44]}',
              매입세액합계세액 = '{mainIssue_17[45]}',
              공제받지못할매입합계금액 = '{mainIssue_17[46]}',
              공제받지못할매입합계세액 = '{mainIssue_17[47]}',
              공제받지못할매입금액 = '{mainIssue_17[48]}',
              공제받지못할매입세액 = '{mainIssue_17[49]}',
              공제받지못할공통매입면세사업금액 = '{mainIssue_17[50]}',
              공제받지못할공통매입면세사업세액 = '{mainIssue_17[51]}',
              공제받지못할대손처분금액 = '{mainIssue_17[52]}',
              공제받지못할대손처분세액 = '{mainIssue_17[53]}',
              공제받지못할매입명세합계금액 = '{mainIssue_17[54]}',
              공제받지못할매입명세합계세액 = '{mainIssue_17[55]}',
              차감합계금액 = '{mainIssue_17[56]}',
              차감합계세액 = '{mainIssue_17[57]}',
              납부환급세액 = '{mainIssue_17[58]}',
              그밖의경감공제세액 = '{mainIssue_17[59]}',
              그밖의경감공제명세합계세액 = '{mainIssue_17[60]}',
              경감공제합계세액 = '{mainIssue_17[61]}',
              예정신고미환급세액 = '{mainIssue_17[62]}',
              예정고지세액 = '{mainIssue_17[63]}',
              사업양수자의대리납부기납부세액 = '{mainIssue_17[64]}',
              매입자납부특례기납부세액 = '{mainIssue_17[65]}',
              가산세액계 = '{mainIssue_17[66]}',
              차감납부할세액 = '{mainIssue_17[67]}',
              과세표준명세수입금액제외금액 = '{mainIssue_17[68]}',
              과세표준명세합계수입금액 = '{mainIssue_17[69]}',
              면세사업수입금액제외금액 = '{mainIssue_17[70]}',
              면세사업합계수입금액 = '{mainIssue_17[71]}',
              계산서교부금액 = '{mainIssue_17[72]}',
              계산서수취금액 = '{mainIssue_17[73]}',
              환급구분코드 = '{mainIssue_17[74]}',
              은행코드 = '{mainIssue_17[75]}',
              계좌번호 = '{mainIssue_17[76]}',
              총괄납부승인번호 = '{mainIssue_17[77]}',
              은행지점명 = '{mainIssue_17[78]}',
              폐업일자 = '{mainIssue_17[79]}',
              폐업사유 = '{mainIssue_17[80]}',
              기한후여부 = '{mainIssue_17[81]}',
              실차감납부할세액 = '{mainIssue_17[82]}',
              일반과세자구분 = '{mainIssue_17[83]}',
              조기환급취소구분 = '{mainIssue_17[84]}',
              수출기업수입납부유예 = '{mainIssue_17[85]}',
              업종코드 = '{upjong_code}',
              전자외매출세금계산서 = '{PaperSalesTaxInvoice}',
              전자외매출세금계산서합계 = '{PaperSalesTaxInvoiceSum}',
              전자외매입세금계산서 = '{PaperExpTaxInvoice}',
              전자외매입세금계산서합계 = '{PaperExpTaxInvoiceSum}',
              신용카드발행집계표 = '{CardSaleSheet}',
              신용카드수취기타카드 = '{CardCost1}',
              신용카드수취현금영수증 = '{CardCost2}',
              신용카드수취화물복지 = '{CardCost3}',
              신용카드수취사업용카드 = '{CardCost4}',
              공제받지못할매입세액명세 = '{BullGongSheet}',
              의제매입세액공제 = '{PretendPurchase}',
              재활용폐자원등매입세액 = '{PretendPurchase2}',
              제출자 = '{issue_id}'

          WHEN NOT MATCHED THEN
          INSERT (
              과세기간, 과세유형,   사업자등록번호,
              매출과세세금계산서발급금액, 매출과세세금계산서발급세액, 매출과세매입자발행세금계산서금액,
              매출과세매입자발행세금계산서세액, 매출과세카드현금발행금액, 매출과세카드현금발행세액,
              매출과세기타금액, 매출과세기타세액, 매출영세율세금계산서발급금액, 매출영세율기타금액,
              매출예정누락합계금액, 매출예정누락합계세액, 예정누락매출세금계산서금액,
              예정누락매출세금계산서세액, 예정누락매출과세기타금액, 예정누락매출과세기타세액,
              예정누락매출영세율세금계산서금액, 예정누락매출영세율기타금액,
              예정누락매출명세합계금액, 예정누락매출명세합계세액, 매출대손세액가감세액,
              과세표준금액, 산출세액, 매입세금계산서수취일반금액,
              매입세금계산서수취일반세액, 매입세금계산서수취고정자산금액,
              매입세금계산서수취고정자산세액, 매입예정누락합계금액, 매입예정누락합계세액,
              예정누락매입신고세금계산서금액, 예정누락매입신고세금계산서세액,
              예정누락매입기타공제금액, 예정누락매입기타공제세액,
              예정누락매입명세합계금액, 예정누락매입명세합계세액,
              매입자발행세금계산서매입금액, 매입자발행세금계산서매입세액,
              매입기타공제매입금액, 매입기타공제매입세액,
              그밖의공제매입명세합계금액, 그밖의공제매입명세합계세액,
              매입세액합계금액, 매입세액합계세액,
              공제받지못할매입합계금액, 공제받지못할매입합계세액,
              공제받지못할매입금액, 공제받지못할매입세액,
              공제받지못할공통매입면세사업금액, 공제받지못할공통매입면세사업세액,
              공제받지못할대손처분금액, 공제받지못할대손처분세액,
              공제받지못할매입명세합계금액, 공제받지못할매입명세합계세액,
              차감합계금액, 차감합계세액, 납부환급세액,
              그밖의경감공제세액, 그밖의경감공제명세합계세액, 경감공제합계세액,
              예정신고미환급세액, 예정고지세액,
              사업양수자의대리납부기납부세액, 매입자납부특례기납부세액,
              가산세액계, 차감납부할세액,
              과세표준명세수입금액제외금액, 과세표준명세합계수입금액,
              면세사업수입금액제외금액, 면세사업합계수입금액,
              계산서교부금액, 계산서수취금액,
              환급구분코드, 은행코드, 계좌번호,
              총괄납부승인번호, 은행지점명, 폐업일자, 폐업사유, 기한후여부,
              실차감납부할세액, 일반과세자구분, 조기환급취소구분, 수출기업수입납부유예,
              업종코드, 전자외매출세금계산서, 전자외매출세금계산서합계,
              전자외매입세금계산서, 전자외매입세금계산서합계,
              신용카드발행집계표, 신용카드수취기타카드, 신용카드수취현금영수증,
              신용카드수취화물복지, 신용카드수취사업용카드,
              공제받지못할매입세액명세, 의제매입세액공제, 재활용폐자원등매입세액,
              제출자
          ) VALUES (
              '{kwasekikan}',  '{wc_corp_gb}',  '{biz_no}',
              '{mainIssue_17[3]}', '{mainIssue_17[4]}', '{mainIssue_17[5]}', '{mainIssue_17[6]}', '{mainIssue_17[7]}', '{mainIssue_17[8]}', '{mainIssue_17[9]}',
              '{mainIssue_17[10]}', '{mainIssue_17[11]}', '{mainIssue_17[12]}', '{mainIssue_17[13]}', '{mainIssue_17[14]}', '{mainIssue_17[15]}', '{mainIssue_17[16]}', 
              '{mainIssue_17[17]}', '{mainIssue_17[18]}', '{mainIssue_17[19]}', '{mainIssue_17[20]}', '{mainIssue_17[21]}', '{mainIssue_17[22]}', '{mainIssue_17[23]}', 
              '{mainIssue_17[24]}', '{mainIssue_17[25]}', '{mainIssue_17[26]}', '{mainIssue_17[27]}', '{mainIssue_17[28]}', '{mainIssue_17[29]}', '{mainIssue_17[30]}', 
              '{mainIssue_17[31]}', '{mainIssue_17[32]}', '{mainIssue_17[33]}', '{mainIssue_17[34]}', '{mainIssue_17[35]}', '{mainIssue_17[36]}', '{mainIssue_17[37]}', 
              '{mainIssue_17[38]}', '{mainIssue_17[39]}', '{mainIssue_17[40]}', '{mainIssue_17[41]}', '{mainIssue_17[42]}', '{mainIssue_17[43]}', '{mainIssue_17[44]}', 
              '{mainIssue_17[45]}', '{mainIssue_17[46]}', '{mainIssue_17[47]}', '{mainIssue_17[48]}', '{mainIssue_17[49]}', '{mainIssue_17[50]}', '{mainIssue_17[51]}', 
              '{mainIssue_17[52]}', '{mainIssue_17[53]}', '{mainIssue_17[54]}', '{mainIssue_17[55]}', '{mainIssue_17[56]}', '{mainIssue_17[57]}', '{mainIssue_17[58]}', 
              '{mainIssue_17[59]}', '{mainIssue_17[60]}', '{mainIssue_17[61]}', '{mainIssue_17[62]}', '{mainIssue_17[63]}', '{mainIssue_17[64]}', '{mainIssue_17[65]}', 
              '{mainIssue_17[66]}', '{mainIssue_17[67]}', '{mainIssue_17[68]}', '{mainIssue_17[69]}', '{mainIssue_17[70]}', '{mainIssue_17[71]}', '{mainIssue_17[72]}', 
              '{mainIssue_17[73]}', '{mainIssue_17[74]}', '{mainIssue_17[75]}', '{mainIssue_17[76]}', '{mainIssue_17[77]}', '{mainIssue_17[78]}', '{mainIssue_17[79]}',
              '{mainIssue_17[80]}', '{mainIssue_17[81]}', '{mainIssue_17[82]}', '{mainIssue_17[83]}', '{mainIssue_17[84]}', '{mainIssue_17[85]}', 
              '{upjong_code}', '{PaperSalesTaxInvoice}', '{PaperSalesTaxInvoiceSum}', '{PaperExpTaxInvoice}', '{PaperExpTaxInvoiceSum}',
              '{CardSaleSheet}', '{CardCost1}', '{CardCost2}',
              '{CardCost3}', '{CardCost4}', '{BullGongSheet}', '{PretendPurchase}', '{PretendPurchase2}', '{issue_id}'
          );      
        """
        # print(merge_query) 
        cursor.execute(merge_query)

        # 검증용 데이터조회
        strsql = build_vatInspect_query(mem_user.seq_no, work_yy, work_qt, kwasekikan, wc_corp_gb)
        # print(strsql) 
        cursor.execute(strsql)
        rs = dictfetchone(cursor)
        if rs:
          result =  get_tax_inspection_result(rs, work_yy, work_qt, biz_no, biz_type,kwasekikan, wc_corp_gb,mem_user.seq_no)
          inspect_issue = result["inspect_issue"]
          inspect_elec = result["inspect_elec"]
          inspect_labor = result["inspect_labor"]
          strsql = f"update  부가가치세전자신고3 set inspect_issue = '{inspect_issue}',inspect_elec = '{inspect_elec}',inspect_labor = '{inspect_labor}' "
          strsql += f"where 사업자등록번호= '{biz_no}' and 과세기간= '{kwasekikan}' and 과세유형='{wc_corp_gb}'"
          # print(strsql) 
          cursor.execute(strsql)
        #통합조회 업데이트
        strKSUH = "확정"
        if wc_corp_gb=="C17": strKSUH = "예정"
        str_nm = f"select * from 부가가치세통합조회 where 과세기수='{kwasekikan}' and 신고구분='{strKSUH}' and 사업자등록번호='{biz_no}'"     
        # 법인이 확정신고기간인데 예정신고 안했으면 예정기간 통합자료를 합산해야 한다
        txtSpecial = isSKGB_C07(biz_no,kwasekikan)#true면 예정신고 있음
        if biz_type<4 and wc_corp_gb=="C07" and not txtSpecial:
          str_nm = f"""
            select 
              max(과세기수) 과세기수, max(과세기간) 과세기간,max(신고구분) 신고구분,max(상호) 상호,max(신고유형) 신고유형,max(관할서) 관할서,max(법인예정고지대상) 법인예정고지대상,max(간이부가율) 간이부가율,max(주업종코드) 주업종코드,
              sum(매출전자세금계산서공급가액) 매출전자세금계산서공급가액,sum(매출전자세금계산서세액) 매출전자세금계산서세액,sum(매출전자계산서공급가액) 매출전자계산서공급가액, 
              sum(매출신용카드공급가액) 매출신용카드공급가액,sum(매출신용카드세액) 매출신용카드세액, 
              sum(매출현금영수증공급가액) 매출현금영수증공급가액,sum(매출현금영수증세액) 매출현금영수증세액,sum(수출신고필증) 수출신고필증,sum(구매확인서등) 구매확인서등, sum(매출판매대행) 매출판매대행, 
              sum(매입전자세금계산서공급가액) 매입전자세금계산서공급가액,sum(매입전자세금계산서세액) 매입전자세금계산서세액,sum(매입전자계산서공급가액) 매입전자계산서공급가액, sum(매입신용카드세액) 매입신용카드세액,
              sum(매입신용카드공급가액) 매입신용카드공급가액, sum(매입현금영수증공급가액) 매입현금영수증공급가액,sum(매입현금영수증세액) 매입현금영수증세액,sum(매입복지카드공급가액) 매입복지카드공급가액,sum(매입복지카드세액) 매입복지카드세액,
              max(예정고지세액일반) 예정고지세액일반, max(예정미환급세액일반) 예정미환급세액일반,max(예정부과세액간이) 예정부과세액간이,max(예정신고세액간이) 예정신고세액간이,
              max(매입자납부특례기납부세액) 매입자납부특례기납부세액, max(현금매출명세서) 현금매출명세서,max(부동산임대공급가액명세서) 부동산임대공급가액명세서 
            from 부가가치세통합조회 where 과세기수='{kwasekikan}'  and 사업자등록번호='{biz_no}'
          """
        cursor.execute(str_nm)
        rs_Tong = dictfetchone(cursor) 
        print(str_nm)
        print(rs_Tong)    
        strsql = build_vatElec_query(biz_no,  kwasekikan, wc_corp_gb)
        cursor.execute(strsql)
        rs_vatElec = dictfetchone(cursor)
        vatElec = process_vat_data(rs_vatElec)
        tong_data = process_Tong_data(biz_no, work_yy, work_qt,rs_Tong,vatElec)

  return JsonResponse({"success": True, "message": "전자신고파일 업로드 완료"})

#전자신고 접수번호 저장 - 클립보드 타입
def save_clipboard_Vat(request):
  if request.method == 'POST':
    clipboardData   = request.POST.get("clipboardData")
    if clipboardData:
      fields = [field.strip() for field in clipboardData.split('\t')]
      wcKwase = fields[0]      # 0:2023년12월
      wcKwase = wcKwase.replace("월", "기")

      # 3. 앞에서 5글자
      wc1 = wcKwase[:5]

      # 4. 오른쪽에서 두 번째 문자를 가져오기 (예: "2023년 7기" -> "7")
      wc2 = wcKwase[-2]
      if wc2 == "7":
          wc2 = "2"

      # 5. 최종 문자열 생성
      wcKwase_final = f"{wc1} {wc2}기"      
      wcCorpGB = fields[1]    # 1:부가가치세 예정(일반) 신고서
      wcSingoGB = fields[2]   # 2:예정(중간예납)
      wcChojung = fields[3]   # 3:정기신고 
      wcSangho = fields[4]    # 4:(주)세원종합건설
      wcBizNo = fields[5]     # 5: 158-88-00608 
      wcJupsuWay = fields[6]  # 6:인터넷(변환)
      wcIssueT = fields[7]    # 7:2025-02-13 16:55:44
      wcJubsuNum = fields[8]  # 8:125-2025-2-504388903630
      wcJupsuGB = fields[9]   # 9:접수서류 18종

      wc_corp_gb_txt = {
        "부가가치세 확정(간이)신고서":"C03",
        "부가가치세 확정(일반) 4,10월조기 신고서":"C05",
        "부가가치세 확정(일반) 5,11월조기 신고서":"C06",
        "부가가치세 확정(일반) 신고서":"C07",
        "부가가치세 예정(간이)신고서":"C13",
        "부가가치세 예정(일반) 1,7월조기 신고서":"C15",
        "부가가치세 예정(일반) 2,8월조기 신고서":"C16",
        "부가가치세 예정(일반) 신고서":"C17"
      }.get(wcCorpGB, "기타")
      with connection.cursor() as cursor:
        merge_query = f"""
          MERGE 부가가치세전자신고3 AS A
          USING (
              SELECT '{wcBizNo}' AS biz_no, '{wcKwase_final}' AS wcKwase, '{wc_corp_gb_txt}' AS wcCorpGB_txt
          ) AS B
          ON A.과세기간 = B.wcKwase AND A.사업자등록번호 = B.biz_no AND A.과세유형 = B.wcCorpGB_txt
          WHEN MATCHED THEN
          UPDATE SET 
            과세기간 = '{wcKwase_final}',신고구분='{wcSingoGB}',과세유형= '{wc_corp_gb_txt}',환급구분='{wcChojung}',
            상호='{wcSangho}',사업자등록번호='{wcBizNo}',접수여부='{wcJupsuWay}',신고번호='{wcJubsuNum}',신고시각='{wcIssueT}'
          WHEN NOT MATCHED THEN
          INSERT (
              과세기간, 신고구분, 과세유형, 환급구분, 상호, 사업자등록번호, 접수여부, 신고번호, 신고시각
          ) VALUES (
            '{wcKwase_final}', '{wcSingoGB}', '{wc_corp_gb_txt}', '{wcChojung}', '{wcSangho}', '{wcBizNo}','{wcJupsuWay}', '{wcJubsuNum}', '{wcIssueT}'
          );      
        """
        # print(merge_query) 
        try:
          cursor.execute(merge_query)
          return JsonResponse({"status": "success", "message": "저장완료"}, status=200)
        except:
          return JsonResponse({"error": "맨 앞에는 공백이 없어야 해요"}, status=500)

  return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def mng_vat_update(request):
  if request.method == 'POST':
    seq_no = request.POST.get("seq_no")
    target = request.POST.get("target")
    work_YY = request.POST.get("work_YY")
    work_QT = request.POST.get("work_QT")
    val_raw = unquote(request.POST.get("val"))
    val = val_raw  # 초기값
    today = datetime.date.today().isoformat()  
    # Target 항목 번호 추출 (예: YN_1~YN_17)
    target_suffix = target[-2:].replace("_", "")
    target_num = int(target_suffix) if target_suffix.isdigit() else None

    if target_num and target_num < 12:
      val = "1" if val_raw not in ["false", "0", "", "none", "null"] else "0"

    if target == "YN_12":
        val = val.replace(",", "")

    with connection.cursor() as cursor:
      check_sql = f"SELECT 1 FROM tbl_vat WHERE seq_no=%s AND work_YY=%s AND work_qt=%s"
      cursor.execute(check_sql, [seq_no, work_YY, work_QT])
      exists = cursor.fetchone() is not None

      if exists:
        update_sql = f"""
            UPDATE tbl_vat 
            SET {target} = %s 
            WHERE seq_no = %s AND work_YY = %s AND work_qt = %s
        """
        cursor.execute(update_sql, (val, seq_no, work_YY, work_QT))
      else:
        fields = ["seq_no", "work_YY", "work_QT"] + [f"YN_{i}" for i in range(1, 18)]
        values = [seq_no, work_YY, work_QT]

        for i in range(1, 18):
            if i == target_num:
                values.append(val if i <= 11 else (val if i == 12 else f"'{val}'"))
            else:
                if i <= 11:
                    values.append("0")
                elif i == 12:
                    values.append("0")
                elif i == 13:
                    values.append("''")
                elif i == 14:
                    values.append("-1")
                else:
                    values.append("0")

        placeholders = ",".join(["%s"] * len(values))
        insert_sql = f"INSERT INTO tbl_vat ({','.join(fields)}) VALUES ({placeholders})"
        cursor.execute(insert_sql, values)

      if target=="YN_11":
        if val=='1':
          sql_to_execute = f"UPDATE tbl_vat SET YN_1='{today}' WHERE seq_no='{seq_no}' AND work_YY='{work_YY}' AND work_qt='{work_QT}'"
        else:  
          sql_to_execute = f"UPDATE tbl_vat SET YN_1='' WHERE seq_no='{seq_no}' AND work_YY='{work_YY}' AND work_qt='{work_QT}'"
        print(sql_to_execute)
        cursor.execute(sql_to_execute)
      if target=="YN_2":
        if val=='1':
          sql_to_execute = f"UPDATE tbl_vat SET YN_3='{today}' WHERE seq_no='{seq_no}' AND work_YY='{work_YY}' AND work_qt='{work_QT}'"
        else:  
          sql_to_execute = f"UPDATE tbl_vat SET YN_3='' WHERE seq_no='{seq_no}' AND work_YY='{work_YY}' AND work_qt='{work_QT}'"
        print(sql_to_execute)
        cursor.execute(sql_to_execute)        
    return JsonResponse({"status": "success", "message": "저장되었습니다."})

@csrf_exempt
def path_to_vat_admin(request):
  seq_no = request.POST.get('seq_no')
  memuser = get_object_or_404(MemUser, seq_no=seq_no)
  path = request.POST.get('path','')
  # print(path)
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    d['isFolder'] = True
    d['totalPath'] = path
    totfileArr = []
    for x in os.listdir(path):
      if os.path.isdir(os.path.join(path,x)):
        tmpDur="";tmpQuarter="";dueDate=""
        if x=="1기예정":
          tmpDur = "1월 1일 ~ " +  "3월 31일"
          tmpQuarter = "1Q"
          dueDate = "4월25일"
        elif x=="1기확정":
          tmpDur = "1월 1일 ~ " +  "6월 30일"
          if memuser.biz_type<4: tmpDur = "4월 1일 ~ " +  "6월 30일"
          tmpQuarter = "2Q"
          dueDate = "7월25일"
        elif x=="2기예정":
          tmpDur = "7월 1일 ~ " +  "9월 30일"
          tmpQuarter = "3Q"
          dueDate = "10월25일"
        elif x=="2기확정":
          tmpDur = "7월 1일 ~ " +  "12월 31일"
          if memuser.biz_type<4: tmpDur = "10월 1일 ~ " +  "12월 31일"
          tmpQuarter = "4Q"
          dueDate = "1월25일"
        row = {
          'displayName':x,
          'totalPath':path+"/"+x,
          'singoDur':tmpDur,
          'quarter':tmpQuarter,
          'dueDate':dueDate
        }
        if len(os.listdir(path+"/"+x))>0:
          totfileArr.append(row)
    d['nodes'] = totfileArr
  return JsonResponse(d,safe=False)

@csrf_exempt
def path_to_file_admin(request):
  path = request.GET.get('path',False)
  singoPeriod = request.GET.get('singoPeriod',False)
  quarter = request.GET.get('quarter',False)
  totfileArr = []
  cnt=1
  arrFiles = getTblSheet("_vat")
  if os.path.isdir(path):
    for x in natsort.natsorted(os.listdir(path)):
      if os.path.isfile(path+"/"+x) and x!="Thumbs.db":
        tmpFileName=""
        for f in arrFiles:
          if f['fileName']==os.path.splitext(x)[0]:tmpFileName = f['sheetName']
        fileArr = {'파일명':tmpFileName}
        fileArr['fileNum'] = os.path.splitext(x)[0]
        fileArr['id'] = str(quarter)+"@" + os.path.splitext(x)[0]
        fileArr['totalPath'] = path+"/"+x
        totfileArr.append(fileArr)
        cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr
  return JsonResponse(rtnJson,safe=False)

def getTblSheet(flag):
  strsql = "SELECT seq,trim(fileName),trim(sheetName) from Tbl_Sheet"+flag+" order by seq"
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = []
  if result:
    for r in result:
      row={
        'seq':r[0],
        'fileName':r[1],
        'sheetName':r[2]
      }
      totfileArr.append(row)
  return totfileArr

@csrf_exempt
def get_IssueVatList_Analy(request):
  if request.method != 'POST':
      return JsonResponse({'error': 'Invalid request method'}, status=405)


  data = json.loads(request.body)
  seq_no = data.get("seq_no")
  work_YY = data.get("work_YY")
  work_QT = data.get("work_QT")

  memuser = get_object_or_404(MemUser, seq_no=seq_no)
  biz_no = memuser.biz_no
  biz_type = memuser.biz_type

  if biz_type < 4:
    card_sum_expr = """
        , SUM((
            CASE
                WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN
                    CASE WHEN b.stnd_gb = '1' THEN splCft ELSE 0 END
                WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN
                    CASE WHEN b.stnd_gb = '2' THEN splCft ELSE 0 END
                WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN
                    CASE WHEN b.stnd_gb = '3' THEN splCft ELSE 0 END
                WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN
                    CASE WHEN b.stnd_gb = '4' THEN splCft ELSE 0 END
            END
        )) AS 카드합계
    """
    biz_filter = "c.biz_type < 4"
  else:
      card_sum_expr = """
          , SUM((
              CASE
                  WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN
                      CASE WHEN b.stnd_gb IN ('1', '2') THEN splCft ELSE 0 END
                  WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN
                      CASE WHEN b.stnd_gb IN ('3', '4') THEN splCft ELSE 0 END
              END
          )) AS 카드합계
      """
      biz_filter = "c.biz_type > 3"

  sql = f"""
  WITH STT AS (
      SELECT
          a.사업자등록번호,
          a.과세기간,
          LTRIM(a.과세유형) AS 과세유형
          {card_sum_expr}
      FROM 부가가치세전자신고3 A WITH (NOLOCK)
      LEFT OUTER JOIN TBL_HOMETAX_SCRAP B WITH (NOLOCK)
          ON a.사업자등록번호 = b.biz_no
          AND LEFT(a.과세기간, 4) = b.tran_YY
      WHERE
          a.사업자등록번호 = '{biz_no}'
          AND a.과세유형 <> ''
          AND a.사업자등록번호 IN (
              SELECT biz_no
              FROM mem_user C WITH (NOLOCK)
              WHERE a.사업자등록번호 = c.biz_no
                AND {biz_filter}
          )
      GROUP BY
          a.사업자등록번호,
          a.과세기간,
          LTRIM(a.과세유형)
  )
  SELECT
      a.과세기간,
      a.과세유형,
      (매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액) AS 매출세금계산서,
      (매출과세세금계산서발급세액 + 매출과세매입자발행세금계산서세액 + 예정누락매출세금계산서세액) AS 매출세금계산서세액,
      매출과세카드현금발행금액 AS 카드매출,
      (매출과세기타금액 + 예정누락매출과세기타금액) AS 기타매출,
      (매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액) AS 영세율매출,
      (매입세금계산서수취일반금액 + 매입세금계산서수취고정자산금액 + 예정누락매입신고세금계산서금액 + 매입자발행세금계산서매입금액) AS 매입세금계산서,
      (매입세금계산서수취일반세액 + 매입세금계산서수취고정자산세액 + 예정누락매입신고세금계산서세액 + 매입자발행세금계산서매입세액) AS 매입세금계산서세액,
      그밖의공제매입명세합계금액 AS 기타매입,
      그밖의공제매입명세합계세액 AS 기타매입세액,
      공제받지못할매입합계금액 AS 불공제,
      공제받지못할매입합계세액 AS 불공제세액,
      경감공제합계세액 AS 경감공제세액,
      면세사업합계수입금액 AS 면세매출,
      계산서수취금액 AS 면세매입,
      (차감납부할세액 + 매입자납부특례기납부세액) AS 실제납부할세액,
      (예정신고미환급세액 + 예정고지세액) AS 예정세액,
      매입세금계산서수취고정자산금액,
      과세표준금액 AS 매출합계,
      매입세액합계금액 AS 매입합계,
      신용카드수취기타카드,
      신용카드수취현금영수증,
      신용카드수취화물복지,
      신용카드수취사업용카드,
      공제받지못할매입세액명세,
      의제매입세액공제,
      재활용폐자원등매입세액,
      납부환급세액,
      매입세금계산서수취고정자산세액,
      산출세액,
      가산세액계,
      카드합계 AS 카드현영사용총액
  FROM
      부가가치세전자신고3 A,
      STT B
  WHERE
      A.사업자등록번호 = B.사업자등록번호
      AND A.과세기간 = B.과세기간
      AND A.과세유형 = B.과세유형
  ORDER BY
      a.과세기간 DESC,
      a.신고구분 DESC,
      a.신고시각 DESC,
      a.과세유형
  """
  with connection.cursor() as cursor:
      cursor.execute(sql)
      rows = cursor.fetchall()

  totalList = []
  for r in rows:
      # 문자열 index 접근 예외 방지
      def safe_slice(val, start, end):
          return str(val)[start:end] if val else ''

      wcCorpGB_txt = {"C03": "확정", "C07": "확정", "C13": "예정", "C17": "예정"}.get(r[1], "")
      tmpKi = r[0][6:7]
      startDt, endDt, work_qt = "", "", ""

      if r[1] == "C03":
          startDt, endDt = "1월 1일", "12월 31일"
      elif r[1] == "C13":
          startDt, endDt = "1월 1일", "6월 30일"
      elif r[1] == "C07":
          if biz_type < 4:
              startDt, endDt, work_qt = ("4월 1일", "6월 30일", "2분기") if tmpKi == "1" else ("10월 1일", "12월 31일", "4분기")
          else:
              startDt, endDt, work_qt = ("1월 1일", "6월 30일", "상반기") if tmpKi == "1" else ("7월 1일", "12월 31일", "하반기")
      elif r[1] == "C17":
          startDt, endDt, work_qt = ("1월 1일", "3월 31일", "1분기") if tmpKi == "1" else ("7월 1일", "9월 30일", "3분기")

      totalList.append({
          '과세기간': r[0] + wcCorpGB_txt,
          '과세유형': r[1],
          '매출세금계산서': r[2],
          '매출세금계산서세액': r[3],
          '카드매출': r[4],
          '기타매출': r[5],
          '영세율매출': r[6],
          '매입세금계산서': r[7],
          '매입세금계산서세액': r[8],
          '기타매입': r[9],
          '기타매입세액': r[10],
          '불공제': r[11],
          '불공제세액': r[12],
          '경감공제세액': r[13],
          '면세매출': r[14],
          '면세매입': r[15],
          '실제납부할세액': r[16],
          '예정세액': r[17],
          '납부세액': int(r[16]) + int(r[17]),
          '매입세금계산서수취고정자산금액': r[18],
          '매출합계': r[19],
          '매입합계': r[20],
          '신용카드수취기타카드': safe_slice(r[21], 60, 73),
          '신용카드수취현금영수증': safe_slice(r[22], 60, 73),
          '신용카드수취화물복지': safe_slice(r[23], 60, 73),
          '신용카드수취사업용카드': safe_slice(r[24], 60, 73),
          '공제받지못할매입세액명세': r[25],
          '의제매입세액공제': safe_slice(r[26], 40, 54),
          '재활용폐자원등매입세액': safe_slice(r[27], 40, 54),
          '납부환급세액': r[28],
          '매입세금계산서수취고정자산세액': r[29],
          '산출세액': r[30],
          '가산세액계': r[31],
          '카드현영사용총액': str(r[32]),
          'startDt': startDt,
          'endDt': endDt,
          'seq_no':seq_no,
          'work_YY':r[0][:4],
          'work_QT':work_qt
      })

  return JsonResponse({'totIssueList': totalList}, safe=False)



@csrf_exempt
def get_IssueVatList(request):
  if request.method == 'POST':
    data = json.loads(request.body)  # JSON 파싱
    seq_no = data.get("seq_no")
    work_YY = data.get("work_YY")
    work_QT = data.get("work_QT")
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    biz_no = memuser.biz_no
    biz_type = memuser.biz_type
    kwasekikan,ks2,SKGB = setKwasekikan(work_YY,work_QT)
    
    today = datetime.datetime.now()
    month_val = today.month
    is_issue_date = False
    if biz_type <= 4:
        if month_val in [1, 2, 4, 7, 10]:
            is_issue_date = True
    elif biz_type == 5:
        if month_val in [1, 2, 7]:
            is_issue_date = True    

    response_data = []
    with connection.cursor() as cursor:
      cursor.execute("select 과세기간,신고구분,과세유형,환급구분 from 부가가치세전자신고3 "
                      "where 사업자등록번호 =  %s order by 과세기간 desc, 신고구분 desc,신고시각 desc, 과세유형 asc", [biz_no])
      rows = cursor.fetchall()
      if rows:
        for idx, row in enumerate(rows, start=0):
          if is_issue_date and idx == 0 and not (row[0] == kwasekikan and row[2] == SKGB):
             response_data.append({
              "과세기간": kwasekikan,
              "신고구분": "신고전",
              "과세유형": "",
              "환급구분": ""
          })
          response_data.append({
              "과세기간": row[0],
              "신고구분": row[1],
              "과세유형": row[2],
              "환급구분": row[3]
          })
      # print(response_data)
      return JsonResponse({"status": "success", "data": response_data})
  return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)

def setKwasekikan(work_YY,work_QT):
  kwasekikan=ks2=SKGB = ""
  if work_QT == 1:
    kwasekikan = f"{work_YY}년 1기"
    ks2 = "예정(정기)"
    SKGB = "C17"
  elif work_QT == 2:
    kwasekikan = f"{work_YY}년 1기"
    ks2 = "확정(정기)"
    SKGB = "C07"
  elif work_QT == 3:
    kwasekikan = f"{work_YY}년 2기"
    ks2 = "예정(정기)"
    SKGB = "C17"
  elif work_QT == 4:
    kwasekikan = f"{work_YY}년 2기"
    ks2 = "확정(정기)"
    SKGB = "C07"     
  return kwasekikan,ks2,SKGB

@csrf_exempt
def get_TongVat(request):
  if request.method == 'POST':
    data = json.loads(request.body)  # JSON 파싱
    seq_no = data.get("seq_no")
    work_YY = data.get("work_YY")
    work_QT = data.get("work_QT")
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    biz_no = memuser.biz_no
    biz_type = memuser.biz_type
    kwasekikan = data.get("kwasekikan")
    KSUH = data.get("KSUH")  
    SKGB = data.get("SKGB")
    txtSpecial = isSKGB_C07(biz_no,kwasekikan)#true면 예정신고 있음
    # 결과 데이터 가공
    strsql = build_vatElec_query(biz_no, kwasekikan, KSUH)
    # print(strsql)
    vatElec = None
    with connection.cursor() as cursor:
      cursor.execute(strsql)
      rs_vatElec = dictfetchone(cursor)
      if SKGB != "신고전":
        vatElec = process_vat_data(rs_vatElec)
        # print(rs_vatElec)
    strsql = f"""
      select RIGHT(tran_mm,2) as work_MM, SaleGubun,MM_Scnt,Tot_StlAmt,Etc_StlAmt,PurcEuCardAmt from Tbl_HomeTax_SaleCard 
      where Tran_YY='{work_YY}' and Seq_No={seq_no}  order by tran_mm,SaleGubun 
    """
    # print(strsql) 
    with connection.cursor() as cursor:
      cursor.execute(strsql)
      rs_SaleCard = dict_fetchall(cursor)   
      sale_card_data = process_SaleCard_data(rs_SaleCard, kwasekikan, KSUH, biz_type,txtSpecial) 
    strKSUH = "확정"
    if KSUH=="C17": strKSUH = "예정"
    str_nm = f"select * from 부가가치세통합조회 where 과세기수='{kwasekikan}' and 신고구분='{strKSUH}' and 사업자등록번호='{biz_no}'"     
    # 법인이 확정신고기간인데 예정신고 안했으면 예정기간 통합자료를 합산해야 한다
    if biz_type<4 and KSUH=="C07" and not txtSpecial:
      str_nm = f"""
        select 
          max(과세기수) 과세기수, max(과세기간) 과세기간,max(신고구분) 신고구분,max(상호) 상호,max(신고유형) 신고유형,max(관할서) 관할서,max(법인예정고지대상) 법인예정고지대상,max(간이부가율) 간이부가율,max(주업종코드) 주업종코드,
          sum(매출전자세금계산서공급가액) 매출전자세금계산서공급가액,sum(매출전자세금계산서세액) 매출전자세금계산서세액,sum(매출전자계산서공급가액) 매출전자계산서공급가액, 
          sum(매출신용카드공급가액) 매출신용카드공급가액,sum(매출신용카드세액) 매출신용카드세액, 
          sum(매출현금영수증공급가액) 매출현금영수증공급가액,sum(매출현금영수증세액) 매출현금영수증세액,sum(수출신고필증) 수출신고필증,sum(구매확인서등) 구매확인서등, sum(매출판매대행) 매출판매대행, 
          sum(매입전자세금계산서공급가액) 매입전자세금계산서공급가액,sum(매입전자세금계산서세액) 매입전자세금계산서세액,sum(매입전자계산서공급가액) 매입전자계산서공급가액, sum(매입신용카드세액) 매입신용카드세액,
          sum(매입신용카드공급가액) 매입신용카드공급가액, sum(매입현금영수증공급가액) 매입현금영수증공급가액,sum(매입현금영수증세액) 매입현금영수증세액,sum(매입복지카드공급가액) 매입복지카드공급가액,sum(매입복지카드세액) 매입복지카드세액,
          max(예정고지세액일반) 예정고지세액일반, max(예정미환급세액일반) 예정미환급세액일반,max(예정부과세액간이) 예정부과세액간이,max(예정신고세액간이) 예정신고세액간이,
          max(매입자납부특례기납부세액) 매입자납부특례기납부세액, max(현금매출명세서) 현금매출명세서,max(부동산임대공급가액명세서) 부동산임대공급가액명세서 
        from 부가가치세통합조회 where 과세기수='{kwasekikan}'  and 사업자등록번호='{biz_no}'
      """
    # print(str_nm)
    tong_data = None
    with connection.cursor() as cursor:
      cursor.execute(str_nm)
      rs_Tong = dictfetchone(cursor)     
      tong_data = process_Tong_data(biz_no, work_YY, work_QT,rs_Tong,vatElec)
    
    return JsonResponse({
        "status": "success",
        "sales_result": tong_data["recordset_result_Hmtx"],
        "purchase_result": tong_data["issue_result_Hmtx"],
        "expected_tax_result": tong_data["diff_result_Hmtx"],
        "total_result": eval("[" + sale_card_data["recordset_total"] + "]") if sale_card_data["recordset_total"] else [],
        "sinca_result": eval("[" + sale_card_data["recordset_sinca"] + "]") if sale_card_data["recordset_sinca"] else [],
        "pmdh_result": eval("[" + sale_card_data["recordset_pmdh"] + "]") if sale_card_data["recordset_pmdh"] else [],
        "cash_result": eval("[" + sale_card_data["recordset_cash"] + "]") if sale_card_data["recordset_cash"] else [],
        "addTxt": tong_data["addTxt"],
    })
  return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)

def isSKGB_C07(biz_no,kwasekikan):
  strsql = f"select 과세기간 from 부가가치세전자신고3 where  사업자등록번호='{biz_no}' and 과세기간='{kwasekikan}'  and 과세유형='C17'"
  with connection.cursor() as cursor:
    cursor.execute(strsql)
    rs = dictfetchone(cursor)    
    if rs: 
      return True
    else:
      return False

@csrf_exempt
def isVatNapbu(request):
    import json

    try:
        body = json.loads(request.body)
        seq_no = body.get('seq_no')
        work_YY = body.get('work_YY')  
        work_QT = body.get('work_QT')  
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({'error': 'Invalid input'}, status=400)

    if not seq_no:
        return JsonResponse({'result': False})

    strKi = '1기' if int(work_QT) <= 2 else '2기'
    KSUH = 'C07'
    if int(work_QT) in (1,3):
        KSUH = 'C17'

    memuser = get_object_or_404(MemUser, seq_no=seq_no)

    sql_query = f"""
        SELECT 차감납부할세액 
        FROM 부가가치세전자신고3
        WHERE 사업자등록번호 = '{memuser.biz_no}' 
          AND 과세기간 = '{work_YY}년 {strKi}' 
          AND 과세유형 = '{KSUH}'
    """  
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        row = cursor.fetchone()

        if row and row[0] > 0:
            return JsonResponse({'result': True})
        else:
            return JsonResponse({'result': False})

def parse_signed_number(val: str) -> float:
    if not val:
        return 0.0
    val = val.strip()
    if val.endswith("}"):
        return float("-" + val[:-1] + "0")
    elif val.endswith("P"):
        return float(val[:-1]) * -1
    return float(val)

#부가가치세 전자신고 데이터 가져오기
def process_vat_data(rs_vat):
  now_saleNonTaxInvoice = "";amt_saleNonTaxInvoice = 0
  if rs_vat.get("전자외매출세금계산서합계", "").strip():
    now_saleNonTaxInvoice = mid_union(rs_vat["전자외매출세금계산서합계"], 26, 15)
    if now_saleNonTaxInvoice.endswith("}"):
        now_saleNonTaxInvoice = "-" + now_saleNonTaxInvoice[:14] + "0"

    if now_saleNonTaxInvoice.endswith("P") or now_saleNonTaxInvoice.endswith("L"):
        now_saleNonTaxInvoice = float(now_saleNonTaxInvoice[:-1]) * -1
    else:
        amt_saleNonTaxInvoice = float(now_saleNonTaxInvoice)

  CardSaleTotal = rs_vat.get("신용카드발행집계표", "").strip()

  elec_saleTI = float(rs_vat.get("매출과세세금계산서발급금액", 0)) + float(rs_vat.get("매출영세율세금계산서발급금액", 0)) - amt_saleNonTaxInvoice
  elec_saleNTI = float(rs_vat.get("계산서교부금액", 0))

  elec_saleSC = float(mid_union(CardSaleTotal, 25, 13)) if CardSaleTotal else 0
  if elec_saleSC:
      elec_saleSC = round(elec_saleSC / 1.1, 0)

  elec_saleSCvat = float(mid_union(CardSaleTotal, 38, 13)) if CardSaleTotal else 0
  if elec_saleSCvat:
      elec_saleSCvat = round(elec_saleSCvat / 1.1, 0)

  elecSaleKita = float(rs_vat.get("매출과세기타금액", 0))

  now_paperExpTaxInvoice = mid_union(rs_vat.get("전자외매입세금계산서합계", ""), 26, 15)
  if now_paperExpTaxInvoice == "":
      amt_paperExpTaxInvoice = 0
  else:
      if now_paperExpTaxInvoice.endswith("}"):
          amt_paperExpTaxInvoice = float(now_paperExpTaxInvoice.replace("}", "")) * -1
      else:
          amt_paperExpTaxInvoice = float(now_paperExpTaxInvoice)

  elec_costTI = (
      float(rs_vat.get("매입세금계산서수취일반금액", 0)) +
      float(rs_vat.get("매입세금계산서수취고정자산금액", 0)) +
      float(rs_vat.get("예정누락매입신고세금계산서금액", 0)) -
      amt_paperExpTaxInvoice
  )
  elec_costNTI = float(rs_vat.get("계산서수취금액", 0))

  def parse_card_data(field):
      raw = rs_vat.get(field, "")
      amt, vat, sign = 0, 0, 1
      if raw:
          amt = float(mid_union(raw, 60, 13))
          if mid_union(raw, 73, 1) == "-":
              sign = -1
          amt *= sign
          vat = float(mid_union(raw, 84, 13)) * sign
      return amt, vat

  elec_costCard1, elec_costCard1Vat = parse_card_data("신용카드수취기타카드")
  elec_costCard2, elec_costCard2Vat = parse_card_data("신용카드수취현금영수증")
  elec_costCard3, elec_costCard3Vat = parse_card_data("신용카드수취화물복지")
  elec_costCard4, elec_costCard4Vat = parse_card_data("신용카드수취사업용카드")

  elec_pretax = float(rs_vat.get("예정고지세액", 0))
  elec_pretaxNot = float(rs_vat.get("예정신고미환급세액", 0))
  elec_purchaseSpecial = float(rs_vat.get("매입자납부특례기납부세액", 0))

  return {
      "elec_saleTI": elec_saleTI,
      "elec_saleNTI": elec_saleNTI,
      "elec_saleSC": elec_saleSC,
      "elec_saleSCvat": elec_saleSCvat,
      "elecSaleKita": elecSaleKita,
      "elec_costTI": elec_costTI,
      "elec_costNTI": elec_costNTI,
      "elec_costCard1": elec_costCard1,
      "elec_costCard1Vat": elec_costCard1Vat,
      "elec_costCard2": elec_costCard2,
      "elec_costCard2Vat": elec_costCard2Vat,
      "elec_costCard3": elec_costCard3,
      "elec_costCard3Vat": elec_costCard3Vat,
      "elec_costCard4": elec_costCard4,
      "elec_costCard4Vat": elec_costCard4Vat,
      "elec_pretax": elec_pretax,
      "elec_pretaxNot": elec_pretaxNot,
      "elec_purchaseSpecial": elec_purchaseSpecial,
  }

#Tbl_HomeTax_SaleCard 카드매출 데이터 가져오기
def process_SaleCard_data(rows, kwasekikan, singokubun_B, biz_type, txtSpecial):
  from collections import defaultdict
  # rows가 None이면 빈 리스트로 초기화
  if not rows:
      rows = []
  # Init result containers and sums
  result = defaultdict(str)
  sums = defaultdict(float)

  # print(rows)
  for row in rows:
    mm = int(row["work_MM"])
    gubun = row["SaleGubun"].strip()
    tot_amt = float(row["Tot_StlAmt"])
    etc_amt = float(row["Etc_StlAmt"])
    purc_amt = float(row["PurcEuCardAmt"])
    count = float(row["MM_Scnt"])

    quarter = (mm - 1) // 3 + 1

    if gubun.startswith("신용카드"):
        result["recordset_sinca"] += f"['{mm}월','{fmt(tot_amt)}','{fmt(etc_amt)}','{fmt(purc_amt)}','{int(count)}'],"
        sums[f"sum_TotalSinca_{quarter}"] += tot_amt
        sums[f"sum_EtcSinca_{quarter}"] = sums[f"sum_TotalSinca_{quarter}"] / 1.1
        sums[f"sum_PurSinca_{quarter}"] = sums[f"sum_TotalSinca_{quarter}"] / 1.1 * 0.1
        sums[f"sum_CntSinca_{quarter}"] += count
    elif gubun == "현금영수증":
        result["recordset_cash"] += f"['{mm}월','{fmt(tot_amt)}','{fmt(etc_amt)}','{fmt(purc_amt)}','{int(count)}','{gubun}'],"
        sums[f"sum_Totalcash_{quarter}"] += tot_amt
        sums[f"sum_Etccash_{quarter}"] += etc_amt
        sums[f"sum_Purcash_{quarter}"] += purc_amt
        sums[f"sum_Cntcash_{quarter}"] += count
    else:
        result["recordset_pmdh"] += f"['{mm}월','{fmt(tot_amt)}','{fmt(etc_amt)}','{fmt(purc_amt)}','{int(count)}','{gubun}'],"
        sums[f"sum_TotalPmdh_{quarter}"] += tot_amt
        sums[f"sum_kkkePmdh_{quarter}"] = sums[f"sum_TotalPmdh_{quarter}"] / 1.1
        sums[f"sum_TaxPmdh_{quarter}"] = sums[f"sum_TotalPmdh_{quarter}"] / 1.1 * 0.1
        sums[f"sum_EtcPmdh_{quarter}"] += etc_amt
        sums[f"sum_PurPmdh_{quarter}"] += purc_amt
        sums[f"sum_CntPmdh_{quarter}"] += count

  # 종합합계 계산 (분기/반기/연간)
  def sum_quarters(prefix, keys):
      return sum(sums.get(f"{prefix}_{k}", 0) for k in keys)

  for prefix, label in [("sinca", "Sinca"), ("Pmdh", "Pmdh"), ("cash", "cash")]:
      for q in range(1, 5):
          result[f"recordset_{prefix}{q}"] = f"['{q}분기','{fmt(sums[f'sum_Total{label}_{q}'])}','{fmt(sums[f'sum_Etc{label}_{q}'])}','{fmt(sums[f'sum_Pur{label}_{q}'])}','{fmt(sums[f'sum_Cnt{label}_{q}'])}'],"
      result[f"recordset_{prefix}5"] = f"['<b>상반기</b>','{fmt(sum_quarters(f'sum_Total{label}', [1,2]))}','{fmt(sum_quarters(f'sum_Etc{label}', [1,2]))}','{fmt(sum_quarters(f'sum_Pur{label}', [1,2]))}','{fmt(sum_quarters(f'sum_Cnt{label}', [1,2]))}'],"
      result[f"recordset_{prefix}6"] = f"['<b>하반기</b>','{fmt(sum_quarters(f'sum_Total{label}', [3,4]))}','{fmt(sum_quarters(f'sum_Etc{label}', [3,4]))}','{fmt(sum_quarters(f'sum_Pur{label}', [3,4]))}','{fmt(sum_quarters(f'sum_Cnt{label}', [3,4]))}'],"
      result[f"recordset_{prefix}"] = ''.join(result[f"recordset_{prefix}{i}"] for i in [1,2,5,3,4,6]).rstrip(',')

  for i in [1,2,5,3,4,6]:
    result[f"recordset_total{i}"] = (
        f"['{f'{i}분기' if i <= 4 else '<b>상반기</b>' if i==5 else '<b>하반기</b>'}',"
        f"'{fmt(sum_quarters('sum_TotalSinca', [i]) + sum_quarters('sum_TotalPmdh', [i]))}',"
        f"'{fmt(sum_quarters('sum_EtcSinca', [i]) + sum_quarters('sum_kkkePmdh', [i]))}',"
        f"'{fmt(sum_quarters('sum_PurSinca', [i]) + sum_quarters('sum_TaxPmdh', [i]))}',"
        f"'{fmt(sum_quarters('sum_CntSinca', [i]) + sum_quarters('sum_CntPmdh', [i]))}'],"
    )
  result["recordset_total"] = ''.join(result[f"recordset_total{i}"] for i in [1,2,5,3,4,6])
  result["recordset_total"] = result["recordset_total"].rstrip(',')

  # 통합조회 조건별 계산
  total_sinca, etc_sinca, pur_sinca = 0, 0, 0
  cond = kwasekikan + singokubun_B
  if cond == "1기C17":
      total_sinca = sums["sum_TotalSinca_1"] + sums["sum_TotalPmdh_1"]
      etc_sinca = sums["sum_EtcSinca_1"] + sums["sum_kkkePmdh_1"]
      pur_sinca = sums["sum_PurSinca_1"] + sums["sum_TaxPmdh_1"]
  elif cond == "1기C07":
      if biz_type < 4 and txtSpecial:
          total_sinca = sums["sum_TotalSinca_2"] + sums["sum_TotalPmdh_2"]
          etc_sinca = sums["sum_EtcSinca_2"] + sums["sum_kkkePmdh_2"]
          pur_sinca = sums["sum_PurSinca_2"] + sums["sum_TaxPmdh_2"]
      else:
          total_sinca = sum_quarters("sum_TotalSinca", [1,2]) + sum_quarters("sum_TotalPmdh", [1,2])
          etc_sinca = sum_quarters("sum_EtcSinca", [1,2]) + sum_quarters("sum_kkkePmdh", [1,2])
          pur_sinca = sum_quarters("sum_PurSinca", [1,2]) + sum_quarters("sum_TaxPmdh", [1,2])
  elif cond == "2기C17":
      total_sinca = sums["sum_TotalSinca_3"] + sums["sum_TotalPmdh_3"]
      etc_sinca = sums["sum_EtcSinca_3"] + sums["sum_kkkePmdh_3"]
      pur_sinca = sums["sum_PurSinca_3"] + sums["sum_TaxPmdh_3"]
  elif cond == "2기C07":
      if biz_type < 4 and txtSpecial:
          total_sinca = sums["sum_TotalSinca_4"] + sums["sum_TotalPmdh_4"]
          etc_sinca = sums["sum_EtcSinca_4"] + sums["sum_kkkePmdh_4"]
          pur_sinca = sums["sum_PurSinca_4"] + sums["sum_TaxPmdh_4"]
      else:
          total_sinca = sum_quarters("sum_TotalSinca", [3,4]) + sum_quarters("sum_TotalPmdh", [3,4])
          etc_sinca = sum_quarters("sum_EtcSinca", [3,4]) + sum_quarters("sum_kkkePmdh", [3,4])
          pur_sinca = sum_quarters("sum_PurSinca", [3,4]) + sum_quarters("sum_TaxPmdh", [3,4])

  result["sum_TotalSinca"] = fmt(total_sinca)
  result["sum_EtcSinca"] = fmt(etc_sinca)
  result["sum_PurSinca"] = fmt(pur_sinca)
  # print(result)
  return result

#통합조회
def process_Tong_data(biz_no,work_YY,work_QT,rs,vatElec):
  # None 체크 및 기본값 처리
  if not rs:
      return {
          "recordset_result_Hmtx": [],
          "issue_result_Hmtx": [],
          "diff_result_Hmtx": [],
          "addTxt": "[데이터 누락]",
      }
  if not vatElec:
    elec_saleTI = 0
    elec_saleNTI= 0
    elec_saleSC = 0
    elec_saleSCvat = 0
    elecSaleKita = 0
    elec_costTI = 0
    elec_costNTI = 0
    elec_costCard1 = 0
    elec_costCard2 = 0
    elec_costCard3 = 0
    elec_costCard4 = 0
    elec_pretax = 0
    elec_pretaxNot = 0
    elec_purchaseSpecial = 0
  else:
    elec_saleTI = vatElec["elec_saleTI"]
    elec_saleNTI= vatElec["elec_saleNTI"]
    elec_saleSC = vatElec["elec_saleSC"]
    elec_saleSCvat = vatElec["elec_saleSCvat"]
    elecSaleKita = vatElec["elecSaleKita"]
    elec_costTI = vatElec["elec_costTI"]
    elec_costNTI = vatElec["elec_costNTI"]
    elec_costCard1 = vatElec["elec_costCard1"]
    elec_costCard2 = vatElec["elec_costCard2"]
    elec_costCard3 = vatElec["elec_costCard3"]
    elec_costCard4 = vatElec["elec_costCard4"]
    elec_pretax = vatElec['elec_pretax']
    elec_pretaxNot = vatElec['elec_pretaxNot']
    elec_purchaseSpecial = vatElec['elec_purchaseSpecial']
  print(rs)
  # 매출 계산
  saleTI = float(rs["매출전자세금계산서공급가액"])
  saleTIvat = float(rs["매출전자세금계산서세액"])
  saleNTI = float(rs["매출전자계산서공급가액"])

  saleSinca = float(rs["매출신용카드공급가액"]) / 1.1 + float(rs["매출판매대행"]) / 1.1
  saleSincavat = (float(rs["매출신용카드공급가액"]) / 1.1) * 0.1 + (float(rs["매출판매대행"]) / 1.1) * 0.1
  saleCash = float(rs["매출현금영수증공급가액"])
  saleCashvat = float(rs["매출현금영수증세액"])

  saleExport = float(rs["수출신고필증"])
  saleExport2 = float(rs["구매확인서등"])
  saleDaehang = float(rs["매출판매대행"]) / 1.1
  saleDaehangvat = saleDaehang * 0.1

  # 매입 계산
  costTI = float(rs["매입전자세금계산서공급가액"])
  costTIvat = float(rs["매입전자세금계산서세액"])
  costNTI = float(rs["매입전자계산서공급가액"])
  costSinca = float(rs["매입신용카드공급가액"])
  costSincavat = float(rs["매입신용카드세액"])
  costCash = float(rs["매입현금영수증공급가액"])
  costCashvat = float(rs["매입현금영수증세액"])
  costBockji = float(rs["매입복지카드공급가액"])
  costBockjivat = float(rs["매입복지카드세액"])

  # 예정고지 및 기타
  pretax = float(rs["예정고지세액일반"])
  pretaxNot = float(rs["예정미환급세액일반"])
  pretaxKani = float(rs["예정부과세액간이"])
  pretaxKaniSingo = float(rs["예정신고세액간이"])
  purchaseSpecial = float(rs["매입자납부특례기납부세액"])
  salecashSheet = rs["현금매출명세서"]
  realestateSheet = rs["부동산임대공급가액명세서"]

  addTxt = ""
  if salecashSheet == "Y":
      addTxt += "  [현금매출명세서 제출대상]"
  if realestateSheet == "Y":
      addTxt += "  [부동산임대공급가액명세서 제출대상]"

  # 검증 로직
  img_warning = "😡"
  img_smile = "😄"

  # 1. 각각의 항목별 검증
  img_saleTI     = img_smile if (saleTI - elec_saleTI) == 0 else img_warning
  img_saleNTI    = img_smile if (saleNTI - elec_saleNTI) == 0 else img_warning
  img_saleSC     = img_warning if (saleSinca > elec_saleSC and abs(saleSinca - elec_saleSC) > 1000) or (elec_saleSC - saleSinca) > saleSinca * 0.3 else img_smile
  img_saleCash   = img_smile if abs(saleCash - elec_saleSCvat) <= 1000 else img_warning
  img_saleDH     = img_warning if (saleDaehang > elecSaleKita and abs(saleDaehang - elecSaleKita) > 1000) or (elecSaleKita - saleDaehang) > saleDaehang * 0.3 else img_smile

  img_costTI     = img_smile if (costTI - elec_costTI) == 0 else img_warning
  img_costNTI    = img_smile if (costNTI - elec_costNTI) == 0 else img_warning
  img_costCard1  = img_smile  # 주석 처리됨
  img_costCard2  = img_smile if costCash <= elec_costCard2 else img_warning
  img_costCard3  = img_smile if costBockji <= elec_costCard3 else img_warning
  img_costCard4  = img_smile if costSinca <= elec_costCard4 else img_warning

  invNum = pretax - elec_pretax
  invNum += pretaxNot - elec_pretaxNot
  invNum += purchaseSpecial - elec_purchaseSpecial
  img_pretax = img_smile if invNum == 0 else img_warning

  # ⚠️ 경고 카운트 (😡의 개수 + invNum)
  warn_images = [
      img_saleTI, img_saleNTI, img_saleSC, img_saleCash, img_saleDH,
      img_costTI, img_costNTI, img_costCard1, img_costCard2, img_costCard3, img_costCard4,
      img_pretax  # 예정고지 포함
  ]

  sum_warn = warn_images.count(img_warning)
  # MERGE 문 생성
  str_mg = f"""
  MERGE Tbl_vat AS A
  USING (
      SELECT
          (SELECT seq_no FROM mem_user WHERE biz_no = '{biz_no}') AS seq_no,
          '{work_YY}' AS work_yy,
          '{work_QT}' AS work_qt
  ) AS B
  ON A.seq_no = B.seq_no AND A.work_yy = B.work_yy AND A.work_qt = B.work_qt
  WHEN MATCHED THEN
      UPDATE SET YN_14 = {sum_warn}
  WHEN NOT MATCHED THEN
      INSERT (
          seq_no, work_YY, work_QT,
          YN_1, YN_2, YN_3, YN_4, YN_5, YN_6, YN_7,
          YN_8, YN_9, YN_10, YN_11, YN_12, YN_13,
          YN_14, YN_15, YN_16, YN_17
      )
      VALUES (
          (SELECT seq_no FROM mem_user WHERE biz_no = '{biz_no}'),
          '{work_YY}', '{work_QT}',
          0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0,
          {sum_warn}, 0, 0, 0
      );
  """
  with connection.cursor() as cursor:
    # print(str_mg)
    cursor.execute(str_mg)

  # 결과 데이터 구성
  recordset_result_Hmtx = [
      ["전자매출세금계산서", fmt(saleTI + saleTIvat), fmt(saleTI), fmt(saleTIvat), fmt(elec_saleTI), img_saleTI],
      ["전자매출계산서", fmt(saleNTI), fmt(saleNTI), "", fmt(elec_saleNTI), img_saleNTI],
      ["신카+대행(24년통합)", fmt(saleSinca + saleSincavat), fmt(saleSinca), fmt(saleSincavat), fmt(elec_saleSC), img_saleSC],
      ["현금영수증매출", fmt(saleCash + saleCashvat), fmt(saleCash), fmt(saleCashvat), fmt(elec_saleSCvat), img_saleCash],
      ["기타매출", 0, 0, 0, fmt(elecSaleKita), ""]
  ]
  
  issue_result_Hmtx = [
      ["전자매입세금계산서", fmt(costTI + costTIvat), fmt(costTI), fmt(costTIvat), fmt(elec_costTI), img_costTI],
      ["전자매입계산서", fmt(costNTI), fmt(costNTI), "", fmt(elec_costNTI), img_costNTI],
      ["사업용신용카드", fmt(costSinca + costSincavat), fmt(costSinca), fmt(costSincavat), fmt(elec_costCard4), img_costCard4],
      ["현금영수증매입", fmt(costCash + costCashvat), fmt(costCash), fmt(costCashvat), fmt(elec_costCard2), img_costCard2],
      ["화물복지카드매입", fmt(costBockji + costBockjivat), fmt(costBockji), fmt(costBockjivat), fmt(elec_costCard3), img_costCard3],
      ["기타신용카드매입", "", "", fmt(elec_costCard1), "", img_costCard1]
  ]

  diff_result_Hmtx = [
      ["홈택스", fmt(pretax), fmt(pretaxNot), fmt(pretaxKani), fmt(pretaxKaniSingo), fmt(purchaseSpecial), img_pretax],
      ["전자신고", fmt(elec_pretax), fmt(elec_pretaxNot), "", "", fmt(elec_purchaseSpecial), img_pretax]
  ]
  return {
      "recordset_result_Hmtx": recordset_result_Hmtx,
      "issue_result_Hmtx": issue_result_Hmtx,
      "diff_result_Hmtx": diff_result_Hmtx,
      "addTxt": addTxt,
  }

#검증
@csrf_exempt
def get_InspectVat(request):
  if request.method == 'POST':
    data = json.loads(request.body)  # JSON 파싱
    seq_no = data.get("seq_no")
    work_YY = data.get("work_YY")
    work_QT = data.get("work_QT")
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    biz_no = memuser.biz_no
    biz_type = memuser.biz_type
    kwasekikan = data.get("kwasekikan")
    SKGB = data.get("SKGB")
    KSUH = data.get("KSUH")
    strsql = build_vatInspect_query(seq_no, work_YY, work_QT, kwasekikan, KSUH)
    # print(strsql)
    with connection.cursor() as cursor:
      cursor.execute(strsql)
      rs = dictfetchone(cursor)
      if rs:
        try:
          result =  get_tax_inspection_result(rs, work_YY, work_QT, biz_no, biz_type,kwasekikan, KSUH,seq_no)
          # print(result["rows"])
          return JsonResponse({"status": "success", "data": result["rows"]})
        except:
          return JsonResponse({"error": "fail", "data": "검증불가 : 전자신고파일을 재업로드하세요."})
      else:
        return JsonResponse({"error": "fail", "data": "검증불가 : 신고전."})
  return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)

def build_vatInspect_query(seq_no, work_YY, work_QT, kwasekikan, KSUH):
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    biz_no = memuser.biz_no
    biz_type = memuser.biz_type
    work_yy = int(work_YY)
    work_qt = int(work_QT)
    qt_period = f"{work_yy}년 {'1기' if work_qt in [1,3] else '2기'}"
    base_select = ["""
      SELECT 매출과세세금계산서발급금액,
      매출과세세금계산서발급세액,
      매출과세매입자발행세금계산서금액,
      매출과세매입자발행세금계산서세액,
      매출과세카드현금발행금액,
      매출과세카드현금발행세액,
      매출과세기타금액,
      매출과세기타세액,
      매출영세율세금계산서발급금액,
      매출영세율기타금액,
      매출예정누락합계금액,
      매출예정누락합계세액,
      예정누락매출세금계산서금액,
      예정누락매출세금계산서세액,
      예정누락매출과세기타금액,
      예정누락매출과세기타세액,
      예정누락매출영세율세금계산서금액,
      예정누락매출영세율기타금액,
      예정누락매출명세합계금액,
      예정누락매출명세합계세액,
      매출대손세액가감세액,
      과세표준금액,
      산출세액,
      매입세금계산서수취일반금액,
      매입세금계산서수취일반세액,
      매입세금계산서수취고정자산금액,
      매입세금계산서수취고정자산세액,
      매입예정누락합계금액,
      매입예정누락합계세액,
      예정누락매입신고세금계산서금액,
      예정누락매입신고세금계산서세액,
      예정누락매입기타공제금액,
      예정누락매입기타공제세액,
      예정누락매입명세합계금액,
      예정누락매입명세합계세액,
      매입자발행세금계산서매입금액,
      매입자발행세금계산서매입세액,
      매입기타공제매입금액,
      매입기타공제매입세액,
      그밖의공제매입명세합계금액,
      그밖의공제매입명세합계세액,
      매입세액합계금액,
      매입세액합계세액,
      공제받지못할매입합계금액,
      공제받지못할매입합계세액,
      공제받지못할매입금액,
      공제받지못할매입세액,
      공제받지못할공통매입면세사업금액,
      공제받지못할공통매입면세사업세액,
      공제받지못할대손처분금액,
      공제받지못할대손처분세액,
      공제받지못할매입명세합계금액,
      공제받지못할매입명세합계세액,
      차감합계금액,
      차감합계세액,
      납부환급세액,
      그밖의경감공제세액,
      그밖의경감공제명세합계세액,
      경감공제합계세액,
      예정신고미환급세액,
      예정고지세액,
      사업양수자의대리납부기납부세액,
      매입자납부특례기납부세액,
      가산세액계,
      차감납부할세액,
      과세표준명세수입금액제외금액,
      과세표준명세합계수입금액,
      면세사업수입금액제외금액,
      면세사업합계수입금액,
      계산서교부금액,
      계산서수취금액,
      환급구분코드,
      은행코드,
      계좌번호,
      총괄납부승인번호,
      은행지점명,
      폐업일자,
      폐업사유,
      기한후여부,
      실차감납부할세액,
      일반과세자구분,
      조기환급취소구분,
      수출기업수입납부유예,
      업종코드,
      전자외매출세금계산서,
      전자외매출세금계산서합계,
      전자외매입세금계산서,
      전자외매입세금계산서합계,
      inspect_issue,
      inspect_elec,
      inspect_labor,
      신용카드발행집계표,
      신용카드수취기타카드,
      신용카드수취현금영수증,
      신용카드수취화물복지,
      신용카드수취사업용카드,
      공제받지못할매입세액명세,
      의제매입세액공제,
      재활용폐자원등매입세액,
      제출자,
      """]

        # 기준연도 및 분기에 따른 하위 쿼리 분기 처리
    if work_qt == 4:
        if biz_type == 4 or biz_type == 1:
            term = f"{work_yy}년 2기"
            period = f"{work_yy}년 1기"
            gubun = 'C07' if biz_type == 4 else 'C17'
        else:
            term = f"{work_yy}년 2기"
            period = f"{work_yy}년 2기"
            gubun = 'C17'
    elif work_qt == 2:
        term = f"{work_yy}년 1기"
        period = f"{work_yy - 1}년 2기" if biz_type == 4 else f"{work_yy}년 1기"
        gubun = 'C07' if biz_type == 4 else 'C17'
    elif work_qt == 1:
        term = "0"
        period = f"{work_yy - 1}년 2기"
        gubun = 'C07'
    elif work_qt == 3:
        term = "0"
        period = f"{work_yy}년 1기"
        gubun = 'C07'

    base_select.append(
        f"isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='{term}' and 신고구분='확정' and 사업자등록번호='{biz_no}'),0) as 예정금액, "
    )
    base_select.extend([
        f"(select isnull((매출과세기타금액 + 예정누락매출과세기타금액 + 면세사업합계수입금액 - 계산서교부금액), 0) from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간현금매출,",
        f"(select isnull(전자외매입세금계산서, '') from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간전자외매입세금계산서,",
        f"(select isnull(전자외매입세금계산서합계, '') from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간전자외매입세금계산서합계,",
        f"(select isnull(의제매입세액공제, '') from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간의제매입세액공제,",
        f"(select isnull(재활용폐자원등매입세액, '') from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간재활용폐자원등매입세액,",
        f"(select isnull(공제받지못할매입세액명세, '') from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and not 신고구분 like '%수정%' and 과세기간='{period}' and 과세유형='{gubun}') as 직전신고기간공제받지못할매입세액명세,",
        f"isnull((select YN_16 from tbl_vat where seq_no={seq_no} and work_yy={work_yy} and work_qt={work_qt}), 0) as YN_16,",
        f"isnull((select YN_17 from tbl_vat where seq_no={seq_no} and work_yy={work_yy} and work_qt={work_qt}), 0) as YN_17,",
        f"(select isnull(sum(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액 + 매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액 + 매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액 + 면세사업합계수입금액), 0) from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and left(과세기간, 4)='{work_yy}') as 당해년도매출,",
        f"(select isnull(sum(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액 + 매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액 + 매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액 + 면세사업합계수입금액), 0) from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and left(과세기간, 4)='{work_yy - 1}' and not 신고구분 like '%수정%') as 직전년도매출,",
        f"(select isnull(sum(면세사업합계수입금액), 0) from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and 과세기간='{kwasekikan}') as 동일기간면세매출,",
        f"(select isnull(sum(경감공제합계세액), 0) from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and left(과세기간, 4)='{work_yy}') as 경감공제합계세액"
    ])

    final_query = "\n".join(base_select)
    final_query += f"\nfrom 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and 과세기간='{kwasekikan}' and 과세유형='{KSUH}'"
    # print(final_query)
    return final_query

def build_vatElec_query(biz_no,  kwasekikan, KSUH):
  final_query = f"""
    SELECT 매출과세세금계산서발급금액,
      매출과세세금계산서발급세액,
      매출과세매입자발행세금계산서금액,
      매출과세매입자발행세금계산서세액,
      매출과세카드현금발행금액,
      매출과세카드현금발행세액,
      매출과세기타금액,
      매출과세기타세액,
      매출영세율세금계산서발급금액,
      매출영세율기타금액,
      매출예정누락합계금액,
      매출예정누락합계세액,
      예정누락매출세금계산서금액,
      예정누락매출세금계산서세액,
      예정누락매출과세기타금액,
      예정누락매출과세기타세액,
      예정누락매출영세율세금계산서금액,
      예정누락매출영세율기타금액,
      예정누락매출명세합계금액,
      예정누락매출명세합계세액,
      매출대손세액가감세액,
      과세표준금액,
      산출세액,
      매입세금계산서수취일반금액,
      매입세금계산서수취일반세액,
      매입세금계산서수취고정자산금액,
      매입세금계산서수취고정자산세액,
      매입예정누락합계금액,
      매입예정누락합계세액,
      예정누락매입신고세금계산서금액,
      예정누락매입신고세금계산서세액,
      예정누락매입기타공제금액,
      예정누락매입기타공제세액,
      예정누락매입명세합계금액,
      예정누락매입명세합계세액,
      매입자발행세금계산서매입금액,
      매입자발행세금계산서매입세액,
      매입기타공제매입금액,
      매입기타공제매입세액,
      그밖의공제매입명세합계금액,
      그밖의공제매입명세합계세액,
      매입세액합계금액,
      매입세액합계세액,
      공제받지못할매입합계금액,
      공제받지못할매입합계세액,
      공제받지못할매입금액,
      공제받지못할매입세액,
      공제받지못할공통매입면세사업금액,
      공제받지못할공통매입면세사업세액,
      공제받지못할대손처분금액,
      공제받지못할대손처분세액,
      공제받지못할매입명세합계금액,
      공제받지못할매입명세합계세액,
      차감합계금액,
      차감합계세액,
      납부환급세액,
      그밖의경감공제세액,
      그밖의경감공제명세합계세액,
      경감공제합계세액,
      예정신고미환급세액,
      예정고지세액,
      사업양수자의대리납부기납부세액,
      매입자납부특례기납부세액,
      가산세액계,
      차감납부할세액,
      과세표준명세수입금액제외금액,
      과세표준명세합계수입금액,
      면세사업수입금액제외금액,
      면세사업합계수입금액,
      계산서교부금액,
      계산서수취금액,
      환급구분코드,
      은행코드,
      계좌번호,
      총괄납부승인번호,
      은행지점명,
      폐업일자,
      폐업사유,
      기한후여부,
      실차감납부할세액,
      일반과세자구분,
      조기환급취소구분,
      수출기업수입납부유예,
      업종코드,
      전자외매출세금계산서,
      전자외매출세금계산서합계,
      전자외매입세금계산서,
      전자외매입세금계산서합계,
      inspect_issue,
      inspect_elec,
      inspect_labor,
      신용카드발행집계표,
      신용카드수취기타카드,
      신용카드수취현금영수증,
      신용카드수취화물복지,
      신용카드수취사업용카드,
      공제받지못할매입세액명세,
      의제매입세액공제,
      재활용폐자원등매입세액,
      제출자
    from 부가가치세전자신고3 where 사업자등록번호='{biz_no}' and 과세기간='{kwasekikan}' and 과세유형='{KSUH}'
    """ 
  return final_query

def get_tax_inspection_result(rs: Dict[str, Any], work_yy: int, work_qt: int, biz_no: str, biz_type: int, kwasekikan: str, SKGB: str, seq_no: int) -> Dict[str, Any]:
  def to_decimal(val):
      try:
          return Decimal(str(val).replace(",", ""))
      except:
          return Decimal("0")

  rows = []
  # 1. 신용카드/현금영수증 매출
  yn_16 = Decimal(rs.get("YN_16", 0))
  yn_17 = Decimal(rs.get("YN_17", 0))

  # 비교 대상: 실제 신고된 카드/현금영수증 매출
  amt_Issue_CARDSALE = to_decimal(rs.get("매출과세카드현금발행금액", 0)) + to_decimal(rs.get("매출과세카드현금발행세액", 0))
  amt_HTX_CARDSALE = yn_16 + yn_17

  # 상태 및 메시지 초기화
  cardsale_status = "✅"
  cardsale_message = ""
  if amt_Issue_CARDSALE < amt_HTX_CARDSALE:
      diff = abs(amt_HTX_CARDSALE - amt_Issue_CARDSALE)
      if diff > 20:
          cardsale_status = "⚠️"
          cardsale_message = f"홈택스 조회 신용카드/현금영수증 금액과 신고 금액의 차이 : {diff:,}원"
  cardsale_detail = (
      f"<b>1. 신용카드 및 현금영수증 매출 (공급대가) 반영여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;검증 대상금액 - 홈택스 조회 신용카드 : {yn_16:,}원<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;검증 대상금액 - 홈택스 조회 현금영수증 : {yn_17:,}원"
  )
  amt_reported = to_decimal(rs["매출과세카드현금발행금액"]) + to_decimal(rs["매출과세카드현금발행세액"])
  amt_target = to_decimal(rs["YN_16"]) + to_decimal(rs["YN_17"])
  rows.append([cardsale_detail, amt_target, amt_reported, cardsale_status, cardsale_message])

  # 2. 현금 건별매출
  prev_cash_sales =  Decimal(rs.get("직전신고기간현금매출") or "0")
  curr_cash_sales = Decimal(rs.get("매출과세기타금액") or "0") + Decimal(rs.get("매출과세기타세액") or "0")

  # 판정
  cash_sale_status = "✅"
  cash_sale_message = ""

  if prev_cash_sales > 0 and curr_cash_sales == 0:
      cash_sale_status = "⚠️"
      cash_sale_message = "직전신고기간에 현금 건별매출이 있었으나 이번기 신고서에 반영되지 않았습니다."

  # ✅ 점검 항목 제목에 세부내역 포함
  cash_sale_detail = (
      f"<b>2. 현금 건별 또는 온라인매출 반영여부 (공급대가)</b><br><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;검증 대상금액 - 지난 분기 현금 건별매출 : {prev_cash_sales:,}원<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;신고서 작성금액 - 기타매출(과세기타) : {curr_cash_sales:,}원"
  )

  rows.append([
      cash_sale_detail,
      prev_cash_sales,
      curr_cash_sales,
      cash_sale_status,
      cash_sale_message
  ])

  # 3. 종이 세금계산서
  now_paperExpTaxInvoice_val = Decimal(0)
  raw_now = rs.get("전자외매입세금계산서합계", "")
  if raw_now:
      val = mid_union(raw_now, 26, 15).replace("}", "").strip()
      now_paperExpTaxInvoice_val = Decimal(val or "0")

  # 직전기 종이세금계산서 금액 추출
  pre_paperExpTaxInvoice_val = Decimal(0)
  raw_pre = rs.get("직전신고기간전자외매입세금계산서합계", "")
  if raw_pre:
      val = mid_union(raw_pre, 26, 15).replace("}", "").strip()
      pre_paperExpTaxInvoice_val = Decimal(val or "0")

  # 검증대상 세부내역 정리
  paperInvoice_status = "✅"
  paperInvoice_message = ""
  tot_paperExpTaxInvoice = ""

  raw_detail = rs.get("직전신고기간전자외매입세금계산서", "")
  if raw_detail:
      biz_key = f"2{biz_no.replace('-', '')}"
      sp_paper_exp = raw_detail.split(biz_key)

      for k, part in enumerate(sp_paper_exp[1:11], 1):  # 최대 10건
          name = mid_union(part, 15, 30).strip()
          count = mid_union(part, 87, 7).strip()
          amount = mid_union(part, 96, 14).replace("}", "").strip()
          if name or count or amount:
              try:
                  tot_paperExpTaxInvoice += f"- {name}&ensp;&ensp;{int(count):,}건&ensp;&ensp;{int(amount):,}원<br>&ensp;&ensp;"
              except:
                  continue

  # 판정
  if pre_paperExpTaxInvoice_val > 0 and now_paperExpTaxInvoice_val == 0:
      paperInvoice_status = "⚠️"
      paperInvoice_message = "직전 신고기간에 종이 매입세금계산서가 있었으니 이번기 누락 여부 확인 필요"

  # 최종 점검 항목 설명 포함
  detail_html = (
      f"<b>3. 반복 발생되는 종이세금계산서 반영여부(임차료 등)</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;{tot_paperExpTaxInvoice}"
  )
  rows.append([
      detail_html,
      pre_paperExpTaxInvoice_val,
      now_paperExpTaxInvoice_val,
      paperInvoice_status,
      paperInvoice_message
  ])

  # 4. 공통매입세액 안분
  taxfree_sales = Decimal(rs.get("동일기간면세매출") or "0")
  disallowed_common_purchase = Decimal(rs.get("공제받지못할공통매입면세사업금액") or "0")
  deduct_total = Decimal(rs.get("차감합계세액") or "0")

  # 판정
  bulgongje_status = "✅"
  bulgongje_message = ""

  if taxfree_sales > 0 and disallowed_common_purchase == 0:
      if deduct_total == 0:
          bulgongje_status = "✅"
          bulgongje_message = ""
      else:
          bulgongje_status = "⚠️"
          bulgongje_message = "면세매출이 있으나 공통매입세액 안분계산이 누락된 것으로 보입니다."

  # 상세 설명 포함한 항목명 (HTML)
  detail_html = (
      f"<b>4. 면세매출 있을 시 공통매입세액 안분여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;검증 대상금액 - 동일 과세기간 면세매출 : {taxfree_sales:,}원<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;신고서 작성금액 - 공통매입 불공제매입세액 : {disallowed_common_purchase:,}원"
  )

  rows.append([
      detail_html,
      taxfree_sales,
      disallowed_common_purchase,
      bulgongje_status,
      bulgongje_message
  ])

  # 5. 예정고지세액
  preAmt = Decimal(rs.get("예정금액") or "0")
  expected_tax = Decimal(rs.get("예정고지세액") or "0")
  expected_refund = Decimal(rs.get("예정신고미환급세액") or "0")
  biz_type = rs.get("biz_type", 0)

  reported_sum = expected_tax + expected_refund

  # 판정
  preTax_status = "✅"
  preTax_message = ""

  if abs(preAmt - reported_sum) >= 10:
      preTax_status = "⚠️"
      if preAmt < expected_refund:
          preTax_message = "예정미환급세액을 과다하게 신고서 반영하였습니다."
      elif biz_type > 3:
          preTax_message = "예정고지금액을 신고서에 반영하지 않았습니다."
      else:
          preTax_message = "예정미환급금액을 신고서에 반영하지 않았습니다."

  # 상세 설명 포함 HTML
  detail_html = (
      f"<b>5. 예정고지세액 또는 예정미환급세액 반영여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;검증 대상금액 : {preAmt:,}원<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;신고서 작성금액 (예정고지 + 미환급) : {reported_sum:,}원"
  )

  # 결과 row
  rows.append([
      detail_html,
      preAmt,
      reported_sum,
      preTax_status,
      preTax_message
  ])

  # 6. 카드세액공제 한도
  credit_deduction_limit = Decimal("10000000")
  actual_deduction = Decimal(rs.get("경감공제합계세액") or "0")
  prev_sales = Decimal(rs.get("직전년도매출") or "0")
  upjong_code = rs.get("업종코드", "")

  # 판정
  sinca_status = "✅"
  sinca_message = ""

  if actual_deduction > credit_deduction_limit:
      sinca_status = "⚠️"
      sinca_message = "신용카드공제 한도(500만원)를 초과했으니<br>재점검 바랍니다."
  elif prev_sales >= 1000000000 and actual_deduction > 0:
      sinca_status = "⚠️"
      sinca_message = "직전년도 매출액이 10억을 초과하는 경우<br>신용카드세액공제를 받을 수 없습니다."
  elif 15 <= int(upjong_code) < 39 and actual_deduction > 0:
      sinca_status = "⚠️"
      sinca_message = "제조업은 신용카드세액공제를 받을 수 없습니다."

  # 상세 설명 텍스트 (HTML 포함)
  lawTxt_6 = (
      "① 신용카드 발행세액공제 가능사업자 및 업종"
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;- 법인사업자 및 과세 연매출이 10억 이상인 사업자 : 공제 불가능"
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;- 개인사업자(간이) : 업종불문 공제가능"
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;- 개인사업자(일반) : 도소매, 음식점, 미용, 건설, 운수, 부동산중개업 등<br>&nbsp;&nbsp;&nbsp;&nbsp;(제조업 불가)"
      "<br>② 공제금액(한도 : 연간 500만원)"
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;- 일반 : 신용카드 등 공급대가 * 1.3%"
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;- 간이 중 음식숙박업: 신용카드 등 공급대가 * 2.6%"
  )

  detail_html = (
      f"<b>6. 연간 신용카드발행세액공제 한도 초과여부</b><br>{lawTxt_6}"
  )

  rows.append([
      detail_html,
      credit_deduction_limit,
      actual_deduction,
      sinca_status,
      sinca_message
  ])

  # 7. 전자세금계산서 의무발행
  e_invoice_threshold = Decimal("80000000")
  last_year_sales = Decimal(rs.get("직전년도매출") or "0")
  biz_type = rs.get("biz_type", 0)

  # 법 조항 설명
  lawTxt_7 = (
      "*** 부가세법시행령 제68조 【전자세금계산서의 발급 등】***<br>"
      "① 직전연도의 사업장별 재화 및 용역의 공급가액의 합계액이 8천만원 이상인 개인사업자"
      "<br>② 전자세금계산서를 발급하여야 하는 기간은 사업장별 재화 및 용역의 "
      "<br>&nbsp;&nbsp;&nbsp;&nbsp;합계액이 <b>8천만원 이상인 해의 다음 해 제2기 과세기간과 그 다음 해 제1기 과세기간</b>"
  )

  # 판정
  dareTI_status = "✅"
  dareTI_message = ""

  if biz_type > 3 and last_year_sales >= e_invoice_threshold:
      dareTI_status = "⚠️"
      dareTI_message = "전자세금계산서 의무발행 대상자입니다."

  # 상세 설명 포함 HTML
  detail_html = (
      f"<b>7. 전자세금계산서 의무발급 개인사업자</b><br>{lawTxt_7}"
  )

  # 결과 구성
  if biz_type>4:
    rows.append([
      detail_html,
      e_invoice_threshold,
      last_year_sales,
      dareTI_status,
      dareTI_message
    ])

  # 데이터 파싱
  upjong_code = rs["업종코드"]
  curr_sales = Decimal(rs["당해년도매출"])
  upjong_prefix = upjong_code[:2]

  # 업종별 기준 설정
  if upjong_prefix in GB_KA:
      Amt_Labor_standard = 1500000000
  elif upjong_prefix in GB_NA:
      Amt_Labor_standard = 750000000
  else:
      Amt_Labor_standard = 500000000

  # 환산 매출
  multiplier = Decimal(4) / Decimal(work_qt)
  adjusted_sales = curr_sales * multiplier if work_qt != 4 else curr_sales

  # 판정
  sungsil_status = "✅"
  sungsil_message = ""

  if adjusted_sales >= Amt_Labor_standard:
      sungsil_status = "⚠️"
      if work_qt != 4:
          sungsil_message = f"환산매출액 : {adjusted_sales:,.0f}원"
      else:
          sungsil_message = "당해년도 매출액이 성실신고 기준 초과"

  # 상세 설명 포함 HTML
  detail_html = (
      f"<b>8. 성실신고 대상 여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;당해년도 수입금액이 업종별 기준 초과시 성실신고 대상자임<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;업종별 기준 금액 : {Amt_Labor_standard:,}원<br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;환산 매출액 : {adjusted_sales:,}원"
  )

  # 결과 구성
  if biz_type>4:
    rows.append([
      detail_html,
      Amt_Labor_standard,
      adjusted_sales,
      sungsil_status,
      sungsil_message
    ])  
  # 9. 환급조사 대상
  amt_target = Decimal("-5000000")
  amt_reported = to_decimal(rs["납부환급세액"])
  status = "⚠️" if amt_reported <= amt_target else "✅"
  message = "매입거래 대금지급증빙 : 통장내역<br>매입거래 실질확인 : 거래명세서, 운송장 등" if status == "⚠️" else ""
  rows.append(["<b>9. 환급조사 대상</b><br>&nbsp;&nbsp;&nbsp;&nbsp;당해년도 환급금액이 500만원 초과시 환급조사 대상자임", amt_target, amt_reported, status, message])

  # 10. 의제매입세액공제
  val = rs.get("직전신고기간의제매입세액공제")
  prior_val_raw = str(val).strip() if val is not None else ""  
  prior_val_raw = prior_val_raw[42:42+18]
  curr_val = rs.get("의제매입세액공제")
  curr_val_raw = str(curr_val).strip() if curr_val is not None else ""  
  curr_val_raw = curr_val_raw[42:42+18] 

  # 점검 로직
  pretendKJ_status = "✅"
  pretendKJ_message = ""
  prior_val_decimal = "-"

  if prior_val_raw and not curr_val_raw:
      prior_val_decimal = Decimal(prior_val_raw)
      curr_val_raw = Decimal(curr_val_raw)
      pretendKJ_status = "⚠️"
      pretendKJ_message = "직전 신고기간에 의제매입세액공제가 있었으니 당기 매입계산서 확인바랍니다"

  else:
      pretendKJ_status = "✅"
      if prior_val_raw:
        prior_val_decimal = Decimal(prior_val_raw)

  # 설명 포함 HTML
  detail_html = (
      f"<b>10. 의제매입세액공제 반영 여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;계산서 매입이 있는 과세사업자"
  )

  # 결과 구성
  rows.append([
      detail_html,
      prior_val_decimal,
      curr_val_raw if curr_val_raw else "-",
      pretendKJ_status,
      pretendKJ_message
  ])

  # 11. 재활용폐자원 공제
  val = rs.get("직전신고기간재활용폐자원등매입세액")
  prior_recycle_raw = str(val).strip() if val is not None else ""  
  prior_recycle_raw = prior_recycle_raw[42:42+18]  
  curr_val = rs.get("재활용폐자원등매입세액")
  curr_recycle_val = str(curr_val).strip() if curr_val is not None else ""  
  curr_recycle_val = curr_recycle_val[42:42+18] 

  # 점검 로직
  pretendKJ2_status = "✅"
  pretendKJ2_message = ""
  prior_recycle_decimal = "-"

  if prior_recycle_raw and not curr_recycle_val:
      prior_recycle_decimal = Decimal(prior_recycle_raw)
      pretendKJ2_status = "⚠️"
      pretendKJ2_message = "직전 신고기간에 재활용폐자원등 매입세액공제가 있었으니 당기 매입계산서 확인바랍니다"
  else:
      pretendKJ2_status = "✅"
      if prior_recycle_raw:
        prior_recycle_decimal = Decimal(prior_recycle_raw)

  # 설명 포함 HTML
  detail_html = (
      f"<b>11. 재활용폐자원 매입세액공제 여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;폐품등 재활용품 매입이 있는 과세사업자"
  )

  # 결과 구성
  rows.append([
      detail_html,
      prior_recycle_decimal,
      curr_recycle_val if curr_recycle_val else "-",
      pretendKJ2_status,
      pretendKJ2_message
  ])

  # 12. 불공제 매입세액 (명세 비교 생략)
  def parse_bull_array_union(raw_str):
      arr = [""] * 9  # 1~8번 항목
      idx = 0
      for i in range(len(raw_str) // 39):
          tmp = raw_str[idx:idx+39]
          key = mid_union(tmp, 2, 1)
          if key.isdigit():
              arr[int(key)] = tmp
          idx += 39
      return arr

  def extract_amount_union(s):
      try:
          return Decimal(mid_union(s, 27, 40).strip())
      except Exception:
          return Decimal(0)
  bull_labels = {
      1: "필요적기재사항누락",
      2: "사업과 직접 관련 없는 지출",
      3: "비영업용 소형승용차 관련",
      4: "접대비 관련",
      5: "면세사업 관련",
      6: "토지의 자본적 지출 관련",
      7: "사업자등록 전 매입세액",
      8: "금구리스크랩 거래계좌 미사용"
  }
  # 재파싱 및 계산
  val = rs.get("직전신고기간공제받지못할매입세액명세")
  prior_bullgong = str(val).strip() if val is not None else ""    
  arr_bf = parse_bull_array_union(prior_bullgong)
  val = rs.get("공제받지못할매입세액명세")
  now_bullgong = str(val).strip() if val is not None else ""      
  arr_now = parse_bull_array_union(now_bullgong)

  sum_bf, sum_now = Decimal(0), Decimal(0)
  bf_detail, now_detail = "", ""
  status = "✅"

  for i in range(1, 9):
      amt_bf = extract_amount_union(arr_bf[i]) if arr_bf[i] else Decimal(0)
      amt_now = extract_amount_union(arr_now[i]) if arr_now[i] else Decimal(0)
      sum_bf += amt_bf
      sum_now += amt_now

      if arr_bf[i] and not arr_now[i]:
          bf_detail += f"{bull_labels[i]}: {amt_bf:,.0f}원<br>"
          status = "⚠️"
      if arr_now[i]:
          now_detail += f"{bull_labels[i]}: {amt_now:,.0f}원<br>"

  if bf_detail.endswith("<br>"):
      bf_detail = bf_detail[:-4]
  if now_detail.endswith("<br>"):
      now_detail = now_detail[:-4]

  # 설명 포함 HTML
  detail_html = (
      f"<b>12. 불공제매입세액 반영 여부</b><br>"
      f"&nbsp;&nbsp;&nbsp;&nbsp;{bf_detail}"
  )

  # 결과 구성
  rows.append([
      detail_html,
      sum_bf,
      sum_now,
      status,
      now_detail
  ])

  inspect_issue = "1#" # 전자신고 파일 업로드시 일단 스마일
  inspect_elec = 0
  inspect_labor = 0

  # 1. 카드/현금영수증 매출 이슈
  if rows[0][3] == "⚠️":
      inspect_issue += "2#"

  # 2. 현금 건별매출
  if rows[1][3] == "⚠️":
      inspect_issue += "8#"

  # 3. 종이 세금계산서
  if rows[2][3] == "⚠️":
      inspect_issue += "4#"

  # 4. 공통매입세액 안분
  if rows[3][3] == "⚠️":
      inspect_issue += "5#"

  # 5. 예정고지세액
  if rows[4][3] == "⚠️":
      inspect_issue += "3#"

  # 6. 카드공제한도 초과
  if rows[5][3] == "⚠️":
      inspect_issue += "6#"

  # 7. 전자세금계산서
  if len(rows) > 6 and "전자세금계산서 의무발급 개인사업자" in rows[6][0]:
      if rows[6][3] == "⚠️":
          inspect_elec = 2
          inspect_issue += "7#"

  # 8. 성실신고
  if len(rows) > 7 and "성실신고 대상 여부" in rows[7][0]:
      if rows[7][3] == "⚠️":
          inspect_labor = 2

  # 9. 환급조사 대상
  if "환급조사 대상" in rows[-3][0] and rows[-3][3] == "⚠️":
      inspect_issue += "9#"

  # 10. 의제매입세액공제
  if "의제매입세액공제 반영 여부" in rows[-2][0] and rows[-2][3] == "⚠️":
      inspect_issue += "10#"

  # 11. 재활용폐자원
  if "재활용폐자원 매입세액공제 여부" in rows[-1][0] and rows[-1][3] == "⚠️":
      inspect_issue += "11#"

  # 12. 불공제매입세액
  if rows[-1][3] == "⚠️":
      inspect_issue += "12#"

  return {
      "rows": rows,
      "inspect_issue": inspect_issue,
      "inspect_elec": inspect_elec,
      "inspect_labor": inspect_labor
  }

@csrf_exempt
def check_yn12(request):
    """YN_12 값 확인 API"""
    if request.method == "POST":
        seq_no = request.POST.get("seq_no")
        work_YY = request.POST.get("work_YY")
        work_QT = request.POST.get("work_QT")

        if not seq_no or not work_YY:
            return JsonResponse({"exists": False, "error": "Missing parameters"}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT YN_12 FROM tbl_vat WHERE seq_no=%s AND work_YY=%s  AND work_QT=%s
            """, [seq_no, work_YY,work_QT])
            row = cursor.fetchone()  # 데이터 가져오기

        # row가 있고 YN_12가 None이 아니고 0보다 큰 경우만 True
        exists = row is not None and row[0] is not None and row[0] > 0
        return JsonResponse({"exists": exists})

    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
def get_Fee_data(request):
  if request.method == "POST":
    seq_no = request.POST.get("seq_no")
    work_YY = request.POST.get("work_YY")
    work_QT = request.POST.get("work_QT")  
    if seq_no:
      memuser = get_object_or_404(MemUser, seq_no=seq_no)      
      memdeal = get_object_or_404(MemDeal, seq_no=seq_no)      
      kijang_YN = memdeal.kijang_yn
      biz_type = memuser.biz_type

      sql_Fee = f" select '부가세' 분류,work_yy 귀속년도, CAST(work_qt AS VARCHAR) + '분기' AS 구분,YN_12 수수료, YN_11 수금여부,YN_1 수금일,YN_2 발행여부,YN_3 발행일 from tbl_vat where seq_no={seq_no} and YN_12>0 "
      if kijang_YN=="Y":
        sql_Fee += " union all "
        sql_Fee += f" SELECT '기장료' 분류, work_YY 귀속년도, CAST(work_mm AS VARCHAR) + '월' AS 구분,'{memdeal.feeamt}' 수수료,YN_10 수금여부,'' 수금일,'' 발행여부,'' 발행일 FROM tbl_mng_jaroe where seq_no={seq_no} and YN_10='1'  "
      tbl_name = "tbl_corporate2";str_name = "법인세"
      if biz_type>=4:
        tbl_name = "tbl_income2";str_name = "종합소득세"
      sql_Fee += " union all "
      sql_Fee += f" select '{str_name}' 분류,work_yy 귀속년도,'' 구분,YN_8 수수료, YN_7 수금여부,YN_10 수금일,YN_11 발행여부,YN_12 발행일  from {tbl_name} where seq_no={seq_no} and YN_8>0  "         
      sql_Fee += " ORDER BY 귀속년도 DESC, 구분 ASC;"
      # print(sql_Fee)
      with connection.cursor() as cursor:
        cursor.execute(sql_Fee)
        rows = dict_fetchall(cursor)
        # print(rows)
        return JsonResponse(rows, safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)      
  

# 매입 매출처 리스트 - 도넛 작성용
@csrf_exempt
def get_TraderList(request):
  if request.method != 'POST':
      return JsonResponse({'error': 'Invalid request method'}, status=405)

  data = json.loads(request.body)
  seq_no = data.get("seq_no")
  work_YY = data.get("work_YY")
  period = data.get("period")
  youhyung = data.get("youhyung")
  memuser = get_object_or_404(MemUser, seq_no=seq_no)
  biz_no = memuser.biz_no
  biz_type = memuser.biz_type
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

  # ✅ 첫 번째 쿼리
  sql_main = """
      SELECT 
        trader_code,max(trader_name),sum(tranamt_cr),sum(tranamt_dr)
      FROM DS_SlipLedgr2
      WHERE seq_no = %s
        AND work_yy = %s
        AND tran_dt >= %s
        AND tran_dt <= %s
        and tran_dt<>'00-00'	
        AND tran_stat = '매입매출전표'
        AND acnt_cd BETWEEN 401 AND 430
      GROUP BY trader_code
      ORDER BY SUM(tranamt_dr) DESC
  """
  # ✅ 두 번째(대체) 쿼리

  sql_fallback = f"""
    SELECT 
        s.trader_code AS trader_code,          -- ✅ DS_SlipLedgr2에서 거래처코드 가져오기
        MAX(e.공급받는자상호) AS trader_name,      -- ✅ 전자세금계산서에서 거래처명
        SUM(e.합계금액) AS total_amount,       -- ✅ 합계금액
        SUM(e.공급가액) AS supply_amount,
        SUM(e.세액) AS tax_amount
    FROM 전자세금계산서 e
    JOIN DS_SlipLedgr2 s 
      ON s.seq_no = e.SEQ_NO and e.공급받는자사업자등록번호 = s.Trader_Bizno              
    WHERE s.seq_no = {seq_no}
      AND s.work_yy = {int(work_YY)-1}
      AND e.작성일자 BETWEEN '{work_YY}-{startDt}' AND '{work_YY}-{endDt}'
      AND e.매입매출구분 in ('1','3')
    GROUP BY s.trader_code
    ORDER BY SUM(e.합계금액) DESC
  """
  totSaleArr = []

  with connection.cursor() as cursor:
      # ✅ 1차 쿼리 실행
      cursor.execute(sql_main, [seq_no, work_YY, startDt, endDt])
      rows = cursor.fetchall()

      # ✅ 결과 없으면 fallback 쿼리 실행
      if not rows:
          print(sql_fallback)
          # cursor.execute(sql_fallback, [seq_no, int(work_YY)-1, startDt, endDt])
          cursor.execute(sql_fallback)
          rows = cursor.fetchall()

  # ✅ 결과를 JSON 형태로 변환
  totSaleArr = [
      {'거래처코드': r[0], '거래처명': r[1], '금액': float(r[3] or 0)}
      for r in rows
  ]

  # 비용내역
  sql_main_Cost = f"""
    select trader_code,max(trader_name),sum(tranamt_cr),sum(tranamt_dr)/1.1 from DS_SlipLedgr2 
    where seq_no ={seq_no} and work_yy={work_YY} and tran_dt>='{startDt}' and tran_dt<='{endDt}' and tran_stat='매입매출전표' 
    and (acnt_cd=251 or acnt_cd=101)
    and tranamt_dr>0
    and tran_dt<>'00-00'	
    and trader_name not like '%카드%'
    group by trader_code order by sum(tranamt_dr) desc 
  """
  sql_fallback_Cost = f"""
    SELECT 
        s.trader_code AS trader_code,          -- ✅ DS_SlipLedgr2에서 거래처코드 가져오기
        MAX(e.공급자상호) AS trader_name,      -- ✅ 전자세금계산서에서 거래처명
        SUM(e.합계금액) AS total_amount,       -- ✅ 합계금액
        SUM(e.공급가액) AS supply_amount,
        SUM(e.세액) AS tax_amount
    FROM 전자세금계산서 e
    JOIN DS_SlipLedgr2 s 
      ON s.seq_no = e.SEQ_NO and e.공급자사업자등록번호 = s.Trader_Bizno              
    WHERE s.seq_no = {seq_no}
      AND s.work_yy = {int(work_YY)-1}
      AND e.작성일자 BETWEEN '{work_YY}-{startDt}' AND '{work_YY}-{endDt}'
      AND e.매입매출구분 in ('2','4')
    GROUP BY s.trader_code
    ORDER BY SUM(e.합계금액) DESC
  """
  totCostArr = []

  with connection.cursor() as cursor:
      # ✅ 1차 쿼리 실행
      cursor.execute(sql_main_Cost)
      rows = cursor.fetchall()

      # ✅ 결과 없으면 fallback 쿼리 실행
      if not rows:
          print(sql_fallback_Cost)
          cursor.execute(sql_fallback_Cost)
          rows = cursor.fetchall()

  # ✅ 결과를 JSON 형태로 변환
  totCostArr = [
      {'거래처코드': r[0], '거래처명': r[1], '금액': float(r[3] or 0)}
      for r in rows
  ]
  # strsql = f"""
  #   with ST As  
  #   (	select *  from DS_SlipLedgr2 with (nolock)  
  #   where seq_no ={seq_no} and work_yy={work_YY} and tran_dt>='{startDt}' and tran_dt<='{endDt}' and tran_stat='매입매출전표'  
  #   and acnt_cd=253		) 
  #   select a.trader_code, max(a.trader_name), sum(a.tranamt_cr), sum(a.tranamt_dr)
  #   from DS_SlipLedgr2   a, ST b
  #   where a.seq_no = b.seq_no 
  #   and a.work_yy = b.work_yy 
  #   and a.tran_dt = b.tran_dt
  #   and a.slip_no = b.slip_no
  #   and a.acnt_cd <> 253 
  #   group by a.trader_code
  #   order by sum(a.tranamt_cr) desc
  # """
  # cursor = connection.cursor()
  # result = cursor.execute(strsql)
  # result = cursor.fetchall()
  # connection.commit()
  # connection.close()
  # totCardArr = []
  # if result:
  #   for r in result:
  #     row = {
  #       '거래처코드':r[0],
  #       '거래처명':r[1],
  #       '금액':r[2],
  #     }
  #     totCardArr.append(row)      
  rtnJson = {"current":1}
  rtnJson["sale"]=totSaleArr          
  rtnJson["cost"]=totCostArr          
  # rtnJson["card"]=totCardArr          
  return JsonResponse(rtnJson,safe=False)

def to_number(val):
  try:
    return Decimal(val)
  except:
    return Decimal('0')

def dict_fetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [
      {col: (value.strip() if isinstance(value, str) else value) for col, value in zip(columns, row)}
      for row in cursor.fetchall()
  ]

def dictfetchone(cursor):
    columns = [col[0] for col in cursor.description]
    row = cursor.fetchone()
    return dict(zip(columns, row)) if row else None

#소수점 절사하고 콤마를 씌운다
def fmt(n):
    try:
        return f"{int(float(n)):,}"
    except:
        return "0"