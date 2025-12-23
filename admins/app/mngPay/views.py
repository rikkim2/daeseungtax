import json
import datetime
import copy
import math
import os
import natsort
import traceback

from datetime import timedelta
from django.db import connection
from collections import defaultdict
from urllib.parse import unquote
from django.views.decorators.csrf import csrf_exempt

from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from app.models import MemAdmin
from app.models import MemDeal
from app.models import MemUser  # KijangMember는 "기장회원관리"와 관련된 모델이라고 가정합니다.
from app.models import userProfile

from app.models import TblMngJaroe
from app.models import TblHometaxScrap
from app.models import TblHometaxSalecard
from django.db import models,transaction

from django.db.models import Q

from admins.utils import (
    tbl_mng_jaroe_update,
    mem_deal_update,
    mid_union,
    kijang_member_popup,
    getMailContent,
    getSentMails,
    sendMail,
    send_kakao_notification,
    send_sms_popbill,
    get_sms_prefill,
    get_popbill_balance,
    get_sent_sms_list
)
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
  if not work_MM:
    work_MM = request.session.get('workmonthPay')
    if not work_MM:
      current_month = today.month
      current_day = today.day
      if current_day >= 11:  
        work_MM = current_month
      else:
        work_MM = current_month - 1 if current_month > 1 else 12
  if not work_YY:
    work_YY = request.session.get('workyearPay')
    if not work_YY:
      if int(work_MM) <= 1 :
        work_YY = today.year - 1
      else:
        work_YY = today.year
    else:
      work_YY = int(work_YY)
  request.session['workyearPay'] = work_YY
  request.session['workmonthPay'] = work_MM

  corpYears = list(range(work_YY, work_YY - 6, -1))
  context['corpYears'] = corpYears
  context['admin_biz_level'] = admin_biz_level
  context['arr_ADID'] = json.dumps(list(arr_ADID))
  context['flag'] = flag
  context['ADID'] = ADID
  request.session['ADID'] = ADID  

  request.session.save()
  templateMenu = gridTitle=""
  if flag == "payroll":
    templateMenu = 'admin/mng_payroll.html'; gridTitle="원천세신고현황"
  elif flag == "kaniKunro":
    templateMenu = 'admin/mng_pay_kaniKunro.html'; gridTitle="근로소득 간이지급명세서"
  elif flag == "kaniSail":
    templateMenu = 'admin/mng_kaniSail.html'; gridTitle="사업일용기타 간이지급명세서"
  elif flag == "yearend":
    templateMenu = 'admin/mng_pay_yearend.html'; gridTitle="연말정산 현황"    
  elif flag == "zzjsKita":
    templateMenu = 'admin/mng_pay_zzjsKita.html'; gridTitle="지급조서 신고현황"        
  elif flag == "payReport":
    templateMenu = 'admin/mng_pay_report.html'; gridTitle="지급조서 분석"            
  context['gridTitle'] = gridTitle  
  return render(request, templateMenu,context)


def mng_kani_kunro(request):
  return
def mng_zzjs_yearend(request):
  return
def mng_zzjs_kita(request):
  return
def mng_pay_report(request):
  return

