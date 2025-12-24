import datetime
import calendar
import os
from dateutil.relativedelta import relativedelta
from django.shortcuts import render,redirect,get_object_or_404
from decimal import Decimal, ROUND_DOWN
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from app.models import MemAdmin
from app.models import TblFault  # 모델 임포트
from django.db import connection
from django.utils import timezone
from pdf2image import convert_from_path
from django.db.models import Q
from django.db.models import Sum, F
from admins.utils import send_kakao_notification
from django.conf import settings
from django.core.files.storage import FileSystemStorage

@login_required(login_url="/login/")
def index(request):
  ADID = request.session.get('Admin_Id')
  admin_grade     = request.session.get('Admin_Grade')
  context = {}
  flag = request.GET.get("flag")

  today = datetime.datetime.now()
  corpYear = today.year-1
  currentMonth = today.month
  currentYear = today.year
  if currentMonth >= 7 :
    corpYear = today.year

  corpYears = list(range(corpYear, corpYear - 6, -1))
  context['admin_grade'] = admin_grade
  context['corpYears'] = corpYears

  templateMenu = gridTitle=""
  if flag == None:
    # 팀별로 그룹화된 데이터 생성
    all_admins = MemAdmin.objects.all().order_by('admin_biz_area', 'biz_level', 'admin_name')

    # 세무사(팀장) 목록 추출
    team_leaders = all_admins.filter(biz_level='세무사')

    # 팀별 데이터 구조 생성
    teams = []
    for leader in team_leaders:
      # 같은 admin_biz_area를 가진 직원들 찾기
      team_members = all_admins.filter(
        admin_biz_area=leader.admin_biz_area,
        biz_level='직원'
      ).order_by('admin_name')

      teams.append({
        'leader': leader,
        'members': list(team_members)
      })

    # 팀에 속하지 않은 직원들 (admin_biz_area가 없거나 매칭되는 세무사가 없는 경우)
    assigned_areas = [team['leader'].admin_biz_area for team in teams]
    unassigned_admins = all_admins.filter(biz_level='직원').exclude(admin_biz_area__in=assigned_areas)

    # 관리자 및 기타
    other_admins = all_admins.filter(biz_level='관리자')

    context['teams'] = teams
    context['unassigned_admins'] = unassigned_admins
    context['other_admins'] = other_admins
    context['adminList'] = all_admins  # 기존 호환성 유지
    templateMenu = 'admin/staffList.html'; gridTitle="관리자리스트"
  elif flag == "Pro":
    context['adminList'] =  MemAdmin.objects.filter(biz_level='세무사', grade='MEM').order_by('admin_name')
    context['invoiceAll'] = invoiceList(ADID,admin_grade,currentMonth,currentYear,corpYears)
    templateMenu = 'admin/staffInfo_Promotion.html'; gridTitle="업무성과금"
  elif flag == "SalePro":

    context['invoiceAll'] = invoiceList_Sale(ADID,admin_grade,currentMonth,currentYear)
    templateMenu = 'admin/sales_Promotion.html'; gridTitle="영업수당"
  context['gridTitle'] = gridTitle

  return render(request, templateMenu,context)

#마케팅수당