#원천세 신고 대상자 리스트
def mng_payroll(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')#전체 선택시 ADID=""상태가 된다
  request.session['ADID'] = ADID  
  
  work_YY = request.GET.get('work_YY', '')
  work_MM = request.GET.get('work_MM', '')
  request.session['workyearPay'] = work_YY
  request.session['workmonthPay'] = work_MM
  request.session.save()

  if request.method == 'GET':
    txtMM = f"0{work_MM}" if int(work_MM) < 10 else str(work_MM)
    s_sql = ""
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"
    sql_query = f"""
      WITH LatestMail AS (
        SELECT  seq_no,MAX(mail_date) AS mail_date FROM tbl_mail 
        WHERE mail_class in ('pay','mail') AND CHARINDEX('{work_YY}년 {work_MM}월', mail_subject) > 0
        GROUP BY seq_no
      )
      SELECT 
          b.biz_manager as groupManager, a.seq_no , a.biz_name,
          b.goyoung_jungkyu, b.goyoung_ilyoung, b.goyoung_sayoup, b.goyoung_banki, 
          COALESCE(d.yn_11, '0') AS YN_11, COALESCE(d.yn_12, '0') AS YN_12, COALESCE(d.yn_13, '0') AS YN_13, COALESCE(d.yn_14, '0') AS YN_14, 
          b.ediid, b.edipw, 
          lm.mail_date, e.접수번호 AS isIssue,  RIGHT(e.제출자, 2) AS issuedID
      FROM Mem_User a
      LEFT JOIN tbl_mng_jaroe d 
          ON a.seq_no = d.seq_no AND d.work_YY = '{work_YY}' AND d.work_MM = '{work_MM}'
      LEFT JOIN 원천세전자신고 e 
          ON a.biz_no = e.사업자등록번호 AND e.과세연월 = '{work_YY}{txtMM}'
      INNER JOIN mem_deal b  ON a.seq_no = b.seq_no
      INNER JOIN mem_admin c  ON b.biz_manager = c.admin_id
      LEFT JOIN LatestMail lm  ON a.seq_no = lm.seq_no
      WHERE 
          a.duzon_ID <> '' AND b.keeping_YN = 'Y' AND a.Del_YN <> 'Y' 
          AND (b.goyoung_jungkyu = 'y' OR b.goyoung_ilyoung = 'y' OR b.goyoung_sayoup = 'y' OR  b.goyoung_banki = 'y')
          {s_sql}
      ORDER BY COALESCE(b.biz_manager,a.biz_name);
    """
    print(sql_query)
    recordset = []
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]  # 컬럼명 가져오기
        results = cursor.fetchall()

        for row in results:
            row_dict = {columns[i]: (value.strip() if isinstance(value, str) else value) for i, value in enumerate(row)}

            # 폴더 내에서 "2월"로 시작하는 파일이 있는지 확인
            srcpath = os.path.join('static/cert_DS/', str(row_dict["biz_name"]), str(work_YY), "인건비")
            fileExist = 0  # 기본값 (없음)
            if os.path.exists(srcpath) and os.path.isdir(srcpath):  # 폴더가 존재하는지 확인
                files = os.listdir(srcpath)  # 폴더 내 파일 목록 가져오기
                if any(file.startswith(f"{work_MM}월") for file in files):  # "2월"로 시작하는 파일이 있는지 확인
                    fileExist  = 1
        
            row_dict["fileExist"] = fileExist
            recordset.append(row_dict)
    #print(recordset) 
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