def invoiceList_Sale(ADID,admin_grade,currentMonth,currentYear):
  admin_data =  MemAdmin.objects.filter(biz_level='세무사', grade='SALE').values_list('admin_name', 'reg_date')
  if admin_grade != "SA":
    admin_data =  MemAdmin.objects.filter(biz_level='세무사', grade='SALE',admin_id = ADID).values_list('admin_name', 'reg_date')
    print(admin_data)
  today = datetime.datetime.now()
  workArr = []
  # 시작과 종료 연월 설정
  start_year, start_month = 2025, 1
  # 오늘 날짜에서 8개월 뒤의 연도와 월 계산
  end_date = today + relativedelta(months=8)
  end_year, end_month = end_date.year, end_date.month

  year, month = start_year, start_month
  # 종료 연월까지 반복하며 workArr 구성
  while (year < end_year) or (year == end_year and month <= end_month):
    workArr.append((year, month))
    # 다음 달 계산
    if month == 12:
        year += 1
        month = 1
    else:
        month += 1
  # 생성된 workArr 출력 (확인용)
  invoiceAll=[]
  for admin_name, reg_date in admin_data:
    for work_YY, work_MM in workArr:
      # print(work_YY, work_MM)
      sql_query = f"""
        DECLARE @today DATE = '{work_YY}-{str(work_MM).zfill(2)}-01';
        DECLARE @this_month_first DATE = DATEFROMPARTS(YEAR(@today), MONTH(@today), 1);
        DECLARE @month_8_before DATE = DATEADD(MONTH, -8, @this_month_first);
        SELECT 
          SUM(
              CASE
                  -- 이번달 계약건 (모두 8배 지급)
                  WHEN DATEFROMPARTS(YEAR(b.createddate), MONTH(b.createddate), 1) = @this_month_first THEN feeamt * 8
                  
                  -- 8개월 전 계약건
                  WHEN DATEFROMPARTS(YEAR(DATEADD(MONTH, 8, b.createddate)), MONTH(DATEADD(MONTH, 8, b.createddate)), 1) = @this_month_first THEN 
                      CASE
                          WHEN Biz_Type >= 4 THEN feeamt * 6
                          ELSE feeamt * 8
                      END
                  ELSE 0
              END
          ) AS total_payment_amount
        FROM 
            mem_user a
        JOIN 
            mem_deal b ON a.seq_no = b.seq_no
        JOIN 
            mem_admin c ON b.biz_manager = c.admin_id
        WHERE 
            a.Del_YN <> 'Y'
            and  b.createddate>'2025-01-01'
            AND (b.biz_manager = N'{admin_name}' OR a.biz_par_chk = N'{admin_name}')
            AND (
                DATEFROMPARTS(YEAR(DATEADD(MONTH, 8, b.createddate)), MONTH(DATEADD(MONTH, 8, b.createddate)), 1) = @this_month_first
                OR
                DATEFROMPARTS(YEAR(b.createddate), MONTH(b.createddate), 1) = @this_month_first
            );
      """  
      
      with connection.cursor() as cursor:
        cursor.execute(sql_query)
        promoAmt = cursor.fetchone()[0] 
        if promoAmt:
          promoAmt = int(promoAmt)
        else:
          promoAmt = 0
        if promoAmt>0:
          isCorpPaid = "?";corpColor = 'info'

          if currentYear==work_YY and currentMonth==work_MM:
            isCorpPaid = "영업중"
            corpColor = 'info'                      
          elif (currentYear==work_YY and currentMonth<work_MM) or (currentYear<work_YY):
            isCorpPaid = "정산예정"
            corpColor = 'pink'
          elif (currentYear==work_YY and currentMonth>work_MM) or (currentYear>work_YY):
            isCorpPaid = "정산완료"
            corpColor = 'primary'            
          formatDate = f"{work_YY}년 {work_MM}월 말일"
          invoiceCorp = {'work_YY':work_YY,'work_MM':str(work_MM),'title':f'{work_MM}월 마케팅 수당내역','admin_name':admin_name,'reg_date':formatDate,'reg_title':'정산월','promoAmt':promoAmt,'isCorpPaid':isCorpPaid,'corpColor':corpColor}
          invoiceAll.append(invoiceCorp)
  return invoiceAll

#마케팅수당 - 상세내역 모달
@csrf_exempt
def getSalesInvoiceDetail(request):
  ADID = request.POST.get('ADID')
  work_YY = request.POST.get('work_YY')
  work_MM = request.POST.get('work_MM')
  if ADID:
      sql_query = f"""
        DECLARE @today DATE = '{work_YY}-{str(work_MM).zfill(2)}-01';
        DECLARE @this_month_first DATE = DATEFROMPARTS(YEAR(@today), MONTH(@today), 1);
        DECLARE @month_8_before DATE = DATEADD(MONTH, -8, @this_month_first);
        SELECT 
          biz_name,
          Biz_Type,
          Biz_Par_Chk,
          Biz_Par_Rate,
          kijang_yn,
          b.createddate,
          feeamt,
          -- 전체 계약금액 계산
          CASE 
              WHEN Biz_Type < 4 THEN feeamt * 16
              WHEN Biz_Type >= 4 AND Biz_Par_Rate = 1 THEN feeamt * 16
              WHEN Biz_Type >= 4 THEN feeamt * 14
              ELSE 0
          END AS total_payment_amount,

          -- 이번달 금액 계산
          CASE 
              WHEN Biz_Type < 4 THEN feeamt * 8
              WHEN Biz_Type >= 4 AND Biz_Par_Rate = 1 THEN feeamt * 8
              WHEN Biz_Type >= 4 THEN feeamt * 8
              ELSE 0
          END AS payment_amount,

          -- ★잔여분 지급금액 컬럼 추가
          CASE 
              WHEN Biz_Type < 4 THEN feeamt * 8
              WHEN Biz_Type >= 4 AND Biz_Par_Rate = 1 THEN feeamt * 8
              WHEN Biz_Type >= 4 THEN feeamt * 6
              ELSE 0
          END AS remaining_payment_amount,

          -- 지급 이유
          CASE 
              WHEN DATEFROMPARTS(YEAR(DATEADD(MONTH, 8, b.createddate)), MONTH(DATEADD(MONTH, 8, b.createddate)), 1) = @this_month_first THEN N'잔여분 지급'
              WHEN DATEFROMPARTS(YEAR(b.createddate), MONTH(b.createddate), 1) = @this_month_first THEN N'당월분 지급'
              ELSE N'해당없음'
          END AS payment_reason,
          -- 잔여분 지급월
          DATEFROMPARTS(YEAR(DATEADD(MONTH, 8, b.createddate)), MONTH(DATEADD(MONTH, 8, b.createddate)), 1) AS next_payment_due_month

        FROM 
            mem_user a
        JOIN 
            mem_deal b ON a.seq_no = b.seq_no
        JOIN 
            mem_admin c ON b.biz_manager = c.admin_id
        WHERE 
            a.Del_YN <> 'Y'
            and  b.createddate>'2025-01-01'
            AND (b.biz_manager = N'{ADID}' OR a.biz_par_chk = N'{ADID}')
            AND (
                DATEFROMPARTS(YEAR(DATEADD(MONTH, 8, b.createddate)), MONTH(DATEADD(MONTH, 8, b.createddate)), 1) = @this_month_first
                OR
                DATEFROMPARTS(YEAR(b.createddate), MONTH(b.createddate), 1) = @this_month_first
            );
      """  
      print(sql_query)
      with connection.cursor() as cursor:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        promoData = []
        for row in rows:
          if int(row[1])<4:
            txtBiztype = "법인"
          else:
            if int(row[3])<1:
              txtBiztype = "개인"
            else:
              txtBiztype = "성실"
          promoDetail = {
              "biz_name": row[0],
              "Biz_Type": txtBiztype,
              "Biz_Par_Chk": row[2],
              "createddate": row[5].strftime('%Y-%m-%d'),
              "feeamt": row[6], 
              "total_payment_amount": row[7],  
              "payment_amount": row[8],
              "remaining_payment_amount": row[9],
              "payment_reason": row[10],
              "next_payment_due_month": row[11].strftime('%Y-%m')
            } 
          promoData.append(promoDetail)
        return JsonResponse({"data": promoData})
  else:
      return JsonResponse({'error': 'Invalid request method.'}, status=400)