#전자신고 접수증 가져오기
def pay_jupsuSummit(request):
  seq_no = request.POST.get('seq_no')
  work_YY = request.POST.get('work_YY')  
  if seq_no:
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    memdeal = get_object_or_404(MemDeal, seq_no=seq_no)

    sql_query = f"""
      SELECT 과세년월,신고서종류,신고구분,신고유형,상호,사업자번호,신고번호,신고시각,접수여부,사용자ID FROM 법인세전자신고2
      WHERE 사업자번호 = '{memuser.biz_no}' AND 과세년월 = '{work_YY}년{memdeal.fiscalmm}월'
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

#전자신고파일 업로드
def extract_value(record, amount_pos, man_pos=None, tax_pos=None):
    if record.strip():
        amount = int(mid_union(record, amount_pos, 15)) if amount_pos else 0
        man = int(mid_union(record, man_pos, 15)) if man_pos else 0
        tax = int(mid_union(record, tax_pos, 15)) if tax_pos else 0
        return amount, man, tax
    return 0, 0, 0
def save_elecfile_Pay(request):
  if request.method != "POST":
      return HttpResponse("Invalid request method.")
  
  # 파일 업로드 처리 (폼 필드 이름: "uploadFile")
  uploaded_file = request.FILES.get("uploadFile")
  if not uploaded_file:
      return HttpResponse("No file uploaded.")
  #접수아이디 파일저장시 최종 리턴하여 Grid 업데이트
  userID = "";seq_no = ""
  # 파일명에서 경로 제거 후 파일명 추출
  user_file_name = os.path.basename(uploaded_file.name)
  # 파일명과 확장자 분리 (예: "example.01" -> ("example", ".01"))
  file_name, file_ext = os.path.splitext(user_file_name)
  ext = file_ext[1:]  # 앞의 '.' 제거
  # 파일 확장자가 "01" 또는 "03"이 아니면 경고 후 중단
  if not file_name.endswith("103900"):
      return HttpResponse(
          "<script language='javascript'>"
          "alert('원천세 전자신고 파일이 아닙니다.');"
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

  # 파일 저장
  with open(save_file_name, "wb") as destination:
      for chunk in uploaded_file.chunks():
          destination.write(chunk)

  # 파일 레코드 저장을 위한 리스트 선언
  record_21 = []
  record_23A01 = []
  record_23A03 = []
  record_23A10 = []
  record_23A20 = []
  record_23A30 = []
  record_23A40 = []
  record_23A50 = []
  record_23A60 = []
  record_23A80 = []
  record_23A99 = []
  sqnos = []
  # 파일 읽기 (cp949 인코딩)
  with open(save_file_name, "r", encoding="cp949", errors="ignore") as f:
      for line in f:
          sr = line.rstrip("\n")
          if sr.startswith("21C"):
              record_21.append(sr)
              record_23A01.append("")
              record_23A03.append("")
              record_23A10.append("")
              record_23A20.append("")
              record_23A30.append("")
              record_23A40.append("")
              record_23A50.append("")
              record_23A60.append("")
              record_23A80.append("")
              record_23A99.append("")
          else:
              if not record_21:
                  continue
              idx = len(record_21) - 1
              if sr.startswith("23C103900A01"):
                  record_23A01[idx] = sr
              elif sr.startswith("23C103900A03"):
                  record_23A03[idx] = sr
              elif sr.startswith("23C103900A10"):
                  record_23A10[idx] = sr
              elif sr.startswith("23C103900A20"):
                  record_23A20[idx] = sr
              elif sr.startswith("23C103900A30"):
                  record_23A30[idx] = sr
              elif sr.startswith("23C103900A40"):
                  record_23A40[idx] = sr
              elif sr.startswith("23C103900A50"):
                  record_23A50[idx] = sr
              elif sr.startswith("23C103900A60"):
                  record_23A60[idx] = sr
              elif sr.startswith("23C103900A80"):
                  record_23A80[idx] = sr                  
              elif sr.startswith("23C103900A99"):
                  record_23A99[idx] = sr

  # 데이터베이스 작업 시작
  with connection.cursor() as cursor:
    for k in range(len(record_21)):
      primary = record_21[k]
      wcA = mid_union(primary, 32, 6)  # 과세연월
      wcB = "원천징수이행상황신고서"
      wcD = mid_union(primary, 27, 2)
      wcD = {"01": "정기신고", "02": "수정신고", "03": "기한후 신고"}.get(wcD, wcD)
      wcC = "정기(확정)"
      wcE = mid_union(primary, 131, 15).strip()
      wcF = f"{mid_union(primary,10,3)}-{mid_union(primary,13,2)}-{mid_union(primary,15,5)}"
      biz_no = wcF
      wcJ = mid_union(primary, 38, 6)  # 지급연월
      wcK = mid_union(primary, 44, 6)  # 제출연월
      issueID = mid_union(primary, 50, 13).strip()
      userID = issueID
      # 세금 데이터 처리

      wcL = wcLman = wcLtax = 0
      wcR = wcRman = wcRtax = 0
      wcM = wcMman = wcMtax = 0
      wcN = wcNman = wcNtax = 0
      wcO = wcOman = wcOtax = 0
      wcP = wcPman = wcPtax = 0
      wcQ = wcQman = wcQtax = 0
      wcS = wcSman = wcStax = 0
      wcZ = wcZman = wcZtax = 0

      # 데이터 추출
      wcL, wcLman, _ = extract_value(record_23A01[k], 28, 13)  # A01 근로소득 간이세액
      wcR, wcRman, _ = extract_value(record_23A03[k], 28, 13)  # A03 근로소득 일용근로
      _, _, wcLtax = extract_value(record_23A10[k], 103)  # A10 근로 전체 세금
      wcM, wcMman, wcMtax = extract_value(record_23A20[k], 28, 13, 103)  # A20 퇴직소득
      wcN, wcNman, wcNtax = extract_value(record_23A30[k], 28, 13, 103)  # A30 사업소득
      wcO, wcOman, wcOtax = extract_value(record_23A40[k], 28, 13, 103)  # A40 기타소득
      wcP, wcPman, wcPtax = extract_value(record_23A50[k], 28, 13, 103)  # A50 이자소득
      wcQ, wcQman, wcQtax = extract_value(record_23A60[k], 28, 13, 103)  # A60 배당소득
      wcS, wcSman, wcStax = extract_value(record_23A80[k], 28, 13, 103)  # A80 법인원천 이자소득
      wcZ, wcZman, wcZtax = extract_value(record_23A99[k], 28, 13, 103)  # A99 전체합계

      wcManDate = datetime.datetime.now().strftime("%Y%m%d")

      # 기존 데이터 확인 후 UPDATE 또는 INSERT 실행
      check_query = "SELECT * FROM 원천세전자신고 WHERE 과세연월=%s AND 사업자등록번호=%s"
      cursor.execute(check_query, [wcA, wcF])
      exists = cursor.fetchone()

      if exists:
        update_query = """
            UPDATE 원천세전자신고
            SET 지급연월=%s, 제출연월=%s, A01=%s, A03=%s, A20=%s, A30=%s, A40=%s, A50=%s, A60=%s, A99=%s,작성일자=%s, 제출자=%s
                ,A01M = %s,A03M = %s,A20M = %s,A30M = %s,A40M = %s,A50M = %s,A60M = %s,A99M = %s,A10T = %s,A20T = %s,A30T = %s,A40T = %s,A50T = %s,A60T = %s,A99T = %s
                ,A80 = %s,A80M = %s,A80T = %s
            WHERE 과세연월=%s AND 사업자등록번호=%s
        """
        cursor.execute(update_query, [wcJ, wcK, wcL, wcR, wcM, wcN, wcO, wcP, wcQ, wcZ, wcManDate, issueID, 
                                      wcLman,wcRman,wcMman,wcNman,wcOman,wcPman,wcQman,wcZman,wcLtax,wcMtax,wcNtax,wcOtax,wcPtax,wcQtax,wcZtax,
                                      wcS,wcSman,wcStax,
                                      wcA, wcF])
      else:
        insert_query = """
            INSERT INTO 원천세전자신고 (과세연월, 신고서종류, 신고구분, 신고유형, 상호, 사업자등록번호,
                지급연월, 제출연월, A01, A03, A20, A30, A40, A50, A60, A99, 작성일자, 
                A01M, A03M, A20M, A30M, A40M, A50M, A60M, A99M, A10T, A20T, A30T, A40T, A50T, A60T, A99T, 제출자, A80, A80M, A80T)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        """
        values = (
          wcA, wcB, wcC, wcD, wcE, wcF, wcJ, wcK, wcL, wcR, wcM, wcN, wcO, wcP, wcQ, wcZ, wcManDate, 
          wcLman,wcRman,wcMman,wcNman,wcOman,wcPman,wcQman,wcZman,wcLtax,wcMtax,wcNtax,wcOtax,wcPtax,wcQtax,wcZtax,  issueID  ,wcS,wcSman,wcStax
        )
        cursor.execute(insert_query, values)

        memuser = get_object_or_404(MemUser, biz_no=biz_no)
        sqnos.append({"userID": userID, "seq_no": memuser.seq_no})
  return JsonResponse({"success": True, "sqnos": sqnos})

#전자신고 접수번호 저장 - 클립보드 타입 - 법인세 전용
def save_clipboard_Pay(request):
  if request.method == 'POST':
    sqnos = []
    clipboardData   = request.POST.get("clipboardData")
    if clipboardData:
      fields = [field.strip() for field in clipboardData.split('\t')]
      wcA = fields[0]      # 0:2023년12월
      wcB = fields[1]    # 1:원천징수이행상황신고서
      wcC = fields[2]   # 2:정기(확정)
      wcD = fields[3]   # 3:정기신고
      wcE = fields[4]    # 4:주식회사 지에스디테크
      wcF = fields[5]     # 5:677-87-01488
      wcG = fields[6]  # 6:인터넷(변환)
      wcH = fields[7]    # 7:2025-02-13 16:55:44
      wcI = fields[8]  # 8:125-2025-2-504388903630
      wcJupsuGB = fields[9]   # 9:접수서류 18종

      # "YYYY년M월" 형식을 "YYYYMM" 형식으로 변환
      strmm = wcA[-3:].replace("년", "").replace("월", "")
      # 월이 한 자리 숫자면 앞에 "0" 추가
      if len(strmm) == 1:
          strmm = "0" + strmm
      # 최종 wcA 값 생성 (YYYYMM 형식)
      wcA = wcA[:4] + strmm

      with connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM 원천세전자신고 WHERE 과세연월='{wcA}' AND 사업자등록번호='{wcF}'")
        row_count = cursor.fetchone()[0]
        if row_count > 0:
          strsql = f"update 원천세전자신고 set  접수일시='{wcH}',접수번호='{wcI}',접수여부='{wcG}' WHERE 과세연월='{wcA}' AND 사업자등록번호='{wcF}'"
          print(strsql)
          cursor.execute(strsql)
        else:
          insert_query = """
              INSERT INTO 원천세전자신고 (
                  과세연월, 신고서종류, 신고구분, 신고유형, 상호, 사업자등록번호, 접수일시, 접수번호, 접수여부, 지급연월, 제출연월, 
                  A01, A20, A30, A40, A50, A99, 작성일자, 
                  A01M, A20M, A30M, A40M, A50M, A99M, 
                  A03, A03M, A60, A60M, 
                  A10T, A20T, A30T, A40T, A50T, A60T, A99T, 제출자,A80,A80M,A80T
              ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, 
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
          """
          values = (
              wcA, wcB, wcC, wcD, wcE, wcF, wcH, wcI, wcG, '','',0, 0, 0, 0, 0, 0, 0,     0, 0, 0, 0, 0, 0,   0, 0, 0, 0,   0, 0, 0, 0, 0, 0, 0, '',0,0,0
          )
          cursor.execute(insert_query, values)

        memuser = get_object_or_404(MemUser, biz_no=wcF)
        sqnos.append({"seq_no": memuser.seq_no})
      return JsonResponse({"status": "success", "sqnos": sqnos}, status=200)

  return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def path_to_pay(request):
  #data = json.loads(request.body)  # stringfy로 넘어오는 경우
  path = request.POST.get("path", "")
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    totTitleArr = [];totfileArr = [];tmpNow="";tmpAfter=""
    cnt=0;
    for x in natsort.natsorted(os.listdir(path)):
      tmpExt = os.path.splitext(x)[1]
      if ("월" in x[:3]) and os.path.isfile(path+"/"+x) and x!="Thumbs.db" and (tmpExt==".pdf" or tmpExt==".jpg" or tmpExt==".png" or tmpExt==".jpeg" ):
        dueDate=""
        fileMM = int(os.path.splitext(x)[0].split(" ")[0].replace("월",""))
        if fileMM==12:
          dueDate = "1월 10일"
        else:
          dueDate = str(fileMM+1)+"월 10일"

        files = {
          'group':x.split(" ")[0]+" 원천징수",
          '파일명':os.path.splitext(x)[0].split(" ")[1],
          'id':str(cnt),
          'totalPath':path+"/"+x,
          'dueDate':dueDate
        }
        tmpNow = x.split(" ")[0]
        if tmpAfter!=tmpNow:
          titles = {
            'displayName':x.split(" ")[0]+" 원천징수",
          }
          totTitleArr.append(titles)
        tmpAfter = tmpNow

        if len(os.listdir(path))>0:
          totfileArr.append(files)
        cnt = cnt+1
    d['titles'] = totTitleArr    
    d['nodes'] = totfileArr
  return JsonResponse(d,safe=False)

#이메일 보낼 파일들을 모아서 리턴
def get_folder_files(request):

    biz_name = request.GET.get("biz_name")
    work_YY = request.GET.get("work_YY")
    work_MM = request.GET.get("work_MM")

    if not biz_name or not work_YY or not work_MM:
        return JsonResponse({"error": "잘못된 요청입니다. (company, year, month 필요)"}, status=400)

    folder_path = os.path.join( "static/cert_DS/", biz_name, str(work_YY), "인건비")

    if not os.path.exists(folder_path):
        return JsonResponse({"error": "폴더를 찾을 수 없습니다."}, status=404)

    # "N월"로 시작하는 파일 중 특정 파일 제외
    search_prefix = f"{work_MM}월"
    exclude_file = f"{work_MM}월 원천징수이행상황신고서.pdf"

    files = [
        file for file in os.listdir(folder_path)
        if file.startswith(search_prefix) and file != exclude_file
    ]

    return JsonResponse({"files": files})


#cursor를 받아서 컬럼명과 함께 dict를 반환한다 "공백제거까지"
def dict_fetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [
      {col: (value.strip() if isinstance(value, str) else value) for col, value in zip(columns, row)}
      for row in cursor.fetchall()
  ]


#간이지급명세서 - 사업/일용
def _yyyymm(input_workyear: int, work_mm: int) -> str:
    return f"{input_workyear}{work_mm:02d}"

def _month_eng(work_mm: int) -> str:
    return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][work_mm-1]

@login_required
def kani_sa_il_page(request):
    """
    페이지는 1번만 렌더. grid 데이터는 JS에서 api_kani_sa_il_list로 가져옴.
    """
    # ===== 기본값(ASP 동일) =====
    today = datetime.date.today()
    input_workyear = request.GET.get("input_workyear")
    if not input_workyear:
        input_workyear = today.year - 1 if today.month <= 1 else today.year
    input_workyear = int(input_workyear)

    work_mm = request.GET.get("work_mm")
    if not work_mm:
        work_mm = today.month - 1
        if work_mm == 0:
            work_mm = 12
    work_mm = int(work_mm)

    # 담당자(ASP의 ADID/arrADID 개념) - 여기서는 기존 세션/권한 로직에 맞게 넣으세요.
    ADID = request.GET.get("ADID") or request.session.get("ADID") or ""
    # 예시: arrADID는 버튼 생성용
    with connection.cursor() as cur:
        cur.execute("""
            select distinct c.admin_id
            from mem_deal b
            join mem_admin c on b.biz_manager = c.admin_id
            where isnull(c.admin_id,'') <> ''
            order by c.admin_id
        """)
        arrADID = [r[0] for r in cur.fetchall()]

    ctx = {
        "input_workyear": input_workyear,
        "work_mm": work_mm,
        "selected_adid": ADID,
        "arrADID": arrADID,
    }
    return render(request, "admin/mng_kani_sa_il.html", ctx)


@require_GET
@login_required
def api_kani_sa_il_list(request):

    def DBG(title, value=None):
        print("\n" + "="*80)
        print(f"[DBG] {title}")
        if value is not None:
            print(value)
        print("="*80)

    try:
        today = datetime.date.today()

        input_workyear = request.GET.get("input_workyear")
        if not input_workyear:
            input_workyear = today.year - 1 if today.month <= 1 else today.year
        input_workyear = int(input_workyear)

        work_mm = request.GET.get("work_mm")
        if not work_mm:
            work_mm = today.month - 1
            if work_mm == 0:
                work_mm = 12
        work_mm = int(work_mm)

        ADID = (request.GET.get("ADID") or "").strip()
        search_text = (request.GET.get("search_text") or "").strip()

        text_mm = f"{work_mm:02d}"
        yyyymm = _yyyymm(input_workyear, work_mm)

        DBG("🔍 REQUEST PARAMS", {
            "input_workyear": input_workyear,
            "work_mm": work_mm,
            "ADID": ADID,
            "yyyymm": yyyymm
        })

        # -------------------------
        # 1) MAIN rows
        # -------------------------
        where_admin = ""
        params = []

        # ASP: 전체면 담당자 조건 없음
        if ADID and ADID != "전체":
            where_admin = " AND b.biz_manager = %s "
            params.append(ADID)

        where_search = ""
        if search_text:
            where_search = " AND (a.biz_name like %s OR a.biz_no like %s) "
            like = f"%{search_text}%"
            params += [like, like]

        # 2023 이하 / 2024 이상 분기 (원본 유지)
        if input_workyear <= 2023:
            cond_sum = f"""
                (
                  (select SUM(a03) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 과세연월='{yyyymm}')>0
                  or
                  (select SUM(a30) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 과세연월='{yyyymm}')>0
                )
            """
            a03_expr = f"(select sum(a03) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"
            a30_expr = f"(select sum(a30) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"
            a40_expr = f"(select sum(a40) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"
        else:
            cond_sum = f"""
                (
                  (select SUM(a03) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')>0
                  or
                  (select SUM(a30) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')>0
                  or
                  (select SUM(a40) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')>0
                )
            """
            a03_expr = f"(select sum(a03) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"
            a30_expr = f"(select sum(a30) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"
            a40_expr = f"(select sum(a40) from 원천세전자신고 d where a.biz_no=d.사업자등록번호 and 지급연월='{yyyymm}')"

        # ✅ 프론트 dataIndex에 맞춰 alias를 통일 (wh_Kunro / YN_9 / isBanki 등)
        sql_main = f"""
            SELECT
                b.biz_manager as groupManager,
                a.seq_no      as seq_no,
                a.biz_name    as biz_name,
                a.biz_no      as biz_no,

                ISNULL({a03_expr}, 0) as wh_Kunro,
                ISNULL({a30_expr}, 0) as wh_sayoup,
                ISNULL({a40_expr}, 0) as wh_kita,

                '' as isBanki,
                ISNULL((select bigo from tbl_mng_jaroe j
                        where j.seq_no=a.seq_no and j.work_yy={input_workyear} and j.work_mm={work_mm}), '') as isIlyoung,

                ISNULL(d.txt_bigo,'') as YN_9
            FROM mem_user a
            JOIN mem_deal b ON a.seq_no=b.seq_no
            LEFT JOIN tbl_kani d
              ON b.seq_no=d.seq_no
             AND d.work_yy=%s
             AND d.work_banki=%s
            WHERE a.duzon_ID <> ''
              AND {cond_sum}
              {where_admin}
              {where_search}
            ORDER BY a.biz_name ASC
        """

        # ⚠️ 이전에 work_banki가 int 컬럼인데 'Jan' 같은 값이 들어가 변환 에러 났던 이슈가 있었음
        # 지금은 work_mm을 문자열로 넘겨 해결했으니 유지
        params_main = [input_workyear, str(work_mm)] + params

        rows = []
        biz_no_list = []

        with connection.cursor() as cur:
            DBG("MAIN SQL", sql_main)
            DBG("MAIN PARAMS", params_main)
            cur.execute(sql_main, params_main)

            cols = [c[0] for c in cur.description]
            for r in cur.fetchall():
                item = dict(zip(cols, r))
                rows.append(item)
                biz_no_list.append(item["biz_no"])

            DBG(f"📊 MAIN QUERY - Found {len(rows)} rows")

        # -------------------------
        # 2) 지급조서간이소득 1번에 조회 → biz_no별로 누적
        # (ASP: rs("biz_no")별로 조회하던 것을 일괄 조회로 최적화)
        # -------------------------
        text_mm_eng = _month_eng(work_mm)
        text_mm_eng2 = f"{input_workyear}-{text_mm}"   # 예: 2025-11
        kwase_key1 = f"{text_mm_eng}-{input_workyear-2000}"  # 예: Nov-25
        kwase_key2 = text_mm_eng2

        income_map = defaultdict(lambda: {"kun": 0, "sa": 0, "ki": 0,
                                          "hasKun": False, "hasSa": False, "hasKi": False})

        if biz_no_list:
            placeholders = ",".join(["%s"] * len(biz_no_list))
            sql_income = f"""
                SELECT
                    사업자번호,
                    LTRIM(RTRIM(REPLACE(신고서종류,' ',''))) as kind,
                    ISNULL(제출금액,0) as amt
                FROM 지급조서간이소득
                WHERE CAST(과세년도 as varchar(20)) IN (%s, %s)
                  AND 사업자번호 IN ({placeholders})
            """
            params_income = [kwase_key1, kwase_key2] + biz_no_list

            with connection.cursor() as cur:
                DBG("INCOME SQL", sql_income)
                DBG("INCOME PARAMS(head)", params_income[:12])
                cur.execute(sql_income, params_income)

                income_rows = cur.fetchall()
                DBG(f"📊 INCOME QUERY - Found {len(income_rows)} rows")

                for biz_no, kind, amt in income_rows:
                    amt = int(amt or 0)
                    if kind == "일용근로소득지급명세서":
                        income_map[biz_no]["kun"] += amt
                        income_map[biz_no]["hasKun"] = True
                    elif kind == "간이지급명세서(거주자의사업소득)":
                        income_map[biz_no]["sa"] += amt
                        income_map[biz_no]["hasSa"] = True
                    elif kind == "간이지급명세서(거주자의기타소득)":
                        income_map[biz_no]["ki"] += amt
                        income_map[biz_no]["hasKi"] = True

        # -------------------------
        # 3) ASP처럼 rows에 합치기 + skeleton 판정
        # -------------------------
        def _to_int(x):
            try:
                return int(str(x).replace(",", "").strip() or 0)
            except:
                return 0

        out = []
        for idx, r in enumerate(rows):
            biz_no = r.get("biz_no") or ""
            wh_k = _to_int(r.get("wh_Kunro"))
            wh_s = _to_int(r.get("wh_sayoup"))
            wh_i = _to_int(r.get("wh_kita"))

            kunAmt = income_map[biz_no]["kun"]
            saAmt  = income_map[biz_no]["sa"]
            kiAmt  = income_map[biz_no]["ki"]

            # ASP: (제출금액합) != (a03+a30+a40) 이면 skeleton
            hasSkeleton = (kunAmt + saAmt + kiAmt) != (wh_k + wh_s + wh_i)

            out.append({
                "YN_0": idx,

                "groupManager": r.get("groupManager", "") or "",
                "seq_no": r.get("seq_no"),
                "biz_name": r.get("biz_name", "") or "",
                "biz_no": biz_no,

                "isBanki": True if str(r.get("banki", "")).strip() == "1" else False,

                "wh_Kunro": wh_k,
                "wh_sayoup": wh_s,
                "wh_kita": wh_i,

                # ✅ 아이콘 대신 플래그/값만 내려준다
                "isKun": income_map[biz_no]["hasKun"],
                "isKunAmt": kunAmt,

                "isIlyoung": r.get("isIlyoung", "") or "",

                "isSa": income_map[biz_no]["hasSa"],
                "isSaAmt": saAmt,

                "isKi": income_map[biz_no]["hasKi"],
                "isKiAmt": kiAmt,

                "YN_9": r.get("YN_9", "") or "",

                "isSkele": True if (hasSkeleton and ((kunAmt+saAmt+kiAmt) != 0 or (wh_k+wh_s+wh_i) != 0)) else False,
            })

        DBG(f"✅ RESPONSE SUCCESS - Returning {len(out)} rows")
        return JsonResponse({"ok": True, "rows": out})

    except Exception as e:
        DBG("❌ EXCEPTION", str(e))
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e), "rows": []}, status=500)

@csrf_exempt
@require_POST
@login_required
def api_kani_sa_il_update(request):
    """
    그리드 셀 수정 저장:
    - isIlyoung(접수번호) -> 원본: ajax_proc_Total_ilyoungIssue.asp
    - YN_9(차이원인 txt_bigo) -> 원본: ajax_proc_kani_sa-il.asp
    """
    seq_no = request.POST.get("seq_no")
    field = request.POST.get("field")
    work_yy = int(request.POST.get("work_yy"))
    work_mm = int(request.POST.get("work_mm"))
    val = request.POST.get("val", "")

    if not seq_no or field not in ("isIlyoung", "YN_9"):
        return JsonResponse({"ok": False, "msg": "bad request"}, status=400)

    with connection.cursor() as cur:
        if field == "isIlyoung":
            # tbl_mng_jaroe의 bigo에 저장하던 로직(원본대로 맞춰서 테이블/컬럼 조정)
            cur.execute("""
                update tbl_mng_jaroe
                   set bigo=%s
                 where seq_no=%s and work_yy=%s and work_mm=%s
            """, [val, seq_no, work_yy, work_mm])
        else:
            # tbl_kani.txt_bigo 저장(원본 txt_bigo)
            # 없으면 upsert
            cur.execute("""
                if exists(select 1 from tbl_kani where seq_no=%s and work_yy=%s and work_banki=%s)
                    update tbl_kani set txt_bigo=%s where seq_no=%s and work_yy=%s and work_banki=%s
                else
                    insert into tbl_kani(seq_no, work_yy, work_banki, txt_bigo)
                    values(%s,%s,%s,%s)
            """, [seq_no, work_yy, work_mm, val, seq_no, work_yy, work_mm,
                  seq_no, work_yy, work_mm, val])

    return JsonResponse({"ok": True})


@csrf_exempt
@require_POST
@login_required
def api_kani_sa_il_paste_issue(request):
    """
    '접수번호저장' 팝업에서 붙여넣기 데이터 저장 (ajax_pasteExcel_ZKKN.asp 역할)
    요청 파라미터: wc2..wc12
    저장 로직은 기존 ASP 저장 테이블/프로시저에 맞게 구현 필요.
    여기서는 예시로만 둠.
    """
    wc2 = request.POST.get("wc2","")
    wc3 = request.POST.get("wc3","")  # 사업자번호
    wc4 = request.POST.get("wc4","")
    wc5 = request.POST.get("wc5","")
    wc7 = request.POST.get("wc7","")
    wc8 = request.POST.get("wc8","")
    wc9 = request.POST.get("wc9","")
    wc10 = request.POST.get("wc10","")
    wc11 = request.POST.get("wc11","")
    wc12 = request.POST.get("wc12","")  # 접수번호

    # TODO: 실제 저장 대상(테이블/프로시저)을 ASP와 동일하게 맞추세요.
    # 예: 접수번호 테이블에 insert, 또는 관련 업무 테이블 업데이트 등
    # 여기서는 ok만 반환
    return JsonResponse({"ok": True})