#업무수당 - 전체리스트
def invoiceList(ADID, admin_grade, currentMonth, currentYear, corpYears):
  invoiceAll = []
  today = datetime.datetime.now()
  
  # ✅ 관리자 목록 가져오기
  admin_data = MemAdmin.objects.filter(biz_level='세무사', grade='MEM').values_list('admin_name', 'reg_date')
  if admin_grade != "SA":
      admin_data = MemAdmin.objects.filter(biz_level='세무사', grade='MEM', admin_id=ADID).values_list('admin_name', 'reg_date')
      print("관리자 제한:", ADID)

  # ✅ 법인연도 루프
  for corpYear in corpYears:
      # ✅ 세무사(admin) 루프
      for admin_name, reg_date in admin_data:
        formatDate = f"{reg_date.year}년 {reg_date.month}월 {reg_date.day}일"

        # ✅ 신고기간 상태 계산
        march_deadline = datetime.datetime.strptime(f"{corpYear+1}-03-01", "%Y-%m-%d")
        may_deadline = datetime.datetime.strptime(f"{corpYear+1}-05-01", "%Y-%m-%d")
        July_deadline = datetime.datetime.strptime(f"{corpYear}-07-01", "%Y-%m-%d")
        Aug_deadline = datetime.datetime.strptime(f"{corpYear}-08-01", "%Y-%m-%d")
        Jan_deadline = datetime.datetime.strptime(f"{corpYear+1}-02-01", "%Y-%m-%d")
        Feb_deadline = datetime.datetime.strptime(f"{corpYear+1}-02-01", "%Y-%m-%d")

        # ✅ title-테이블 매핑
        title_table_map = {
            "법인세신고": "tbl_corporate2",
            "종합소득세신고": "tbl_income2",
            "부가세(1기확정)": "tbl_vat",
            "부가세(2기확정)": "tbl_vat"
        }

        titles = ["법인세신고", "종합소득세신고", "부가세(1기확정)", "부가세(2기확정)"]
        invoices = []
        isCorpPaid_status = ""
        corpColor_status = ""
        for title in titles:
          table_name = title_table_map[title]

          # ✅ 테이블별 조건 분기
          if table_name == "tbl_vat":
            ElecTable_Join = f""
            except_Condition = ""
            date_condition = f"d.YN_1 < '{corpYear+1}-05-02'"
            amt_col = "d.YN_12"
            flag_col = "d.YN_11"
            whamul_Condition = "AND b.biz_manager = '화물'"
            promoAmt_Condition = "FLOOR(-f.faultAmt * 0.3) AS promoAmt"
            faultAmt_Condition = f"AND NOT (f.AdaptOption = '법인세' AND LEFT(f.occurDate, 4) = '{corpYear}')"
            if title=="부가세(2기확정)":
              if today < Jan_deadline:
                  isCorpPaid_status = "신고기간 아님"
                  corpColor_status = "info"
              elif today < Feb_deadline:
                  isCorpPaid_status = "신고중"
                  corpColor_status = "danger"
              else:
                  isCorpPaid_status = "마감"
                  corpColor_status = "primary"    
            else:      
              if today < July_deadline:
                  isCorpPaid_status = "신고기간 아님"
                  corpColor_status = "info"
              elif today < Aug_deadline:
                  isCorpPaid_status = "신고중"
                  corpColor_status = "danger"
              else:
                  isCorpPaid_status = "마감"
                  corpColor_status = "primary"                               
          elif table_name == "tbl_income2":
            ElecTable_Join = f"LEFT JOIN 종합소득세전자신고2 e ON left(e.주민번호,6) = left(a.ssn,6) and a.ceo_name = e.이름 AND LEFT(e.과세년월, 4) = '{corpYear}'"
            except_Condition = "and (right(e.제출자,2)>40 or e.제출자='')"
            date_condition = f"d.YN_10 < '{corpYear+1}-07-31'"
            amt_col = "d.YN_8"
            flag_col = "d.YN_7"
            promoAmt_Condition = "FLOOR(-f.faultAmt * 0.05) AS promoAmt"
            whamul_Condition = "AND b.biz_manager <> '화물'"
            faultAmt_Condition = f"AND NOT (f.AdaptOption = '법인세' AND LEFT(f.occurDate, 4) = '{corpYear}')"
            if today < may_deadline:
                isCorpPaid_status = "신고기간 아님"
                corpColor_status = "info"
            elif today < July_deadline:
                isCorpPaid_status = "신고중"
                corpColor_status = "danger"
            else:
                isCorpPaid_status = "마감"
                corpColor_status = "primary"                  
          else:  # 법인세 (tbl_corporate2)
            ElecTable_Join = f"LEFT JOIN 법인세전자신고2 e  ON e.사업자번호 = a.biz_no AND LEFT(e.과세년월, 4) = '{corpYear}'"
            except_Condition = "and (right(e.사용자ID,2)>40 or e.사용자ID='')"
            date_condition = f"d.YN_10 < '{corpYear+1}-05-02'"
            amt_col = "d.YN_8"
            flag_col = "d.YN_7"
            promoAmt_Condition = "FLOOR(-f.faultAmt * 0.05) AS promoAmt"
            whamul_Condition = "AND b.biz_manager <> '화물'"
            faultAmt_Condition = ""
            if today < march_deadline:
                isCorpPaid_status = "신고기간 아님"
                corpColor_status = "info"
            elif today < may_deadline:
                isCorpPaid_status = "신고중"
                corpColor_status = "danger"
            else:
                isCorpPaid_status = "마감"
                corpColor_status = "primary"
          # ✅ SQL 작성
          sql_query = f"""
          SELECT 
              SUM(YN_8) AS total_YN_8,
              SUM(promoAmt) AS total_promoAmt
          FROM (
              SELECT 
                  ISNULL(SUM({amt_col}), 0) AS YN_8,
                  FLOOR(ISNULL(SUM({amt_col}), 0) * 0.05) AS promoAmt
              FROM mem_user a
              JOIN mem_deal b ON a.seq_no = b.seq_no
              JOIN mem_admin c ON b.biz_manager = c.admin_id
              JOIN {table_name} d ON a.seq_no = d.seq_no
              {ElecTable_Join}
              WHERE admin_name = '{admin_name}'
                {whamul_Condition}
                AND d.work_yy = {corpYear}
                AND {flag_col} = 1
                AND {date_condition}
                {except_Condition}
              UNION ALL

              SELECT 
                  -f.faultAmt AS YN_8,
                  {promoAmt_Condition}
              FROM tbl_fault f
              WHERE f.admin_id = '{admin_name}'
                AND LEFT(f.occurDate, 4) = '{corpYear}'
                {faultAmt_Condition}
          ) AS combined;
          """
          #print(sql_query)
          with connection.cursor() as cursor:
              cursor.execute(sql_query)
              total_YN_8, total_promoAmt = cursor.fetchone()  # 두 컬럼 모두 받기

          # ✅ Python에서 재계산 ❌ (DB에서 promoAmt 이미 계산했음)
          # ✅ 그냥 total_promoAmt 그대로 사용
          promoAmt = int(total_promoAmt) if total_promoAmt else 0

          invoice_data = {
              "corpYear": corpYear,
              "title": title,
              "admin_name": admin_name,
              "reg_date": formatDate,
              "promoAmt": promoAmt,
              "isCorpPaid": isCorpPaid_status,
              "corpColor": corpColor_status
          }
          invoices.append(invoice_data)

        # ✅ title별 dict 변환
        invoice_dict = {inv["title"]: inv for inv in invoices}

        # ✅ 조건별 invoiceAll에 append
        if currentYear == corpYear:
            if currentMonth <= 3:
                invoiceAll.append(invoice_dict["법인세신고"])
            elif currentMonth <= 5:
                invoiceAll.append(invoice_dict["법인세신고"])
                invoiceAll.append(invoice_dict["종합소득세신고"])
            elif currentMonth <= 7:
                invoiceAll.append(invoice_dict["법인세신고"])
                invoiceAll.append(invoice_dict["종합소득세신고"])
                if admin_name == "최에스더":
                    invoiceAll.append(invoice_dict["부가세(1기확정)"])
            elif currentMonth <= 12:
                invoiceAll.append(invoice_dict["법인세신고"])
                invoiceAll.append(invoice_dict["종합소득세신고"])
                if admin_name == "최에스더":
                    invoiceAll.append(invoice_dict["부가세(1기확정)"])
                    invoiceAll.append(invoice_dict["부가세(2기확정)"])
        else:
            invoiceAll.append(invoice_dict["법인세신고"])
            invoiceAll.append(invoice_dict["종합소득세신고"])
            if admin_name == "최에스더":
                invoiceAll.append(invoice_dict["부가세(1기확정)"])
                invoiceAll.append(invoice_dict["부가세(2기확정)"])

        print(f"✅ {admin_name} ({corpYear}) 처리 완료 → 총 {len(invoiceAll)}개")

  # ✅ 모든 admin_data 처리 후 결과 리턴
  return invoiceAll

#실수정보
def get_fault_data(request):
    admin_grade     = request.session.get('Admin_Grade')
    admin_id = request.GET.get("admin_id", "")
    fault_list = TblFault.objects.all().order_by("-occurDate")
    if admin_grade!="SA":
      fault_list = TblFault.objects.filter(admin_id=admin_id).order_by("-occurDate")

    data = [
        {
          "admin_id":fault.admin_id,
          "occurDate": fault.occurDate,
          "biz_name": fault.biz_name,
          "faultAmt": fault.faultAmt,
          "reason": fault.reason,
          "AdaptOption": fault.AdaptOption,
        }
        for fault in fault_list
    ]
    return JsonResponse({"data": data})

@csrf_exempt
def getInvoiceDetail(request):
    ADID = request.POST.get('ADID')
    title = request.POST.get('title')
    work_YY = request.POST.get('work_YY')
    
    if ADID:
        sql_query = ""
        
        # 1. 법인세 신고
        if title == "법인세신고":
            sql_query = f"""
                SELECT 
                    b.biz_manager,
                    e.사용자ID,
                    a.biz_name,
                    d.YN_8,
                    FLOOR(d.YN_8 * 0.05) AS promoAmt
                FROM mem_user a
                JOIN mem_deal b ON a.seq_no = b.seq_no
                JOIN mem_admin c ON b.biz_manager = c.admin_id
                JOIN tbl_corporate2 d ON a.seq_no = d.seq_no
                LEFT JOIN 법인세전자신고2 e ON e.사업자번호 = a.biz_no AND LEFT(e.과세년월, 4) = '{work_YY}'
                WHERE c.admin_name = '{ADID}'
                  AND d.work_yy = '{work_YY}'
                  AND d.YN_7 = 1        
                  AND d.YN_10 < '{int(work_YY)+1}-05-02'
                  AND (RIGHT(e.사용자ID, 2) > 40 OR e.사용자ID = '')

                UNION ALL

                SELECT 
                    f.admin_id AS biz_manager, '',
                    (TRIM(f.biz_name) + '@' + f.reason) AS biz_name, 
                    -f.faultAmt AS YN_8, 
                    -f.faultAmt * 0.05 AS promoAmt
                FROM tbl_fault f
                WHERE f.admin_id = '{ADID}'
                  AND LEFT(f.occurDate, 4) = '{work_YY}'
            """
        
        # 2. 종합소득세 및 부가세 신고
        elif title == "종합소득세신고" or "부가세" in title:
            # 변수 초기화
            table_join = ""
            e_join = ""
            date_condition = ""
            col_submitter = ""
            col_fee = ""
            
            # (1) 종합소득세 설정
            if title == "종합소득세신고":
                table_join = "JOIN tbl_income2 d ON a.seq_no = d.seq_no"
                e_join = f"LEFT JOIN 종합소득세전자신고2 e ON LEFT(e.주민번호,6) = LEFT(a.ssn,6) AND a.ceo_name = e.이름 AND LEFT(e.과세년월, 4) = '{work_YY}'"
                date_condition = f"AND d.YN_10 < '{int(work_YY)+1}-07-31'"
                col_submitter = "e.제출자"
                col_fee = "YN_8"
            # (2) 부가세 설정 (테이블명 tbl_vat 가정, 필요시 수정)
            else:
                # ★ [주의] 부가세 테이블 및 컬럼명이 실제 DB와 맞는지 확인 필요
                table_join = "JOIN tbl_vat d ON a.seq_no = d.seq_no" 
                
                # 부가세 전자신고 테이블 조인 (예시: 부가가치세전자신고3)
                # 기수(1기/2기)에 따라 로직이 달라질 수 있음
                vat_term = "1기" if "1기" in title else "2기"
                # e_join 로직은 실제 부가세 신고 테이블 구조에 맞춰 수정 필요
                e_join = f"LEFT JOIN 부가가치세전자신고3 e ON e.사업자등록번호 = a.biz_no AND e.과세기간 LIKE '%{vat_term}%' AND LEFT(e.신고시각, 4) = '{work_YY}'"
                
                # 수금 기한 등 조건
                date_condition = f"AND d.YN_10 < '{int(work_YY)+1}-02-28'" # 예시 날짜
                col_submitter = "e.제출자" # 예시 컬럼
                col_fee = "YN_12"
            # 쿼리 조립 (종소세/부가세 공통 구조)
            # ★ 여기서 title 체크를 제거하여 부가세도 쿼리가 만들어지도록 수정함
            sql_query = f"""
                SELECT 
                    b.biz_manager,
                    {col_submitter},
                    a.biz_name,
                    d.{col_fee},
                    FLOOR(d.{col_fee} * 0.05) AS promoAmt
                FROM mem_user a
                JOIN mem_deal b ON a.seq_no = b.seq_no
                JOIN mem_admin c ON b.biz_manager = c.admin_id
                {table_join}
                {e_join}
                WHERE c.admin_name = '{ADID}'
                  AND d.work_yy = {work_YY}
                  AND d.YN_7 = 1
                  {date_condition}
                  AND (TRY_CAST(RIGHT({col_submitter}, 2)AS INT) > 40 OR {col_submitter} = '' OR {col_submitter} IS NULL)
                  AND b.biz_manager <> '화물'
                
                UNION ALL

                SELECT 
                    f.admin_id AS biz_manager, '',
                    (TRIM(f.biz_name) + '@' + f.reason) AS biz_name, 
                    -f.faultAmt AS YN_8, 
                    -f.faultAmt * 0.05 AS promoAmt
                FROM tbl_fault f
                WHERE f.admin_id = '{ADID}'
                  AND LEFT(f.occurDate, 4) = '{work_YY}'
            """

        # 3. 쿼리 실행 및 결과 반환
        if sql_query:
            # 실수 차감 조건 추가 (종소세/부가세인 경우 법인세 실수 제외)
            if title in ("종합소득세신고", "부가세(1기확정)", "부가세(2기확정)"):
                sql_query += f"""
                  AND NOT (f.AdaptOption = '법인세' AND LEFT(f.occurDate, 4) = '{work_YY}')
                """
            
            # 정렬 추가
            sql_query += " ORDER BY biz_manager, biz_name;"
            
            rows = []
            with connection.cursor() as cursor:
                print(sql_query)
                cursor.execute(sql_query)
                rows = cursor.fetchall() # ★ [중요] 데이터 가져오기 추가됨

            # JSON 변환
            promoData = [
                {"biz_manager": row[0], "JupsuID": row[1], "biz_name": row[2], "YN_8": row[3], "promoAmt": row[4]}
                for row in rows
            ]
            return JsonResponse({"data": promoData})
        
        else:
            # 쿼리가 생성되지 않은 경우 (타이틀 불일치 등)
            return JsonResponse({"data": []})

    else:
        return JsonResponse({'error': 'Invalid request method or missing ADID.'}, status=400)
    
@csrf_exempt  # AJAX 요청을 위해 CSRF 해제 (보안 설정 필요시 CSRF 보호 사용)
def save_fault(request):
    if request.method == "POST":
        admin_id = request.POST.get("admin_id")
        occurDate = request.POST.get("occurDate")
        biz_name = request.POST.get("biz_name", "")
        faultAmt = request.POST.get("faultAmt", 0).replace(",","")
        reason = request.POST.get("reason", "")
        AdaptOption = request.POST.get("AdaptOption", "")

        try:
            # 날짜 형식 변환 (YYYY-MM-DD)
            occurDate = datetime.datetime.strptime(occurDate, "%Y-%m-%d").date()

            # 데이터 저장
            TblFault.objects.create(
                admin_id=admin_id,
                occurDate=occurDate,
                biz_name=biz_name,
                faultAmt=int(faultAmt),  # 숫자로 변환
                reason=reason,
                AdaptOption=AdaptOption
            )

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)

@csrf_exempt
def admin_create(request):
  if request.method == 'POST':
      admin_id = request.POST.get('admin_id')
      admin_pwd = request.POST.get('admin_pwd')
      admin_name = request.POST.get('admin_name')
      admin_tel_no = request.POST.get('admin_tel_no')
      admin_email = request.POST.get('admin_email')
      admin_biz_area = request.POST.get('admin_biz_area')
      biz_level = request.POST.get('biz_level')
      manage_YN = request.POST.get('manage_YN')
      grade = request.POST.get('grade')
      htx_id = request.POST.get('htx_id')

      # 새로운 Admin 객체 생성
      try:
        if User.objects.filter(username=admin_id).exists():
            # 이미 존재하는 경우 기존 User 객체 가져오기
            user = User.objects.get(username=admin_id)
        else:
            # 새로운 User 객체 생성 및 저장
            user = User.objects.create_user(username=admin_id, password=admin_pwd, email=admin_email, is_staff=1)

        # 새로운 Admin 객체 생성
        new_admin = MemAdmin(
            admin_id=admin_id,
            admin_pwd=admin_pwd,
            admin_name=admin_name,
            admin_tel_no=admin_tel_no,
            admin_email=admin_email,
            admin_biz_area=admin_biz_area,
            biz_level=biz_level,
            reg_date=timezone.now(),
            manage_YN=manage_YN,
            grade=grade,
            htx_id=htx_id,
            user_id=user.id
        )
        new_admin.save()  # 데이터베이스에 저장

        # 프로필 이미지 처리
        if 'avatar_image' in request.FILES:
            avatar_file = request.FILES['avatar_image']
            # static/assets/images/faces/ 경로에 저장
            faces_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'images', 'faces')

            # 디렉토리가 없으면 생성
            if not os.path.exists(faces_path):
                os.makedirs(faces_path)

            # 파일 확장자 추출
            file_extension = os.path.splitext(avatar_file.name)[1]
            # admin_name으로 파일명 설정
            filename = f"{admin_name}.png"
            file_path = os.path.join(faces_path, filename)

            # 파일 저장
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)

        return redirect('staffList')  # 성공적으로 저장된 후 리디렉션
      except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
  else:
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@csrf_exempt
def admin_update(request):
  if request.method == 'POST':
      admin_id = request.POST.get('admin_id')
      print(admin_id)

      if admin_id:
        try:
          admin = get_object_or_404(MemAdmin, admin_id=admin_id)

          # Update the fields with new data
          admin.admin_name = request.POST.get('admin_name', admin.admin_name)
          admin.admin_pwd = request.POST.get('admin_pwd')
          print("admin.admin_pwd :"+str(admin.admin_pwd ))
          admin.admin_tel_no = request.POST.get('admin_tel_no')
          admin.admin_email = request.POST.get('admin_email')
          admin.admin_biz_area = request.POST.get('admin_biz_area')
          admin.biz_level = request.POST.get('biz_level')
          print("admin.biz_level :"+str(admin.biz_level ))
          admin.grade = request.POST.get('grade')
          print("admin.grade :"+str(admin.grade ))
          admin.manage_YN = request.POST.get('manage_YN')
          print("admin.manage_YN :"+str(admin.manage_YN ))
          admin.reg_date = request.POST.get('reg_date')
          admin.htx_id = request.POST.get('htx_id')

          # auth_user 모델의 비밀번호를 업데이트
          if admin.user_id and admin.admin_pwd:  # user_id가 연결된 경우에만 처리
            user = get_object_or_404(User, pk=admin.user_id)
            if user:
              new_password = request.POST.get('admin_pwd')
              if new_password:
                user.set_password(new_password)  # 비밀번호 해시화
                user.save()
                print('auth_user 저장됨')

          # Save changes to the database
          admin.save()

          # 프로필 이미지 처리
          if 'avatar_image' in request.FILES:
            avatar_file = request.FILES['avatar_image']
            # static/assets/images/faces/ 경로에 저장
            faces_path = os.path.join(settings.BASE_DIR, 'static', 'assets', 'images', 'faces')

            # 디렉토리가 없으면 생성
            if not os.path.exists(faces_path):
              os.makedirs(faces_path)

            # admin_name으로 파일명 설정
            filename = f"{admin.admin_name}.png"
            file_path = os.path.join(faces_path, filename)

            # 파일 저장
            with open(file_path, 'wb+') as destination:
              for chunk in avatar_file.chunks():
                destination.write(chunk)

          # AJAX 요청인 경우 JSON 반환
          if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
              'success': True,
              'message': '업데이트되었습니다.',
              'data': {
                'admin_id': admin.admin_id,
                'admin_name': admin.admin_name,
                'admin_tel_no': admin.admin_tel_no or '',
                'admin_email': admin.admin_email or '',
                'admin_biz_area': admin.admin_biz_area or '',
                'biz_level': admin.biz_level or '',
                'grade': admin.grade or '',
                'manage_YN': admin.manage_YN or '',
                'htx_id': admin.htx_id or '',
              }
            })

          return redirect('staffList')
        except Exception as e:
          if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
          return redirect('staffList')

  return redirect('staffList')

@csrf_exempt
def getAdminInfo(request):
  if request.method == 'POST':
    admin_id = request.POST.get('admin_id')
    print(admin_id)

    if admin_id:
      admin = get_object_or_404(MemAdmin, admin_id=admin_id)
      data = {
        'success': True,
        'admin_pwd' : admin.admin_pwd,
        'admin_name' : admin.admin_name,
        'admin_tel_no' : admin.admin_tel_no or '',
        'admin_email' : admin.admin_email or '',
        'admin_biz_area' : admin.admin_biz_area or '',
        'biz_level' : admin.biz_level or '',
        'reg_date' : admin.reg_date.strftime('%Y-%m-%d') if admin.reg_date else '',
        'manage_YN' : admin.manage_YN or '',
        'grade' : admin.grade or '',
        'htx_id' : admin.htx_id or '',
        'user_id' : admin.user_id
      }
      return JsonResponse(data)
    else:
      return JsonResponse({'success': False, 'error': 'Admin ID not provided'})
  else:
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def delete_admin(request, seq_no):
  if request.method == 'POST': 
      item = get_object_or_404(MemAdmin, pk=seq_no)
      # 연결된 auth_user 인스턴스를 먼저 삭제
      if item.user_id:  # user_id가 연결된 경우에만 삭제
          user = get_object_or_404(User, pk=item.user_id)
          user.delete()

      item.delete()
      # Redirect to a success page or the list view
      return redirect('staffList')
  else:
      # Redirect to a safe page if the request is not POST
      return redirect('dsboard')