import json
import datetime
import copy
import math
import os
import natsort
import traceback
# from datetime import datetime
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
from app.models import userProfile

from app.models import TblMngJaroe
from app.models import TblHometaxScrap
from app.models import TblHometaxSalecard
from django.db import models,transaction

from django.db.models import Q

from admins.utils import send_kakao_notification,kijang_member_popup,tbl_mng_jaroe_update,getSentMails,sendMail,mid_union


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
    work_MM = request.session.get('workmonth')
    if not work_MM:
      work_MM = today.month
  corpYear = today.year
  if int(work_MM) <= 4 :
    corpYear = today.year-1
  if not work_YY:
    work_YY = request.session.get('workyearCorp')
    if not work_YY:
      if int(work_MM) <= 4 :
        work_YY = today.year - 1
      else:
        work_YY = today.year
    else:
      work_YY = int(work_YY)
  request.session['workyearCorp'] = work_YY
  request.session['workmonth'] = work_MM
  
  corpYears = list(range(corpYear, corpYear - 6, -1))
  # print(corpYears)
  context['corpYears'] = corpYears
  context['admin_grade'] = admin_grade
  context['admin_biz_level'] = admin_biz_level
  context['arr_ADID'] = json.dumps(list(arr_ADID))
  context['flag'] = flag
  context['ADID'] = ADID
  request.session['ADID'] = ADID  

  request.session.save()

  templateMenu = gridTitle=""
  if flag == "bank":
    templateMenu = 'admin/mng_corp_bank.html'; gridTitle="법인통장 관리"
  elif flag == "deduct":
    templateMenu = 'admin/mng_corp_deduct.html'; gridTitle="법인세 : 감면 공제 체크"
  elif flag == "helper":
    templateMenu = 'admin/mng_corp_helper.html'; gridTitle="법인세 : 신고서 작성도우미"
  elif flag == "jungki":
    templateMenu = 'admin/mng_corp_jungki.html'; gridTitle="법인세 : 정기신고"    
  elif flag == "jungkan":
    templateMenu = 'admin/mng_corp_jungkan.html'; gridTitle="법인세 : 중간예납"        
  elif flag == "report":
    templateMenu = 'admin/mng_corp_report.html'; gridTitle="법인 기장보고서·가결산"            
  context['gridTitle'] = gridTitle  
  return render(request, templateMenu,context)

def mng_corp_report(request):
  #관리업체 전체 연간 매출액 / 순이익 / 세액감면 / 세액공제 / 업체별 특이사항 / 이월관리사항 / 주식변동 / 잉여금현황
  return

#법인세 정기신고 대상자 리스트
def mng_corp_jungki(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')#전체 선택시 ADID=""상태가 된다
  request.session['ADID'] = ADID  
  
  work_YY = request.GET.get('work_YY', '')

  request.session['workyearCorp'] = work_YY
  request.session.save()

  if request.method == 'GET':
    s_sql = ""
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"

    sql_query = f"""
      select  
        b.biz_manager as groupManager,a.seq_no ,a.biz_name	
        ,SUM(isnull( CASE WHEN S.acnt_cd>=401 and S.acnt_cd<=430 and S.remk <> '손익계정에 대체' THEN S.tranamt_dr-S.tranamt_cr ELSE  0 END , 0)) as revenue  
        ,SUM(isnull( CASE WHEN S.acnt_cd =400 and S.remk='비용에서 대체' THEN tranamt_cr ELSE  0 END , 0)) as expense 
        ,SUM(isnull( CASE WHEN S.acnt_cd =400 and S.remk IN ('당기순손익 잉여금에 대체', '당기순손익 결손금에 대체') THEN S.tranamt_cr-S.tranamt_dr ELSE  0 END , 0)) as income  
        ,max(isnull(MID.법인세,0)) as YN_4
        ,max(isnull(eq.총부담세액_합계,0)) as YN_5
        ,max(isnull(yn_6,0)) as YN_6
        ,max(isnull(yn_7,0)) as YN_7
        ,isnull((select top 1 mail_subject from tbl_mail M where M.seq_no=a.seq_no and year(mail_date)='{int(work_YY)+1}' and mail_class='corp' order by len(mail_subject)/1 desc),'') as MailGrade
        ,max(isnull(YN_8,0)) as YN_8
        ,max(isnull(yn_9,0)) as YN_9
        ,MAX(ISNULL(e.과세년월, '')) isIssue 
        ,max(isnull(사용자ID,'')) as JupsuID 
        ,max(isnull(yn_10,'')) as YN_10
        ,max(isnull(yn_11,0)) as YN_11
        ,max(isnull(yn_12,'')) as YN_12
        ,max(isnull(yn_13,0)) as YN_13
        ,max(isnull(yn_14,0)) as YN_14
        ,max(isnull(yn_15,0)) as YN_15
      FROM Mem_User    A    WITH (NOLOCK)  
          INNER JOIN  mem_deal       B WITH (NOLOCK) on a.seq_no = b.seq_no  
          INNER JOIN  ds_FiscalMM_V    F WITH (NOLOCK) on a.seq_no = f.seq_no  
          LEFT OUTER JOIN  ds_slipledgr2  S WITH (NOLOCK) on a.seq_no = s.seq_no  AND ( ( S.work_yy =  '{work_YY}'  AND S.Tran_Dt < F.시작일 ) OR (S.work_yy =  '{work_YY}' + F.기준년 AND S.Tran_Dt >= F.시작일 ) ) 
          LEFT OUTER JOIN  법인세전자신고2  E WITH (NOLOCK) on a.biz_no = e.사업자번호  and 신고구분='정기(확정)' and left(rtrim(e.과세년월),4) =  '{work_YY}'   
          LEFT OUTER JOIN tbl_corporate2 corp WITH (NOLOCK) ON a.seq_no = corp.seq_no  AND corp.work_yy = '{work_YY}'
          LEFT OUTER JOIN tbl_equityeval eq WITH (NOLOCK) ON a.biz_no = eq.사업자번호  AND LEFT(eq.사업연도말, 4) = '{work_YY}'
          LEFT OUTER JOIN tbl_EquityEval_MID MID WITH (NOLOCK) ON a.biz_no = MID.사업자번호  AND LEFT(MID.사업연도말, 4) = '{work_YY}'
      where   a.duzon_ID <> '' and  a.biz_type in ('1','2') and  b.keeping_YN='Y' and a.Del_YN<>'Y' {s_sql}
      GROUP BY b.biz_manager,a.seq_no ,a.biz_name
      order BY b.biz_manager ,a.biz_name    
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

#법인세 중간신고 대상자 리스트
def mng_corp_jungkan(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')#전체 선택시 ADID=""상태가 된다
  request.session['ADID'] = ADID  
  
  work_YY = request.GET.get('work_YY', '')

  request.session['workyearCorp'] = work_YY
  request.session.save()

  if request.method == 'GET':
    s_sql = ""
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"

    sql_query = f"""
    WITH slip_data AS (
        SELECT 
            s.seq_no,
            s.work_yy,
            s.Tran_Dt,
            s.acnt_cd,
            s.remk,
            s.tranamt_cr,
            s.tranamt_dr,
            f.시작일,
            f.기준년
        FROM ds_slipledgr2 s
        INNER JOIN ds_FiscalMM_V f ON s.seq_no = f.seq_no
        WHERE s.work_yy IN ('{int(work_YY)-1}', '{work_YY}')
    ),
    calc_data AS (
        SELECT
            a.seq_no AS sqno,
            MAX(b.biz_manager) AS groupManager,
            MAX(a.biz_name) AS biz_name,
            MAX(ISNULL(e.과세년월, '')) AS isIssue,
            MAX(b.createdDate) AS createdDate,
            SUM(CASE 
                WHEN sd.work_yy = '{work_YY}' AND sd.acnt_cd BETWEEN 401 AND 430 AND sd.remk <> '손익계정에 대체' THEN sd.tranamt_dr - sd.tranamt_cr
                ELSE 0
            END) AS revenue,
            SUM(CASE 
                WHEN sd.work_yy = '{work_YY}'  AND sd.acnt_cd = 400 AND sd.remk = '비용에서 대체' THEN sd.tranamt_cr
                ELSE 0
            END) AS expense,
            SUM(CASE 
                WHEN sd.work_yy = '{work_YY}'  AND sd.acnt_cd = 400 AND sd.remk IN ('당기순손익 잉여금에 대체', '당기순손익 결손금에 대체') THEN sd.tranamt_cr - sd.tranamt_dr
                ELSE 0
            END) AS income,
            SUM(CASE 
                WHEN sd.work_yy = '{int(work_YY)-1}' AND sd.acnt_cd BETWEEN 401 AND 430 AND sd.remk <> '손익계정에 대체' THEN sd.tranamt_dr - sd.tranamt_cr
                ELSE 0
            END) AS revenue_pre,
            SUM(CASE 
                WHEN sd.work_yy = '{int(work_YY)-1}' AND sd.acnt_cd = 400 AND sd.remk IN ('당기순손익 잉여금에 대체', '당기순손익 결손금에 대체') THEN sd.tranamt_cr - sd.tranamt_dr
                ELSE 0
            END) AS income_pre
        FROM Mem_User a
        INNER JOIN mem_deal b ON a.seq_no = b.seq_no
        LEFT JOIN slip_data sd ON a.seq_no = sd.seq_no
        LEFT JOIN 법인세전자신고_MID e 
            ON a.biz_no = e.사업자번호 
            AND e.신고구분 = '예정(중간예납)' 
            AND LEFT(RTRIM(e.과세년월), 4) = '{work_YY}'
        WHERE a.duzon_ID <> ''
          AND a.biz_type IN ('1','2')
          AND b.keeping_YN = 'Y'
          AND a.Del_YN <> 'Y'
          {s_sql}
        GROUP BY a.seq_no
    )

    SELECT
        cd.groupManager, cd.sqno, cd.biz_name, cd.isIssue, cd.createdDate,
        cd.revenue, cd.expense, cd.income, cd.revenue_pre, cd.income_pre,
        ISNULL(eq.중간예납신고방법, 0) AS submitWay,
        ISNULL(eq.법인세, 0) AS midTax,
        ISNULL(eq.안내메일, 0) AS mail_Guide,
        ISNULL(eq.납부서메일, 0) AS mail_Issue,
        ISNULL(eq.총부담세액_합계, 0) AS confirmTax,
        ISNULL(c2.총부담세액_합계, 0) AS preYearCorpTax
    FROM calc_data cd
    LEFT JOIN mem_user a ON cd.sqno = a.seq_no
    LEFT JOIN mem_deal d ON a.seq_no = d.seq_no
    LEFT JOIN tbl_equityeval_MID eq ON a.biz_no = eq.사업자번호 AND LEFT(eq.사업연도말, 4) = '{work_YY}'
    LEFT JOIN tbl_equityeval c2 ON a.biz_no = c2.사업자번호 AND left(c2.사업연도말,4) = {int(work_YY)-1}
    ORDER BY cd.groupManager, cd.biz_name

    """
    #print(sql_query)
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        columns = [col[0] for col in cursor.description]  # 컬럼명 가져오기
        results = cursor.fetchall()
        # 파일 경로 확인
        root_disk = "D:/세무자료"  # 실제 경로로 수정
        results_with_file_info = []
        for row in results:
            row_data = dict(zip(columns, row))
            groupManager = row_data["groupManager"]
            biz_name = row_data["biz_name"]
            seq_no = row_data["sqno"]
            isIssue = row_data["isIssue"].strip()
            revenue = row_data["revenue"]
            expense = row_data["expense"]
            income = row_data["income"]
            revenue_pre = row_data["revenue_pre"]
            income_pre = row_data["income_pre"]
            submitWay = row_data["submitWay"]
            pre_tax_raw = row_data.get("preYearCorpTax", 0)  #전년도 총부담세액
            preYearCorpTax = int(float(pre_tax_raw)) if pre_tax_raw not in (None, "", "null") else 0
            midTax_raw = row_data.get("midTax", 0)
            midTax = int(float(midTax_raw)) if midTax_raw not in (None, "", "null") else 0       
            mail_Guide =  row_data["mail_Guide"]
            mail_Issue =  row_data["mail_Issue"]
            created_year = row_data["createdDate"].year if isinstance(row_data["createdDate"], datetime.date) else str(row_data["createdDate"])[:4]

            suggestWay = ""
            txt_submitWay = ""
            inspectIssue = ""
            preTax = 0
            N10 = 0

            # createdDate가 inputWorkyear와 같은 경우 무신고 처리
            if created_year == work_YY:
                suggestWay = "무신고"
                preTax = 0
            else:
                if preYearCorpTax > 1000000:
                    # up_Act_PLInquiry 프로시저 실행
                    strsql_1 = f"EXEC up_Act_PLInquiry '{work_YY}', '{seq_no}'"
                    cursor3 = connection.cursor()
                    cursor3.execute(strsql_1)
                    rows3 = cursor3.fetchall()

                    # 계정코드별 값 추출
                    for row3 in rows3:
                        acnt_cd = row3[0].strip()  # 계정코드가 첫 번째 컬럼이라면
                        rightAmt = float(row3[2])  # 당기잔액1이 두 번째 컬럼이라면
                        if acnt_cd == "N10":
                            N10 = rightAmt
                            income = N10

                    # 법인세차감전이익 계산
                    if N10 > 200_000_000:
                        preTax = N10 * 0.2 - 20_000_000
                    else:
                        preTax = N10 * 0.1

                    # preYearCorpTax를 기준으로 유리한 신고방법 결정
                    if preYearCorpTax == 0 or revenue == 0:
                        suggestWay = "<b>직전년도"
                        preTax = float(preYearCorpTax) / 2
                    elif preTax < preYearCorpTax / 2:
                        suggestWay = "<b>자기계산 유리"
                        mail_Guide = "2"
                        preTax = max(preTax, 0)  # 0 미만은 0 처리
                    else:
                        suggestWay = "<b>직전년도 유리"
                        preTax = preYearCorpTax / 2

                    # 중간예납신고방법 코드 해석
                    if submitWay == "1":
                        txt_submitWay = "직전년도"
                    elif submitWay == "2":
                        txt_submitWay = "자기계산"
                else:
                    suggestWay = "신고안함(개정)"
            if preTax>500000:
              mail_Guide = "2"
            if preTax<500000 and preYearCorpTax / 2 <500000:
              suggestWay = "납부면제"
              mail_Guide = ""
              mail_Issue = ""
            filecount = 0
            srcpath = os.path.join('static/cert_DS/', str(row_data.get("biz_name")), str(work_YY), "세무조정계산서")
            if os.path.exists(srcpath):
                try:
                    for fname in os.listdir(srcpath):
                        if fname in ("204.pdf", "205.pdf"):
                            filecount += 1
                except PermissionError:
                    print(f"[권한 오류] {srcpath} 디렉토리를 읽을 수 없습니다.")
            else:
                print(f"[없음] 경로 없음: {srcpath}")

            mail_Issue = "2" if filecount > 0 else ""
            if isIssue != "" and preTax<midTax:
                inspectIssue = "1"
            results_with_file_info.append({
              "groupManager":groupManager,
              "seq_no": seq_no,
              "biz_name": biz_name,
              "revenue": revenue,
              "expense":expense,
              "income":income,
              "preTax":preTax,
              "midTax":midTax,
              "revenue_pre": revenue_pre,
              "income_pre":income_pre,   
              "preYearCorpTax":preYearCorpTax,           
              "suggestWay": suggestWay,
              "submitWay":txt_submitWay,
              "mail_Guide":mail_Guide,
              "mail_Issue":mail_Issue,
              "isIssue": isIssue,
              "inspectIssue":inspectIssue
            })
    return JsonResponse(list(results_with_file_info), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

#법인세 신고서 리스트
@csrf_exempt
def path_to_corp_admin(request):
    data = json.loads(request.body)
    base_path = data.get("path", "")
    seq_no = data.get("seq_no", "")

    memuser = MemUser.objects.get(seq_no=seq_no)
    memdeal = MemDeal.objects.get(seq_no=seq_no)

    fiscalMM = memdeal.fiscalmm
    isCorp = memuser.biz_type < 4

    paths_to_check = []
    modified_path = base_path + "(수정)"
    if os.path.isdir(modified_path):
        paths_to_check.append((modified_path, "세무조정계산서(수정)", True))
    if os.path.isdir(base_path):
        paths_to_check.append((base_path, os.path.basename(base_path), False))

    totTitleArr = []
    totfileArr = []
    cnt = 0

    for current_path, override_title, single_group in paths_to_check:
        tmpAfter = ""
        for x in natsort.natsorted(os.listdir(current_path)):
            x = ''.join(c for c in x if c.isprintable())        

            tmpPureFile = os.path.splitext(x)[0]
            pureOrder = tmpPureFile.split("-")[0]
            etcFileName = ""

            if "-" in tmpPureFile:
                etcFileName = tmpPureFile.split("-")[1]

            tmpExt = os.path.splitext(x)[1].lower()

            if pureOrder.isnumeric() and tmpExt in [".pdf", ".jpg", ".png", ".jpeg"]:
                dueDate = ""

                if isCorp:
                    if fiscalMM == "12":
                        if tmpPureFile == "200": dueDate = " 3월 31일"
                        if tmpPureFile == "201": dueDate = " 4월 30일"
                        if tmpPureFile == "202": dueDate = " 5월 31일"
                        if tmpPureFile == "203": dueDate = " 6월 30일"
                        if tmpPureFile == "204": dueDate = " 8월 31일"
                        if tmpPureFile == "205": dueDate = " 10월 31일"
                    else:
                        dueDate = str(int(fiscalMM) + 3) + "월 30일"
                        if fiscalMM == "3":
                            if tmpPureFile == "200": dueDate = " 6월 30일"
                            if tmpPureFile == "201": dueDate = " 7월 31일"
                            if tmpPureFile == "202": dueDate = " 8월 31일"
                            if tmpPureFile == "203": dueDate = " 9월 30일"
                            if tmpPureFile == "204": dueDate = " 11월 30일"
                            if tmpPureFile == "205": dueDate = " 1월 31일"
                        elif fiscalMM == "6":
                            if tmpPureFile == "200": dueDate = " 9월 30일"
                            if tmpPureFile == "201": dueDate = " 4월 30일"
                            if tmpPureFile == "202": dueDate = " 5월 31일"
                            if tmpPureFile == "203": dueDate = " 6월 30일"
                            if tmpPureFile == "204": dueDate = " 2월 28일"
                            if tmpPureFile == "205": dueDate = " 4월 30일"
                else:
                    if tmpPureFile == "200": dueDate = " 5월 31일"
                    if tmpPureFile == "201": dueDate = " 5월 31일"
                    if tmpPureFile == "202": dueDate = " 7월 31일"
                    if tmpPureFile == "204": dueDate = " 11월 30일"

                order = int(pureOrder)
                if single_group:
                    tmpTitle = override_title
                else:
                    if order < 100: tmpTitle = "법인세신고서" if isCorp else "종합소득세신고서"
                    elif order < 127: tmpTitle = "결산보고서"
                    elif order < 198: tmpTitle = "기타부속서류"
                    elif order < 300: tmpTitle = "접수증 및 납부서"
                    elif order == 300: tmpTitle = "전체서식"
                    elif order == 400: tmpTitle = "종합소득세 신고안내문"
                    else: tmpTitle = "기타부속서류"

                if tmpAfter != tmpTitle:
                    titles = {'displayName': tmpTitle}
                    totTitleArr.append(titles)

                tmpAfter = tmpTitle

                tmpSheet = "_corp" if isCorp else "_income"
                arrFiles = getTblSheet(tmpSheet)
                tmpFileName = ""
                for f in arrFiles:
                    if f['fileName'] == tmpPureFile:
                        tmpFileName = f['sheetName']
                    elif etcFileName and (127 <= order < 198 or order > 400):
                        tmpFileName = etcFileName

                files = {
                    'group': tmpTitle,
                    '파일명': tmpFileName,
                    'id': str(cnt),
                    'totalPath':current_path+"/"+x,# os.path.join(current_path, x),
                    'dueDate': dueDate
                }
                totfileArr.append(files)
                cnt += 1

    d = {
        'text': os.path.basename(base_path),
        'titles': totTitleArr,
        'nodes': totfileArr
    }

    return JsonResponse(d, safe=False)

def getTblSheet(flag):
  if flag=="_corp": flag=""
  strsql = "SELECT seq,trim(fileName),trim(sheetName) from Tbl_Sheet"+flag+" order by seq/1"
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

# 신고서 작성도우미 쿼리
def mng_corp_helper(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')
  request.session['ADID'] = ADID  
  

  work_YY = request.GET.get('work_YY', '')
  request.session['workyearCorp'] = work_YY
  request.session.save()

  if request.method == 'GET':
    s_sql = f" AND b.biz_manager = '{ADID}' "
    if ADID=="전체": s_sql = ""
    sql_query = f"""
      DECLARE @CurrentYear INT = YEAR(GETDATE());
      WITH BaseData AS (
          SELECT 
              c.admin_id,
              a.seq_no,
              a.biz_name,
              a.biz_no,
              CASE 
                  WHEN LEFT(ssn, 2) BETWEEN '00' AND '24' THEN @CurrentYear - (2000 + CAST(LEFT(ssn, 2) AS INT))
                  ELSE @CurrentYear - (1900 + CAST(LEFT(ssn, 2) AS INT))
              END AS 나이,
              (a.uptae + a.jongmok) AS 업종,
              (a.biz_addr1 + a.biz_addr2) AS 지역,
              (@CurrentYear - YEAR(a.reg_date)) AS 기수,
              a.reg_date AS 등록일,
              a.isRND AS 연구개발여부,
              a.isVenture AS 벤처여부,
              a.biz_no AS 사업자번호
          FROM mem_user a WITH (NOLOCK)
          INNER JOIN mem_deal b WITH (NOLOCK) ON a.seq_no = b.seq_no
          INNER JOIN mem_admin c WITH (NOLOCK) ON b.biz_manager = c.admin_id
          WHERE keeping_yn = 'Y'
              AND kijang_yn = 'Y'
              AND ISNULL(taltyoedate, '') = ''
              AND biz_type < 4
              AND fiscalMM = 12
              AND YEAR(a.reg_date) <= {work_YY}
              {s_sql}
      ),
      Sales AS (
        SELECT seq_no, SUM(tranamt_dr) AS 매출액 FROM ds_slipledgr2 WITH (NOLOCK)  WHERE work_yy = '{work_YY}' AND acnt_cd BETWEEN 401 AND 430  GROUP BY seq_no ),
      NetProfit AS (
        SELECT seq_no, SUM(tranamt_dr - tranamt_cr) AS 순손익  FROM ds_slipledgr2 WITH (NOLOCK)  WHERE work_yy = '{work_YY}' AND acnt_cd > 400 AND Remk <> '손익계정에 대체'  GROUP BY seq_no ),
      TaxExpenses AS (
        SELECT seq_no, SUM(tranamt_cr) AS 세금비용  FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd IN (517, 617, 717, 817)  GROUP BY seq_no ),
      Penalties AS (
        SELECT seq_no, SUM(tranamt_cr) AS 벌금   FROM ds_slipledgr2 WITH (NOLOCK)  WHERE work_yy = '{work_YY}' AND (remk LIKE '%가산세%' OR remk LIKE '%벌금%' OR remk LIKE '%과태%') GROUP BY seq_no  ),
      AA AS ( SELECT seq_no, SUM(tranamt_cr) AS 접대비   FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd IN (513, 613, 713, 813)   GROUP BY seq_no ),
      BB AS (  SELECT seq_no, SUM(tranamt_cr) AS 기부금 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =953   GROUP BY seq_no),
      CC AS (  SELECT seq_no, SUM(tranamt_cr) AS 대손금 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =853   GROUP BY seq_no),
      DD AS (  SELECT seq_no, SUM(tranamt_cr) AS 이자비용 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =951   GROUP BY seq_no),
      EE AS (  SELECT seq_no, SUM(tranamt_dr) AS 차입금 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd in (260,293)  GROUP BY seq_no),
      FF AS (  SELECT seq_no, SUM(tranamt_cr) AS 가지급 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =134   GROUP BY seq_no),
      GG AS (  SELECT seq_no, SUM(tranamt_cr) AS 선납세금 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =116   GROUP BY seq_no),
      HH AS (  SELECT seq_no, SUM(tranamt_dr) AS 가수금 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =257   GROUP BY seq_no),
      II AS (  SELECT seq_no, SUM(tranamt_cr) AS 미수수익 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =136   GROUP BY seq_no),
      JJ AS (  SELECT seq_no, SUM(tranamt_cr) AS 고정자산 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' and acnt_cd>=195 and acnt_cd<=230   GROUP BY seq_no),
      KK AS (  SELECT seq_no, SUM(tranamt_cr) AS 감가상각 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =818   GROUP BY seq_no),
      LL AS (  SELECT seq_no, SUM(tranamt_cr) AS 차량 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =208   GROUP BY seq_no),
      MM AS (  SELECT seq_no, SUM(tranamt_cr-tranamt_dr) AS 재고자산 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd >=146 and acnt_cd<=175 GROUP BY seq_no),
      NN AS (  SELECT seq_no, SUM(tranamt_cr) AS 토지 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =201   GROUP BY seq_no),
      OO AS (  select seq_no, isnull(sum(a60),0) as 중간배당 from mem_user a,원천세전자신고 b where a.biz_no=b.사업자등록번호 and left(과세연월,4)='{work_YY}' and a60>0 group by a.seq_no),
      PP AS (  SELECT seq_no, max(Tran_Dt) AS 최종분개 FROM ds_slipledgr2 WHERE work_yy = '{work_YY}'    GROUP BY seq_no),
      QQ AS (  select seq_no, sum(tranamt_Cr+tranamt_Dr) as 결산분개 from ds_slipledgr2 WITH (NOLOCK) where  work_yy='{work_YY}' and Tran_dt='12-31' and acnt_cd='400'  GROUP BY seq_no ),
      RR AS (  select  M.seq_no,sum(StckH_FEquityGP) as 주식변동 from Tbl_StckHListTrn T,mem_user M where M.seq_no=T.seq_no and year(tran_dt)='{work_YY}' and year(M.reg_date)<2022 group by M.seq_no),
      SS AS (  SELECT seq_no, SUM(tranamt_dr) AS 이자수익 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =901   GROUP BY seq_no),
      TT AS (  SELECT seq_no, SUM(tranamt_dr) AS 배당금수익 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =903   GROUP BY seq_no),
      UU AS (  SELECT seq_no, SUM(tranamt_dr) AS 외화환산이익 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =910   GROUP BY seq_no),
      VV AS (  SELECT seq_no, SUM(tranamt_cr) AS 외화환산손실 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =955   GROUP BY seq_no),
      WW AS (  SELECT seq_no, SUM(tranamt_cr) AS 법인세비용 FROM ds_slipledgr2 WITH (NOLOCK) WHERE work_yy = '{work_YY}' AND acnt_cd =998   GROUP BY seq_no),
      XX AS (  select 사업자번호,isnull(trim(결손금누계),0) as 이월결손금 from tbl_EquityEval where  left(사업연도말,4)='{int(work_YY)-1}')
      SELECT 
          T.admin_id AS admin_id,T.seq_no AS seq_no,T.biz_name AS biz_name,T.biz_no,
          T.나이,T.등록일,T.업종,T.지역, T.기수, T.연구개발여부, T.벤처여부,
          isnull(S.매출액,0) AS 매출,
          isnull(N.순손익,0) 순손익, isnull(TX.세금비용,0) T817, isnull(P.벌금,0) S817,
          isnull(AA.접대비,0) 접대비,isnull(BB.기부금,0) 기부금,isnull(CC.대손금,0) 대손금,
          isnull(DD.이자비용,0) 이자비용,isnull(EE.차입금,0) 차입금,isnull(FF.가지급,0) 가지급,
          isnull(GG.선납세금,0) 선납세금,isnull(HH.가수금,0) 가수금,isnull(II.미수수익,0) 미수수익,
          isnull(JJ.고정자산,0) 고정자산,isnull(KK.감가상각,0) 감가상각,isnull(LL.차량,0) 차량,
          isnull(MM.재고자산,0) 재고자산,isnull(NN.토지,0) 토지,isnull(OO.중간배당,0) 중간배당,PP.최종분개,QQ.결산분개,RR.주식변동,
          isnull(SS.이자수익,0) 이자수익,isnull(TT.배당금수익,0) 배당금수익,isnull(UU.외화환산이익,0) 외화환산이익,
          isnull(VV.외화환산손실,0) 외화환산손실,isnull(WW.법인세비용,0) 법인세비용,isnull(XX.이월결손금,0) 이월결손금
      FROM BaseData T
      LEFT JOIN Sales S         ON T.seq_no = S.seq_no
      LEFT JOIN NetProfit N     ON T.seq_no = N.seq_no
      LEFT JOIN TaxExpenses TX  ON T.seq_no = TX.seq_no
      LEFT JOIN Penalties P     ON T.seq_no = P.seq_no
      LEFT JOIN AA              ON T.seq_no = AA.seq_no
      LEFT JOIN BB              ON T.seq_no = BB.seq_no
      LEFT JOIN CC              ON T.seq_no = CC.seq_no
      LEFT JOIN DD              ON T.seq_no = DD.seq_no
      LEFT JOIN EE              ON T.seq_no = EE.seq_no
      LEFT JOIN FF              ON T.seq_no = FF.seq_no
      LEFT JOIN GG              ON T.seq_no = GG.seq_no
      LEFT JOIN HH              ON T.seq_no = HH.seq_no
      LEFT JOIN II              ON T.seq_no = II.seq_no
      LEFT JOIN JJ              ON T.seq_no = JJ.seq_no
      LEFT JOIN KK              ON T.seq_no = KK.seq_no
      LEFT JOIN LL              ON T.seq_no = LL.seq_no
      LEFT JOIN MM              ON T.seq_no = MM.seq_no
      LEFT JOIN NN              ON T.seq_no = NN.seq_no
      LEFT JOIN OO              ON T.seq_no = OO.seq_no
      LEFT JOIN PP              ON T.seq_no = PP.seq_no
      LEFT JOIN QQ              ON T.seq_no = QQ.seq_no
      LEFT JOIN RR              ON T.seq_no = RR.seq_no
      LEFT JOIN SS              ON T.seq_no = SS.seq_no
      LEFT JOIN TT              ON T.seq_no = TT.seq_no
      LEFT JOIN UU              ON T.seq_no = UU.seq_no
      LEFT JOIN VV              ON T.seq_no = VV.seq_no
      LEFT JOIN WW              ON T.seq_no = WW.seq_no
      LEFT JOIN XX              ON T.biz_no = XX.사업자번호
      ORDER BY T.admin_id, T.biz_name;
    """
    #print(sql_query)
    recordset = process_helper(work_YY,sql_query)
    # print(recordset)
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

# 신고서 작성도우미 연산
def process_helper(work_YY,sql_query):
    # DB 연결 및 쿼리 실행
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        rows = dict_fetchall(cursor)

    # 각 레코드별 처리
    rec = []
    for idx, row in enumerate(rows):
        # 기본 변수 초기화
        reg_date = str(row.get("등록일"))[:10]
        saleAmt = float(row.get("매출", 0))
        isRND = row.get("연구개발여부")
        isVenture = row.get("벤처여부")
        isYoung = 0
        kisu = None
        deductRate = 0
        region = row.get("지역")
        upJong = row.get("업종")
        kisu = row.get("기수") 
        age = row.get("나이") 

        if kisu is not None and float(kisu) < 6:
            kisu = float(kisu)
        if age is not None and float(age) < 36:
            isYoung = float(age)

        # 수도권과밀억제권역 판단 Y 또는 ""
        isKWAMIL = func_isKWAMIL(region)
        # 수도권(도시) 여부: 해당 단어가 없으면 지방(Y)
        isRural_count = sum(1 for r in ["서울", "인천", "경기"] if r in region)
        isRural = "Y" if isRural_count <= 0 else ""
        # 특별세액감면 검토 (업종)
        isSpecialUpjong = func_isSpecialDeductUpjong(upJong)
        # 소기업/중기업 판별
        isSmall = func_isSmall(upJong,saleAmt)
        # 지식기반사업 여부
        isKnowledge = func_isKnowledge(upJong)
        # 창업 관련 변수
        isChangUpUpjong = func_isChangUp(upJong)
        # 물류산업여부/성정산업
        isMyulyu = func_isMyulyu(upJong)
        isNewGroth = func_isNewGroth(upJong)      
        # 물류산업여부/신성장산업 인 경우 특별감면과 창업감면 대상이다
        if isMyulyu=="Y" or isNewGroth=="Y":
          isSpecialUpjong = "Y"
          isChangUpUpjong = "Y"          
        SpecialDeductRate,SpecialDeduct = func_SpecialDeduct(upJong,isSpecialUpjong,isRural,isSmall)
        ChangUpDeductRate,ChangUpDeduct,isLittle = func_ChangupDeduct(work_YY,kisu,isKWAMIL,isChangUpUpjong,isNewGroth,isVenture,saleAmt,reg_date,age)        

        # 재무조건에 따른 감면율 조정
        valDefict = row.get("이월결손금") or 0
        net_income = float(row.get("순손익", 0))
        if (net_income - float(valDefict)) < 0 or net_income < 0:
            SpecialDeductRate =ChangUpDeductRate =  0

        def format_number(n):
            try:
                return f"{float(n):,.0f}"
            except Exception:
                return str(n)

        # PDF 관련 변수 초기화 (모든 pdf 변수들을 미리 빈 문자열로 초기화)
        pdf_vars = { key: "" for key in [
            "pdf0","pdf1","pdf2","pdf3","pdf4","pdf5","pdf6","pdf7","pdf9","pdf12","pdf13",
            "pdf15","pdf16","pdf17","pdf18","pdf21","pdf22","pdf24","pdf25","pdf29","pdf32",
            "pdf33","pdf34","pdf35","pdf36","pdf39","pdf41","pdf42","pdf43","pdf44","pdf48",
            "pdf49","pdf51","pdf54","pdf55","pdf56","pdf57","pdf58","pdf61","pdf63","pdf64",
            "pdf65","pdf66","pdf68","pdf69","pdf70","pdf74","pdf81","pdf82","pdf83","pdf85",
            "pdf90","pdf98","pdf99","pdf100","pdf101","pdf102","pdf103","pdf104","pdf105",
            "pdf106","pdf110","pdf111","pdf112","pdf113","pdf114","pdf115","pdf116","pdf117",
            "pdf118","pdf120","pdf121","pdf122","pdf123","pdf124","pdf125","pdf126","pdf31_4",
            "pdf35_2","pdf42_2","pdf43_2","pdf52_2","pdf54_1","pdf56_1","pdf57_2","pdf58_2",
            "pdf58_3","pdf58_5","pdf58_6","pdf58_7","pdf58_8","pdf63_4","pdf64_5","pdf71_2",
            "pdf71_8","pdf74_1","pdf74_2","pdf75_3","pdf75_4","pdf76_2","pdf76_3","pdf76_4",
            "pdf20_2_1","pdf15_1","pdf20_1","pdf31_1","pdf15_2","pdf16_2","pdf20_2","pdf3_1",
            "pdf3_2","pdf3_3","pdf3_4","pdf20_3","pdf31_3","pdf20_4","pdf6_2","pdf6_11",
            "pdf6_12","pdf8_1","pdf8_2","pdf8_3","pdf8_4","pdf8_5","pdf8_6","pdf8_9","pdf0_1",
            "pdf10_1","pdf10_2","pdf19_1","pdf19_2","pdf23_1","pdf23_2","pdf26_1","pdf26_2",
            "pdf27_1","pdf27_2","pdf40_1","pdf40_2","pdf46_2_1","pdf46_2_2","pdf46_1","pdf46_2",
            "pdf47_1","pdf47_2","pdf50_1","pdf50_2","pdf52_1","pdf52_2","pdf63_16_1","pdf63_16_2",
            "pdf63_16_3","pdf63_16_4","pdf8_A","pdf8_B","pdf91_1","pdf91_10","pdf91_10_8",
            "pdf91_11_3_1","pdf91_11_3_2","pdf91_11_3_3","pdf91_11_4","pdf91_11_5","pdf91_1_2",
            "pdf91_2","pdf91_2_2","pdf91_2_3","pdf91_26","pdf91_3_1","pdf91_31","pdf91_3_1_1",
            "pdf91_3_2","pdf91_35","pdf91_37_2","pdf91_38","pdf91_38_2","pdf91_40_4","pdf91_43",
            "pdf91_45","pdf91_45_2","pdf91_46","pdf91_46_2","pdf91_47","pdf91_49","pdf91_60_2",
            "pdf91_62","pdf91_64_10","pdf91_64_14","pdf91_64_15","pdf91_64_19","pdf91_64_4",
            "pdf91_64_5","pdf91_64_7","pdf91_64_8","pdf91_64_9","pdf91_9","pdf92_43","pdf92_43_2",
            "pdf92_43_5_1","pdf92_43_5_2","pdf198","pdf199"
        ]}
        isSkeleton = False
        strSkeleton = "*******  " + str(row.get("biz_name")) + "  *******<br>"

        # 파일 시스템: srcpath 폴더 내 PDF 파일 읽기
        srcpath = os.path.join('static/cert_DS/', str(row.get("biz_name")), str(work_YY), "세무조정계산서")
        if os.path.exists(srcpath) and os.path.isdir(srcpath):
            for filename in os.listdir(srcpath):
                if filename:
                    if filename == "0.pdf":                        pdf_vars["pdf0"] = "0/"
                    elif filename == "1.pdf":                        pdf_vars["pdf1"] = "1/"
                    elif filename == "2.pdf":                        pdf_vars["pdf2"] = "2/"
                    elif filename == "3.pdf":                        pdf_vars["pdf3"] = "3/"
                    elif filename == "4.pdf":                        pdf_vars["pdf4"] = "4/"
                    elif filename == "5.pdf":                        pdf_vars["pdf5"] = "5/"
                    elif filename == "6.pdf":                        pdf_vars["pdf6"] = "6/"
                    elif filename == "7.pdf":                        pdf_vars["pdf7"] = "7/"
                    elif filename == "9.pdf":                        pdf_vars["pdf9"] = "9/"
                    elif filename == "12.pdf":                        pdf_vars["pdf12"] = "12/"
                    elif filename == "13.pdf":                        pdf_vars["pdf13"] = "13/"
                    elif filename == "15.pdf":                        pdf_vars["pdf15"] = "15/"
                    elif filename == "16.pdf":                        pdf_vars["pdf16"] = "16/"
                    elif filename == "17.pdf":                        pdf_vars["pdf17"] = "17/"
                    elif filename == "18.pdf":                        pdf_vars["pdf18"] = "18/"
                    elif filename == "21.pdf":                        pdf_vars["pdf21"] = "21/"
                    elif filename == "22.pdf":                        pdf_vars["pdf22"] = "22/"
                    elif filename == "24.pdf":                        pdf_vars["pdf24"] = "24/"
                    elif filename == "25.pdf":                        pdf_vars["pdf25"] = "25/"
                    elif filename == "29.pdf":                        pdf_vars["pdf29"] = "29/"
                    elif filename == "32.pdf":                        pdf_vars["pdf32"] = "32/"
                    elif filename == "33.pdf":                        pdf_vars["pdf33"] = "33/"
                    elif filename == "34.pdf":                        pdf_vars["pdf34"] = "34/"
                    elif filename == "35.pdf":                        pdf_vars["pdf35"] = "35/"
                    elif filename == "36.pdf":                        pdf_vars["pdf36"] = "36/"
                    elif filename == "39.pdf":                        pdf_vars["pdf39"] = "39/"
                    elif filename == "41.pdf":                        pdf_vars["pdf41"] = "41/"
                    elif filename == "42.pdf":                        pdf_vars["pdf42"] = "42/"
                    elif filename == "43.pdf":                        pdf_vars["pdf43"] = "43/"
                    elif filename == "44.pdf":                        pdf_vars["pdf44"] = "44/"
                    elif filename == "48.pdf":                        pdf_vars["pdf48"] = "48/"
                    elif filename == "49.pdf":                        pdf_vars["pdf49"] = "49/"
                    elif filename == "51.pdf":                        pdf_vars["pdf51"] = "51/"
                    elif filename == "54.pdf":                        pdf_vars["pdf54"] = "54/"
                    elif filename == "55.pdf":                        pdf_vars["pdf55"] = "55/"
                    elif filename == "56.pdf":                        pdf_vars["pdf56"] = "56/"
                    elif filename == "57.pdf":                        pdf_vars["pdf57"] = "57/"
                    elif filename == "58.pdf":                        pdf_vars["pdf58"] = "58/"
                    elif filename == "61.pdf":                        pdf_vars["pdf61"] = "61/"
                    elif filename == "63.pdf":                        pdf_vars["pdf63"] = "63/"
                    elif filename == "64.pdf":                        pdf_vars["pdf64"] = "64/"
                    elif filename == "65.pdf":                        pdf_vars["pdf65"] = "65/"
                    elif filename == "66.pdf":                        pdf_vars["pdf66"] = "66/"
                    elif filename == "68.pdf":                        pdf_vars["pdf68"] = "68/"
                    elif filename == "69.pdf":                        pdf_vars["pdf69"] = "69/"
                    elif filename == "70.pdf":                        pdf_vars["pdf70"] = "70/"
                    elif filename == "74.pdf":                        pdf_vars["pdf74"] = "74/"
                    elif filename == "81.pdf":                        pdf_vars["pdf81"] = "81/"
                    elif filename == "82.pdf":                        pdf_vars["pdf82"] = "82/"
                    elif filename == "83.pdf":                        pdf_vars["pdf83"] = "83/"
                    elif filename == "85.pdf":                        pdf_vars["pdf85"] = "85/"
                    elif filename == "90.pdf":                        pdf_vars["pdf90"] = "90/"
                    elif filename == "98.pdf":                        pdf_vars["pdf98"] = "98/"
                    elif filename == "99.pdf":                        pdf_vars["pdf99"] = "99/"
                    elif filename == "100.pdf":                        pdf_vars["pdf100"] = "100/"
                    elif filename == "101.pdf":                        pdf_vars["pdf101"] = "101/"
                    elif filename == "102.pdf":                        pdf_vars["pdf102"] = "102/"
                    elif filename == "103.pdf":                        pdf_vars["pdf103"] = "103/"
                    elif filename == "104.pdf":                        pdf_vars["pdf104"] = "104/"
                    elif filename == "105.pdf":                        pdf_vars["pdf105"] = "105/"
                    elif filename == "106.pdf":                        pdf_vars["pdf106"] = "106/"
                    elif filename == "110.pdf":                        pdf_vars["pdf110"] = "110/"
                    elif filename == "111.pdf":                        pdf_vars["pdf111"] = "111/"
                    elif filename == "112.pdf":                        pdf_vars["pdf112"] = "112/"
                    elif filename == "113.pdf":                        pdf_vars["pdf113"] = "113/"
                    elif filename == "114.pdf":                        pdf_vars["pdf114"] = "114/"
                    elif filename == "115.pdf":                        pdf_vars["pdf115"] = "115/"
                    elif filename == "116.pdf":                        pdf_vars["pdf116"] = "116/"
                    elif filename == "117.pdf":                        pdf_vars["pdf117"] = "117/"
                    elif filename == "118.pdf":                        pdf_vars["pdf118"] = "118/"
                    elif filename == "120.pdf":                        pdf_vars["pdf120"] = "120/"
                    elif filename == "121.pdf":                        pdf_vars["pdf121"] = "121/"
                    elif filename == "122.pdf":                        pdf_vars["pdf122"] = "122/"
                    elif filename == "123.pdf":                        pdf_vars["pdf123"] = "123/"
                    elif filename == "124.pdf":                        pdf_vars["pdf124"] = "124/"
                    elif filename == "125.pdf":                        pdf_vars["pdf125"] = "125/"
                    elif filename == "126.pdf":                        pdf_vars["pdf126"] = "126/"
                    elif filename == "31-4.pdf":                        pdf_vars["pdf31_4"] = "31-4/"
                    elif filename == "35-2.pdf":                        pdf_vars["pdf35_2"] = "35-2/"
                    elif filename == "42-2.pdf":                        pdf_vars["pdf42_2"] = "42-2/"
                    elif filename == "43-2.pdf":                        pdf_vars["pdf43_2"] = "43-2/"
                    elif filename == "52-2.pdf":                        pdf_vars["pdf52_2"] = "52-2/"
                    elif filename == "54-1.pdf":                        pdf_vars["pdf54_1"] = "54-1/"
                    elif filename == "56-1.pdf":                        pdf_vars["pdf56_1"] = "56-1/"
                    elif filename == "57-2.pdf":                        pdf_vars["pdf57_2"] = "57-2/"
                    elif filename == "58-2.pdf":                        pdf_vars["pdf58_2"] = "58-2/"
                    elif filename == "58-3.pdf":                        pdf_vars["pdf58_3"] = "58-3/"
                    elif filename == "58-5.pdf":                        pdf_vars["pdf58_5"] = "58-5/"
                    elif filename == "58-6.pdf":                        pdf_vars["pdf58_6"] = "58-6/"
                    elif filename == "58-7.pdf":                        pdf_vars["pdf58_7"] = "58-7/"
                    elif filename == "58-8.pdf":                        pdf_vars["pdf58_8"] = "58-8/"
                    elif filename == "63-4.pdf":                        pdf_vars["pdf63_4"] = "63-4/"
                    elif filename == "64-5.pdf":                        pdf_vars["pdf64_5"] = "64-5/"
                    elif filename == "71-2.pdf":                        pdf_vars["pdf71_2"] = "71-2/"
                    elif filename == "71-8.pdf":                        pdf_vars["pdf71_8"] = "71-8/"
                    elif filename == "74-1.pdf":                        pdf_vars["pdf74_1"] = "74-1/"
                    elif filename == "74-2.pdf":                        pdf_vars["pdf74_2"] = "74-2/"
                    elif filename == "75-3.pdf":                        pdf_vars["pdf75_3"] = "75-3/"
                    elif filename == "75-4.pdf":                        pdf_vars["pdf75_4"] = "75-4/"
                    elif filename == "76-2.pdf":                        pdf_vars["pdf76_2"] = "76-2/"
                    elif filename == "76-3.pdf":                        pdf_vars["pdf76_3"] = "76-3/"
                    elif filename == "76-4.pdf":                        pdf_vars["pdf76_4"] = "76-4/"
                    elif filename == "20-2-1.pdf":                      pdf_vars["pdf20_2_1"] = "20-2-1/"
                    elif filename == "15-1.pdf":                        pdf_vars["pdf15_1"] = "15-1/"
                    elif filename == "20-1.pdf":                        pdf_vars["pdf20_1"] = "20-1/"
                    elif filename == "31-1.pdf":                        pdf_vars["pdf31_1"] = "31-1/"
                    elif filename == "15-2.pdf":                        pdf_vars["pdf15_2"] = "15-2/"
                    elif filename == "16-2.pdf":                        pdf_vars["pdf16_2"] = "16-2/"
                    elif filename == "20-2.pdf":                        pdf_vars["pdf20_2"] = "20-2/"
                    elif filename == "3-1.pdf":                        pdf_vars["pdf3_1"] = "3-1/"
                    elif filename == "3-2.pdf":                        pdf_vars["pdf3_2"] = "3-2/"
                    elif filename == "3-3.pdf":                        pdf_vars["pdf3_3"] = "3-3/"
                    elif filename == "3-4.pdf":                        pdf_vars["pdf3_4"] = "3-4/"
                    elif filename == "20-3.pdf":                        pdf_vars["pdf20_3"] = "20-3/"
                    elif filename == "31-3.pdf":                        pdf_vars["pdf31_3"] = "31-3/"
                    elif filename == "20-4.pdf":                        pdf_vars["pdf20_4"] = "20-4/"
                    elif filename == "6-2.pdf":                        pdf_vars["pdf6_2"] = "6-2/"
                    elif filename == "6-11.pdf":                        pdf_vars["pdf6_11"] = "6-11/"
                    elif filename == "6-12.pdf":                        pdf_vars["pdf6_12"] = "6-12/"
                    elif filename == "8-1.pdf":                        pdf_vars["pdf8_1"] = "8-1/"
                    elif filename == "8-2.pdf":                        pdf_vars["pdf8_2"] = "8-2/"
                    elif filename == "8-3.pdf":                        pdf_vars["pdf8_3"] = "8-3/"
                    elif filename == "8-4.pdf":                        pdf_vars["pdf8_4"] = "8-4/"
                    elif filename == "8-5.pdf":                        pdf_vars["pdf8_5"] = "8-5/"
                    elif filename == "8-6.pdf":                        pdf_vars["pdf8_6"] = "8-6/"
                    elif filename == "8-9.pdf":                        pdf_vars["pdf8_9"] = "8-9/"
                    elif filename == "0-1.pdf":                        pdf_vars["pdf0_1"] = "0-1/"
                    elif filename == "10-갑.pdf":                        pdf_vars["pdf10_1"] = "10-갑/"
                    elif filename == "10-을.pdf":                        pdf_vars["pdf10_2"] = "10-을/"
                    elif filename == "19-갑.pdf":                        pdf_vars["pdf19_1"] = "19-갑/"
                    elif filename == "19-을.pdf":                        pdf_vars["pdf19_2"] = "19-을/"
                    elif filename == "23-갑.pdf":                        pdf_vars["pdf23_1"] = "23-갑/"
                    elif filename == "23-을.pdf":                        pdf_vars["pdf23_2"] = "23-을/"
                    elif filename == "26-갑.pdf":                        pdf_vars["pdf26_1"] = "26-갑/"
                    elif filename == "26-을.pdf":                        pdf_vars["pdf26_2"] = "26-을/"
                    elif filename == "27-갑.pdf":                        pdf_vars["pdf27_1"] = "27-갑/"
                    elif filename == "27-을.pdf":                        pdf_vars["pdf27_2"] = "27-을/"
                    elif filename == "40-갑.pdf":                        pdf_vars["pdf40_1"] = "40-갑/"
                    elif filename == "40-을.pdf":                        pdf_vars["pdf40_2"] = "40-을/"
                    elif filename == "46-2-갑.pdf":                        pdf_vars["pdf46_2_1"] = "46-2-갑/"
                    elif filename == "46-2-을.pdf":                        pdf_vars["pdf46_2_2"] = "46-2-을/"
                    elif filename == "46-갑.pdf":                        pdf_vars["pdf46_1"] = "46-갑/"
                    elif filename == "46-을.pdf":                        pdf_vars["pdf46_2"] = "46-을/"
                    elif filename == "47-갑.pdf":                        pdf_vars["pdf47_1"] = "47-갑/"
                    elif filename == "47-을.pdf":                        pdf_vars["pdf47_2"] = "47-을/"
                    elif filename == "50-갑.pdf":                        pdf_vars["pdf50_1"] = "50-갑/"
                    elif filename == "50-을.pdf":                        pdf_vars["pdf50_2"] = "50-을/"
                    elif filename == "52-갑.pdf":                        pdf_vars["pdf52_1"] = "52-갑/"
                    elif filename == "52-을.pdf":                        pdf_vars["pdf52_2"] = "52-을/"
                    elif filename == "63-16-1.pdf":                        pdf_vars["pdf63_16_1"] = "63-16-1/"
                    elif filename == "63-16-2.pdf":                        pdf_vars["pdf63_16_2"] = "63-16-2/"
                    elif filename == "63-16-3.pdf":                        pdf_vars["pdf63_16_3"] = "63-16-3/"
                    elif filename == "63-16-4.pdf":                        pdf_vars["pdf63_16_4"] = "63-16-4/"
                    elif filename == "8-갑.pdf":                        pdf_vars["pdf8_A"] = "8-갑/"
                    elif filename == "8-을.pdf":                        pdf_vars["pdf8_B"] = "8-을/"
                    elif filename == "91-조-1.pdf":                        pdf_vars["pdf91_1"] = "91-조-1/"
                    elif filename == "91-조-10.pdf":                        pdf_vars["pdf91_10"] = "91-조-10/"
                    elif filename == "91-조-10-8.pdf":                        pdf_vars["pdf91_10_8"] = "91-조-10-8/"
                    elif filename == "91-조-11-3-1.pdf":                        pdf_vars["pdf91_11_3_1"] = "91-조-11-3-1/"
                    elif filename == "91-조-11-3-2.pdf":                        pdf_vars["pdf91_11_3_2"] = "91-조-11-3-2/"
                    elif filename == "91-조-11-3-3.pdf":                        pdf_vars["pdf91_11_3_3"] = "91-조-11-3-3/"
                    elif filename == "91-조-11-4.pdf":                        pdf_vars["pdf91_11_4"] = "91-조-11-4/"
                    elif filename == "91-조-11-5.pdf":                        pdf_vars["pdf91_11_5"] = "91-조-11-5/"
                    elif filename == "91-조-1-2.pdf":                        pdf_vars["pdf91_1_2"] = "91-조-1-2/"
                    elif filename == "91-조-2.pdf":                        pdf_vars["pdf91_2"] = "91-조-2/"
                    elif filename == "91-조-2-2.pdf":                        pdf_vars["pdf91_2_2"] = "91-조-2-2/"
                    elif filename == "91-조-2-3.pdf":                        pdf_vars["pdf91_2_3"] = "91-조-2-3/"
                    elif filename == "91-조-26.pdf":                        pdf_vars["pdf91_26"] = "91-조-26/"
                    elif filename == "91-조-3-1.pdf":                        pdf_vars["pdf91_3_1"] = "91-조-3-1/"
                    elif filename == "91-조-31.pdf":                        pdf_vars["pdf91_31"] = "91-조-31/"
                    elif filename == "91-조-3-1-1.pdf":                        pdf_vars["pdf91_3_1_1"] = "91-조-3-1-1/"
                    elif filename == "91-조-3-2.pdf":                        pdf_vars["pdf91_3_2"] = "91-조-3-2/"
                    elif filename == "91-조-35.pdf":                        pdf_vars["pdf91_35"] = "91-조-35/"
                    elif filename == "91-조-37-2.pdf":                        pdf_vars["pdf91_37_2"] = "91-조-37-2/"
                    elif filename == "91-조-38.pdf":                        pdf_vars["pdf91_38"] = "91-조-38/"
                    elif filename == "91-조-38-2.pdf":                        pdf_vars["pdf91_38_2"] = "91-조-38-2/"
                    elif filename == "91-조-40-4.pdf":                        pdf_vars["pdf91_40_4"] = "91-조-40-4/"
                    elif filename == "91-조-43.pdf":                        pdf_vars["pdf91_43"] = "91-조-43/"
                    elif filename == "91-조-45.pdf":                        pdf_vars["pdf91_45"] = "91-조-45/"
                    elif filename == "91-조-45-2.pdf":                        pdf_vars["pdf91_45_2"] = "91-조-45-2/"
                    elif filename == "91-조-46.pdf":                        pdf_vars["pdf91_46"] = "91-조-46/"
                    elif filename == "91-조-46-2.pdf":                        pdf_vars["pdf91_46_2"] = "91-조-46-2/"
                    elif filename == "91-조-47.pdf":                        pdf_vars["pdf91_47"] = "91-조-47/"
                    elif filename == "91-조-49.pdf":                        pdf_vars["pdf91_49"] = "91-조-49/"
                    elif filename == "91-조-60-2.pdf":                        pdf_vars["pdf91_60_2"] = "91-조-60-2/"
                    elif filename.strip() == "91-조-62.pdf":                        pdf_vars["pdf91_62"] = "91-조-62/"
                    elif filename == "91-조-64-10.pdf":                        pdf_vars["pdf91_64_10"] = "91-조-64-10/"
                    elif filename == "91-조-64-14.pdf":                        pdf_vars["pdf91_64_14"] = "91-조-64-14/"
                    elif filename == "91-조-64-15.pdf":                        pdf_vars["pdf91_64_15"] = "91-조-64-15/"
                    elif filename == "91-조-64-19.pdf":                        pdf_vars["pdf91_64_19"] = "91-조-64-19/"
                    elif filename == "91-조-64-4.pdf":                        pdf_vars["pdf91_64_4"] = "91-조-64-4/"
                    elif filename == "91-조-64-5.pdf":                        pdf_vars["pdf91_64_5"] = "91-조-64-5/"
                    elif filename == "91-조-64-7.pdf":                        pdf_vars["pdf91_64_7"] = "91-조-64-7/"
                    elif filename == "91-조-64-8.pdf":                        pdf_vars["pdf91_64_8"] = "91-조-64-8/"
                    elif filename == "91-조-64-9.pdf":                        pdf_vars["pdf91_64_9"] = "91-조-64-9/"
                    elif filename == "91-조-9.pdf":                        pdf_vars["pdf91_9"] = "91-조-9/"
                    elif filename == "92-지-43.pdf":                        pdf_vars["pdf92_43"] = "92-지-43/"
                    elif filename == "92-지-43-2.pdf":                        pdf_vars["pdf92_43_2"] = "92-지-43-2/"
                    elif filename == "92-지-43-5-갑.pdf":                        pdf_vars["pdf92_43_5_1"] = "92-지-43-5-갑/"
                    elif filename == "92-지-43-5-을.pdf":                        pdf_vars["pdf92_43_5_2"] = "92-지-43-5-을/"
                    elif filename == "198.pdf":                        pdf_vars["pdf198"] = "198"
                    elif filename == "199.pdf":                        pdf_vars["pdf199"] = "199"

        # PDF 누락에 따른 skeleton 처리
        for key in ["pdf198", "pdf199", "pdf101", "pdf102", "pdf104", "pdf105", "pdf106", "pdf3_1", "pdf3_2", "pdf3_4"]:
            if not pdf_vars.get(key):
              isSkeleton = True;       strSkeleton += "#" + key.replace("pdf","")
        if saleAmt > 0 and not pdf_vars.get("pdf16"):
            isSkeleton = True;            strSkeleton += "#16"
        if saleAmt > 0 and not pdf_vars.get("pdf17"):
            isSkeleton = True;            strSkeleton += "#17"
        if float(row.get("재고자산", 0)) > 0 and not pdf_vars.get("pdf39"):
            isSkeleton = True;            strSkeleton += "#39"
        if float(row.get("차량", 0)) > 0 and not pdf_vars.get("pdf29"):
            isSkeleton = True;            strSkeleton += "#29"
        if float(row.get("감가상각", 0)) > 0 and not pdf_vars.get("pdf20_4"):
            isSkeleton = True;            strSkeleton += "#20-4"
        if (float(row.get("고정자산", 0)) - float(row.get("토지", 0))) > 0 and not pdf_vars.get("pdf110"):
            isSkeleton = True;            strSkeleton += "#110"
        if float(row.get("가지급", 0)) > 0 and not pdf_vars.get("pdf19_1"):
            isSkeleton = True;            strSkeleton += "#19-1"
        if (float(row.get("이자비용", 0)) > 0 and float(row.get("가지급", 0)) > 0 and
            float(row.get("대손금", 0)) > 0 and float(row.get("접대비", 0)) > 0 and
            float(row.get("기부금", 0)) > 0 and not pdf_vars.get("pdf47_1")):
            isSkeleton = True;            strSkeleton += "#47-갑"
        if float(row.get("재고자산", 0)) > 0 and not pdf_vars.get("pdf47_2"):
            isSkeleton = True;            strSkeleton += "#47-을"
        if not pdf_vars.get("pdf50_1"):
            isSkeleton = True;            strSkeleton += "#50-갑"
        if not pdf_vars.get("pdf51"):
            isSkeleton = True;            strSkeleton += "#51"
        if row.get("주식변동") and not pdf_vars.get("pdf54"):
            isSkeleton = True;            strSkeleton += "#54"
        if not pdf_vars.get("pdf85"):
            isSkeleton = True;            strSkeleton += "#85"
        if not pdf_vars.get("pdf90"):
            isSkeleton = True;            strSkeleton += "#90"
        if not pdf_vars.get("pdf99"):
            isSkeleton = True;            strSkeleton += "#99"
        if not pdf_vars.get("pdf3"):
            isSkeleton = True;            strSkeleton += "#3"
        if not pdf_vars.get("pdf1"):
            isSkeleton = True;            strSkeleton += "#1"
        if not pdf_vars.get("pdf92_43"):
            isSkeleton = True;            strSkeleton += "#92-지-43"
        if net_income > 0 and (SpecialDeductRate>0 or ChangUpDeductRate>0) and not pdf_vars.get("pdf4"):
            isSkeleton = True;            strSkeleton += "#4"
        if net_income > 0 and (SpecialDeductRate>0 or ChangUpDeductRate>0) and not pdf_vars.get("pdf8_A"):
            isSkeleton = True;            strSkeleton += "#8-갑"
        if net_income > 0 and (SpecialDeductRate>0 or ChangUpDeductRate>0) and not pdf_vars.get("pdf8_2"):
            isSkeleton = True;            strSkeleton += "#8-2"
        if net_income > 0 and (SpecialDeductRate>0 or ChangUpDeductRate>0) and not pdf_vars.get("pdf91_2"):
            isSkeleton = True;            strSkeleton += "#91-조-2"
        if float(row.get("Increase_UsualEmp", 0)) > 0 and not pdf_vars.get("pdf8_3"):
            isSkeleton = True;            strSkeleton += "#8-3"
        if float(row.get("Increase_UsualEmp", 0)) > 0 and not pdf_vars.get("pdf91_1"):
            isSkeleton = True;            strSkeleton += "#91-조-1"
        if float(row.get("Increase_UsualEmp", 0)) > 0 and not pdf_vars.get("pdf91_10_8"):
            isSkeleton = True;            strSkeleton += "#91-조-10-8"
        if float(row.get("Increase_UsualEmp", 0)) > 0 and not pdf_vars.get("pdf91_11_5"):
            isSkeleton = True;            strSkeleton += "#91-조-11-5"
        imgSkeleton = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-heart.png'>"
        if isSkeleton: imgSkeleton = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
        # 숫자형식 처리 및 recordset 항목 구성
        rec.append({
          'groupManager':row.get("admin_id"),
          'seq_no':    str(row.get("seq_no")).strip(),
          'biz_name':  row.get("biz_name").strip(),
          'SALE' :  format_number(row.get("매출", 0)),
          'BENE':  format_number(row.get("순손익", 0)),
          'T817':  format_number(row.get("T817", 0)),
          'S817':  format_number(row.get("S817", 0)),
          'AA':  format_number(row.get("접대비", 0)),
          'BB':  format_number(row.get("기부금", 0)),
          'CC':  format_number(row.get("대손금", 0)),
          'DD':  format_number(row.get("이자비용", 0)),
          'EE':  format_number(row.get("차입금", 0)),
          'FF':  format_number(row.get("가지급", 0)),
          'GG':  format_number(row.get("가수금", 0)),
          'HH':  format_number(row.get("선납세금", 0)),
          'JJ':  format_number(row.get("미수수익", 0)),
          'WW':  format_number(row.get("이자수익", 0)),
          'XX':  format_number(row.get("배당금수익", 0)),
          'YY':  format_number(float(row.get("외화환산이익", 0)) + float(row.get("외화환산손실", 0))),
          'KK':  format_number(row.get("고정자산", 0)),
          'LL':  format_number(row.get("감가상각", 0)),
          'MM':  format_number(row.get("차량", 0)),
          'NN':  format_number(row.get("재고자산", 0)),
          'PP':  format_number(row.get("토지", 0)),
          'QQ':  format_number(row.get("중간배당", 0)),
          'VV':  str(row.get("최종분개")),
          'RR':  format_number(row.get("결산분개", 0)),
          'SS':  format_number(row.get("주식변동", 0)),
          'ZZ':  format_number(row.get("법인세비용", 0)),
          'AB':  str(deductRate),
          'AC':  "0",
          'inspect_issue':  ""
        })

        # PDF 관련 정보(폰트 스타일 적용)
        pdf_info1 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf16', '')}{pdf_vars.get('pdf17', '')}</font>"
        pdf_info2 = f"<font style='color:red;font-weight:bold;'>{imgSkeleton}</font>"
        pdf_info3 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf6_11', '')}</font>"
        pdf_info4 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf15', '')}</font>"
        pdf_info5 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf23_1', '')}</font>"
        pdf_info6 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf21', '')}{pdf_vars.get('pdf22', '')}</font>"
        pdf_info7 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf34', '')}</font>"
        pdf_info8 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf26_1', '')}</font>"
        pdf_info9 = ""  # 차입금 관련 빈 값
        pdf_info10 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf19_1', '')}</font>"
        pdf_info11 = ""  # 가수금
        pdf_info12 = ""  # 선납세금
        pdf_info13 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf19_2', '')}</font>"
        pdf_info14 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf10_1', '')}</font>"
        pdf_info15 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf16_2', '')}</font>"
        pdf_info16 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf40_1', '')}{pdf_vars.get('pdf40_2')}</font>"
        pdf_info17 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf110')}{pdf_vars.get('pdf111')}{pdf_vars.get('pdf112')}" + \
                     f"{pdf_vars.get('pdf113')}{pdf_vars.get('pdf114')}{pdf_vars.get('pdf115')}" + \
                     f"{pdf_vars.get('pdf116')}{pdf_vars.get('pdf117')}{pdf_vars.get('pdf120')}" + \
                     f"{pdf_vars.get('pdf121')}{pdf_vars.get('pdf122')}{pdf_vars.get('pdf123')}" + \
                     f"{pdf_vars.get('pdf124')}{pdf_vars.get('pdf125')}{pdf_vars.get('pdf126')}</font>"
        pdf_info18 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf20_1')}{pdf_vars.get('pdf20_2')}{pdf_vars.get('pdf20_3')}" + \
                     f"{pdf_vars.get('pdf20_4')}{pdf_vars.get('pdf20_2_1')}</font>"
        pdf_info19 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf29')}</font>"
        pdf_info20 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf39')}</font>"
        pdf_info21 = ""  # 토지 빈값
        pdf_info22 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf104')}</font>"
        pdf_info23 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf101')}{pdf_vars.get('pdf102')}{pdf_vars.get('pdf103')}" + \
                     f"{pdf_vars.get('pdf105')}{pdf_vars.get('pdf106')}</font>"
        pdf_info24 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf3_1')}{pdf_vars.get('pdf3_2')}{pdf_vars.get('pdf3_3')}" + \
                     f"{pdf_vars.get('pdf3_4')}</font>"
        pdf_info25 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf54')}{pdf_vars.get('pdf54_1')}</font>"
        pdf_info26 = f"<font style='color:blue;font-weight:bold;'>{pdf_vars.get('pdf15')}</font>"
        pdf_info27 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf4')}{pdf_vars.get('pdf8_2')}{pdf_vars.get('pdf8_A')}" + \
                     f"{pdf_vars.get('pdf91_2')}</font>"
        pdf_info28 = f"<font style='color:blue;font-weight:bold;'>" + \
                     f"{pdf_vars.get('pdf8_3')}{pdf_vars.get('pdf91_1')}{pdf_vars.get('pdf91_10_8')}" + \
                     f"{pdf_vars.get('pdf91_11_5')}</font>"
        pdf_info29 = strSkeleton
        rec.append({
          'groupManager':row.get("admin_id"),
          'seq_no':    str(row.get("seq_no")).strip(),
          'biz_name':  row.get("biz_name").strip()+"(도움)",
          'SALE' :  pdf_info1,
          'BENE':  pdf_info2,
          'T817':  pdf_info3,
          'S817':  pdf_info4,
          'AA':  pdf_info5,#format_number(row.get("접대비", 0)),
          'BB':  pdf_info6,#format_number(row.get("기부금", 0)),
          'CC':  pdf_info7,#format_number(row.get("대손금", 0)),
          'DD':  pdf_info8,#format_number(row.get("이자비용", 0)),
          'EE':  pdf_info9,#format_number(row.get("차입금", 0)),
          'FF':  pdf_info10,#format_number(row.get("가지급", 0)),
          'GG':  pdf_info11,#format_number(row.get("가수금", 0)),
          'HH':  pdf_info12,#format_number(row.get("선납세금", 0)),
          'JJ':  pdf_info13,#format_number(row.get("미수수익", 0)),
          'WW':  pdf_info14,#format_number(row.get("이자수익", 0)),
          'XX':  pdf_info15,#format_number(row.get("배당금수익", 0)),
          'YY':  pdf_info16,#format_number(float(row.get("외화환산이익", 0)) + float(row.get("외화환산손실", 0))),
          'KK':  pdf_info17,#format_number(row.get("고정자산", 0)),
          'LL':  pdf_info18,#format_number(row.get("감가상각", 0)),
          'MM':  pdf_info19,#format_number(row.get("차량", 0)),
          'NN':  pdf_info20,#format_number(row.get("재고자산", 0)),
          'PP':  pdf_info21,#format_number(row.get("토지", 0)),
          'QQ':  pdf_info22,#format_number(row.get("중간배당", 0)),
          'VV':  pdf_info23,#str(row.get("최종분개')),
          'RR':  pdf_info24,#format_number(row.get("결산분개", 0)),
          'SS':  pdf_info25,#format_number(row.get("주식변동", 0)),
          'ZZ':  pdf_info26,#format_number(row.get("법인세비용", 0)),
          'AB':  pdf_info27,#str(deductRate),
          'AC':  pdf_info28,#"0",
          'inspect_issue': pdf_info29# ""
        })

    return rec

#세액감면공제정보 툴팁작성
def mng_corp_deduct_tooltip(request):
  seq_no = request.POST.get('seq_no')
  work_YY = request.POST.get('work_YY')
  if seq_no:
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    memdeal = get_object_or_404(MemDeal, seq_no=seq_no)
    reg_date = memuser.reg_date.strftime('%Y-%m-%d')[:10]
    
    isRND = memuser.isrnd
    isVenture = memuser.isventure
    isYoung = "N"

    region = f"{memuser.biz_addr1}{memuser.biz_addr2}"
    upJong = f"{memuser.uptae} {memuser.jongmok}"
    kisu = int(work_YY) - int(reg_date[:4]) + 1
    birth_year_prefix = 2000 if '00' <= memuser.ssn[:2] <= '24' else 1900
    birth_year = birth_year_prefix + int(memuser.ssn[:2])
    age =  int(work_YY) - birth_year    
    sql_query = f"""
      SELECT 
          isnull(SUM(CASE WHEN acnt_cd BETWEEN 401 AND 430 THEN tranamt_Dr ELSE 0 END),0) AS 매출액,
          isnull(SUM(CASE WHEN acnt_cd > 400 AND Remk <> '손익계정에 대체' THEN tranamt_dr - tranamt_cr ELSE 0 END),0) AS 순손익,
          isnull((SELECT  TRIM(결손금누계) AS 이월결손금  FROM tbl_EquityEval 
          WHERE LEFT(사업연도말, 4) = CAST('{work_YY}' AS VARCHAR)  and 사업자번호='{memuser.biz_no}'),0) AS 이월결손금
      FROM ds_slipledgr2 WITH (NOLOCK)
      WHERE seq_no = {seq_no} AND work_yy = '{work_YY}'
    """  
    #print(sql_query)  
    previous_year = int(work_YY) - 1  # 이월결손금 조회를 위한 연도 계산

    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        result = cursor.fetchone() 
    saleAmt = result[0] if result else 0
    net_income = int(result[1]) if result else 0  
    valDefict = result[2] if result else 0
    if valDefict=="" or valDefict==None:
      valDefict = 0
    else:
      valDefict = int(valDefict)
   
    if age is not None and float(age) < 36:
        isYoung = "Y"

    # 수도권과밀억제권역 판단 Y 또는 "" => 창업감면 판단
    isKWAMIL = func_isKWAMIL(region)
    # 수도권(도시) 여부: 해당 단어가 없으면 지방(Y)
    isRural_count = sum(1 for r in ["서울", "인천", "경기"] if r in region)
    isRural = "Y" if isRural_count <= 0 else ""
    # 특별세액감면 검토 (업종)
    isSpecialUpjong = func_isSpecialDeductUpjong(upJong)
    # 소기업/중기업 판별
    isSmall = func_isSmall(upJong,saleAmt)
    # 지식기반사업 여부
    isKnowledge = func_isKnowledge(upJong)
    # 창업 관련 변수
    isChangUpUpjong = func_isChangUp(upJong)
    # 물류산업여부/성정산업
    isMyulyu = func_isMyulyu(upJong)
    isNewGroth = func_isNewGroth(upJong)
    # 물류산업여부/신성장산업 인 경우 특별감면과 창업감면 대상이다
    if isMyulyu=="Y" or isNewGroth=="Y":
       isSpecialUpjong = "Y"
       isChangUpUpjong = "Y"
    # 감면율 판단
    SpecialDeductRate,SpecialDeduct = func_SpecialDeduct(upJong,isSpecialUpjong,isRural,isSmall)
    ChangUpDeductRate,ChangUpDeduct,isLittle = func_ChangupDeduct(work_YY,kisu,isKWAMIL,isChangUpUpjong,isNewGroth,isVenture,saleAmt,reg_date,age)

    # 재무조건에 따른 감면율 조정
    # if (net_income - float(valDefict)) < 0 or net_income < 0:
    #     ChangUpDeductRate = 0;SpecialDeductRate = 0

    #고용증대 인원
    cntGoyoungIncrease = func_cntGoyoungIncrease(seq_no,work_YY,reg_date,memdeal.fiscalmm)

    deduct_info = {
      'biz_name': memuser.biz_name,
      'ceo_name':memuser.ceo_name,
      'age':age,
      'kisu':kisu,
      'addr':region,
      'upjong': upJong,
      'SpecialDeduct': SpecialDeduct,
      'isSpecialUpjong': isSpecialUpjong,
      'ChangUpDeduct': ChangUpDeduct,
      'SpecialDeductRate': SpecialDeductRate,      
      'ChangUpDeduct': ChangUpDeduct,
      'ChangUpDeductRate': ChangUpDeductRate,
      'cntGoyoungIncrease': round(cntGoyoungIncrease,3),
      'isRND': isRND,
      'isVenture': isVenture,
      'isYoung': isYoung,
      'isKWAMIL': isKWAMIL,
      'isRural': isRural,
      'isSmall': isSmall,
      'isKnowledge':isKnowledge,
      'isMyulyu': isMyulyu,
      'isNewGroth': isNewGroth,
      "isLittle" : isLittle
    }
    return JsonResponse(deduct_info)
  else:
      return JsonResponse({'error': 'Invalid request method.'}, status=400)

#전자신고 접수증 가져오기
def mng_corp_jupsuSummit(request):
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

#전자신고 파일 업로드 - 정기/기한후
def save_elecfile_Corp(request):
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
  if ext not in ["01", "03"]:
      return HttpResponse(
          "<script language='javascript'>"
          "alert('법인세 전자신고 파일이 아닙니다.');"
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

  # 각 레코드를 저장할 리스트들 (ReDim preserve 대신 사용)
  record_81D100100    = []
  record_83D100200    = []
  record_83D100100    = []
  record_83D100300    = []
  record_83D103700_813 = []
  record_83D103700_816 = []
  record_83D103700_817 = []
  record_83D103700_818 = []
  record_83D103700_819 = []
  record_83D103700_820 = []
  record_83D103700_822 = []
  record_83D103700_955 = []
  record_83D103700_300 = []
  record_83D103700_301 = []
  record_83D103700_302 = []
  record_83D100500_100 = []
  record_83D100500_176 = []
  record_83D100500_200 = []
  record_93D108700     = []
  record_94D108600     = []

  # 파일 읽기 (인코딩 cp949)
  with open(save_file_name, "r", encoding="cp949", errors="ignore") as f:
      for line in f:
          sr = line.rstrip("\n")
          if sr.startswith("81D100100"):
              record_81D100100.append(sr)
              # 각 리스트에 빈 문자열을 추가하여 동일 인덱스 맞춤
              record_83D100200.append("")
              record_83D100100.append("")
              record_83D100300.append("")
              record_83D103700_813.append("")
              record_83D103700_816.append("")
              record_83D103700_817.append("")
              record_83D103700_818.append("")
              record_83D103700_819.append("")
              record_83D103700_820.append("")
              record_83D103700_822.append("")
              record_83D103700_955.append("")
              record_83D103700_300.append("")
              record_83D103700_301.append("")
              record_83D103700_302.append("")
              record_83D100500_100.append("")
              record_83D100500_176.append("")
              record_83D100500_200.append("")
              record_93D108700.append("")
              record_94D108600.append("")
          else:
              if not record_81D100100:
                  continue
              idx = len(record_81D100100) - 1
              if sr.startswith("83D100200"):
                  record_83D100200[idx] = mid_union(sr, 85, 60).strip()
              elif sr.startswith("83D100100"):
                  record_83D100100[idx] = sr
              elif sr.startswith("83D100300"):
                  record_83D100300[idx] = sr
              elif sr.startswith("83D103700"):
                  if sr[9:11] == "01":
                      if "접대" in sr:
                          record_83D103700_813[idx] = mid_union(sr, 58, 15).strip()
                      elif ("벌금" in sr) or ("과금" in sr) or ("과태료" in sr):
                          record_83D103700_816[idx] = mid_union(sr, 58, 15).strip()
                      elif "세금과" in sr:
                          record_83D103700_817[idx] = mid_union(sr, 58, 15).strip()
                      elif "무관" in sr and ("이자" not in sr):
                          record_83D103700_818[idx] = mid_union(sr, 58, 15).strip()
                      elif ("이자" in sr) and ("인정" not in sr):
                          record_83D103700_819[idx] = mid_union(sr, 58, 15).strip()
                      elif "외화" in sr:
                          record_83D103700_955[idx] = mid_union(sr, 58, 15).strip()   
                      elif "승용" in sr:
                          record_83D103700_822[idx] = mid_union(sr, 58, 15).strip()    
                      elif "감가" in sr:
                          record_83D103700_820[idx] = mid_union(sr, 58, 15).strip()                           
                  elif mid_union(sr, 9, 2) == "02":
                      if "배당" in sr:
                          record_83D103700_300[idx] = mid_union(sr, 58, 15).strip()
                      elif "외화" in sr:
                          record_83D103700_302[idx] = mid_union(sr, 58, 15).strip()                          
                      elif "승용" in sr:
                          record_83D103700_301[idx] = mid_union(sr, 58, 15).strip()                          


              elif sr.startswith("83D100500"):
                  if mid_union(sr, 10, 6) == "210071":
                      record_83D100500_100[idx] = mid_union(sr, 16, 16).strip()
                  elif mid_union(sr, 10, 6) == "210102":
                      record_83D100500_200[idx] = mid_union(sr, 16, 16).strip()
                  elif mid_union(sr, 10, 6) == "210176":
                      record_83D100500_176[idx] = mid_union(sr, 16, 16).strip()
              elif sr.startswith("94D108600"):
                  record_94D108600[idx] = mid_union(sr, 157, 15).strip()
              elif sr.startswith("93D108700"):
                  record_93D108700[idx] = mid_union(sr, 101, 15).strip()

  # 각 회사 레코드별로 데이터 추출 후 SQL 쿼리 실행
  with connection.cursor() as cursor:
      for k in range(len(record_81D100100)):
          primary = record_81D100100[k]
          biz_no = (
              mid_union(primary, 18, 3)
              + "-"
              + mid_union(primary, 21, 2)
              + "-"
              + mid_union(primary, 23, 5)
          )
          kwasekikan = mid_union(primary, 12, 6)
          wcTotLocalTax = 0
          corp_no = mid_union(primary, 49, 13)
          wcYupTae = mid_union(primary, 266, 30).strip()
          wcJongMok = mid_union(primary, 296, 50).strip()
          wcYJCode = mid_union(primary, 346, 6).strip()
          wcCeoName = mid_union(primary, 122, 30).strip()
          wcAddr = mid_union(primary, 152, 70).strip()
          wcSayupFiscalYear = mid_union(primary, 352, 8) + mid_union(primary, 360, 8)
          wcSayupKB = mid_union(record_83D100100[k], 18, 2)
          wcTotCorpTax = mid_union(record_83D100100[k], 197, 15).strip()
          sanchul = mid_union(record_83D100100[k], 152, 15).strip()
          try:
              if float(sanchul) > 0:
                  wcTotLocalTax = math.floor(float(sanchul) / 100) * 10
          except Exception:
              wcTotLocalTax = 0
          wcKibuExceed = mid_union(record_83D100300[k], 70, 15).strip()
          wcKibuInceed = mid_union(record_83D100300[k], 85, 15).strip()
          wcKackIncome = mid_union(record_83D100300[k], 100, 15).strip()
          wcLimitTaxTarget = mid_union(record_83D100300[k], 245, 15).strip()
          wcLimitTaxFree = mid_union(record_83D100300[k], 275, 15).strip()
          userID = mid_union(primary, 456, 30).replace(" ", "")

          # DELETE 쿼리 실행
          delete_query = (
              "DELETE FROM tbl_equityeval WHERE 사업연도말 = %s AND 사업자번호 = %s"
          )
          cursor.execute(delete_query, [kwasekikan, biz_no])

          # INSERT 쿼리의 각 컬럼값 (총 56개)
          values = [
              biz_no,                              # 1. 사업자번호
              kwasekikan,                          # 2. 사업연도말
              corp_no,                             # 3. 법인번호
              wcYupTae,                            # 4. 업태
              wcJongMok,                           # 5. 종목
              wcYJCode,                            # 6. 코드
              wcSayupFiscalYear,                   # 7. 사업연도
              wcSayupKB,                           # 8. 회사종류
              record_83D100500_100[k],              # 9. 재무재표상 자산
              0,                                   # 10. 자산가산1 (평가차액)
              record_93D108700[k],                  # 11. 자산가산2 (법인세법상 유보금액)
              0,                                   # 12. 자산가산3 (유상증자 등)
              record_83D100500_176[k],              # 13. 자산차감1 (선급비용)
              0,                                   # 14. 자산차감2 (증자일전 잉여금 유보액)
              record_83D100500_200[k],              # 15. 재무재표상 부채
              0,                                   # 16. 부채가산배당
              0,                                   # 17. 부채가산퇴추
              wcKackIncome,                        # 18. 각사업연도 소득금액
              record_83D103700_301[k],             # 19. 환급이자   ==> 이월된 업무용승용차 손금추인액 25.8.26
              record_83D103700_300[k],             # 20. 소득가산배당
              wcKibuInceed,                        # 21. 소득가산기부추인
              record_83D103700_816[k],              # 22. 벌금
              record_83D103700_817[k],              # 23. 공과금
              record_83D103700_818[k],              # 24. 업무무관
              record_83D103700_822[k],             # 25. 징수불 ==> 업무용승용차 손금불산입 25.8.26
              wcKibuExceed,                        # 26. 기부금
              record_83D103700_813[k],              # 27. 접대비
              record_83D103700_955[k],             # 28. 과다경비 ==> 외화환산손실 25.8.26
              record_83D103700_819[k],              # 29. 지급이자
              record_83D103700_820[k],              # 30. 감비추인
              wcTotCorpTax,                        # 31. 법인세
              record_83D100200[k],                  # 32. 농특세
              wcTotLocalTax,                       # 33. 지방세
              record_93D108700[k],                  # 34. 익금유보
              0,                                   # 35. 손금유보
              record_94D108600[k],                  # 36. 결손금누계
              wcLimitTaxTarget,                    # 37. 최저한세적용대상
              wcLimitTaxFree,                      # 38. 최저한세적용제외
              mid_union(record_83D100100[k], 62, 15),   # 39. 수입금액
              mid_union(record_83D100100[k], 77, 15),   # 40. 과세표준_법인세
              mid_union(record_83D100100[k], 92, 15),   # 41. 과세표준_토지
              mid_union(record_83D100100[k], 107, 15),  # 42. 과세표준_합계
              mid_union(record_83D100100[k], 122, 15),  # 43. 산출세액_법인세
              mid_union(record_83D100100[k], 137, 15),  # 44. 산출세액_토지
              mid_union(record_83D100100[k], 152, 15),  # 45. 산출세액_합계
              mid_union(record_83D100100[k], 167, 15),  # 46. 총부담세액_법인세
              mid_union(record_83D100100[k], 182, 15),  # 47. 총부담세액_토지
              mid_union(record_83D100100[k], 197, 15),  # 48. 총부담세액_합계
              mid_union(record_83D100100[k], 212, 15),  # 49. 기납부세액_법인세
              mid_union(record_83D100100[k], 227, 15),  # 50. 기납부세액_토지
              mid_union(record_83D100100[k], 242, 15),  # 51. 기납부세액_합계
              mid_union(record_83D100100[k], 257, 15),  # 52. 차감납부세액_법인세
              mid_union(record_83D100100[k], 272, 15),  # 53. 차감납부세액_토지
              mid_union(record_83D100100[k], 287, 15),  # 54. 차감납부세액_합계
              mid_union(record_83D100100[k], 302, 15),  # 55. 분납세액
              mid_union(record_83D100100[k], 317, 15),  # 56. 차감납부세액
          ]
          placeholders = ", ".join(["%s"] * len(values))
          insert_query = "INSERT INTO tbl_equityeval VALUES (" + placeholders + ")"
          cursor.execute(insert_query, values)

          # UPDATE 쿼리 실행
          update_query = (
              "UPDATE mem_user SET uptae = %s, Jongmok = %s, Ceo_name = %s, "
              "biz_addr1 = %s, biz_addr2 = '' WHERE biz_no = %s"
          )
          cursor.execute(update_query, [wcYupTae, wcJongMok, wcCeoName, wcAddr, biz_no])

          # MERGE 쿼리 실행 (SQL Server의 MERGE 구문 예시)
          과세년월 = kwasekikan[:4] + "년" + str(int(kwasekikan[-2:])) + "월"
          merge_query = (
              "MERGE 법인세전자신고2 AS A "
              "USING (SELECT %s AS 과세년월, %s AS 사업자번호) AS B "
              "ON A.과세년월 = B.과세년월 AND A.사업자번호 = B.사업자번호 "
              "WHEN MATCHED THEN UPDATE SET 사용자ID = %s;"
          )
          cursor.execute(merge_query, [과세년월, biz_no, userID])
  memuser = get_object_or_404(MemUser, biz_no=biz_no)
  seq_no = memuser.seq_no
  return JsonResponse({"success": True, "userID": userID, "seq_no": seq_no})

#전자신고 접수번호 저장 - 클립보드 타입
def save_clipboard_Corp(request):
  if request.method == 'POST':
    clipboardData   = request.POST.get("clipboardData")
    if clipboardData:
      fields = [field.strip() for field in clipboardData.split('\t')]
      wcKwase = fields[0]      # 0:2023년12월
      wcCorpGB = fields[1]    # 1:법인세 일반정기확정(내국세,농특세) 신고서
      wcSingoGB = fields[2]   # 2:정기(확정)
      wcChojung = fields[3]   # 3:기한후신고
      wcSangho = fields[4]    # 4:주식회사 지에스디테크
      wcBizNo = fields[5]     # 5:677-87-01488
      wcJupsuWay = fields[6]  # 6:인터넷(변환)
      wcIssueT = fields[7]    # 7:2025-02-13 16:55:44
      wcJubsuNum = fields[8]  # 8:125-2025-2-504388903630
      wcJupsuGB = fields[9]   # 9:접수서류 18종

      with connection.cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM 법인세전자신고2 WHERE 과세년월='{wcKwase}' AND 사업자번호='{wcBizNo}'")
        row_count = cursor.fetchone()[0]
        if row_count > 0:
          sql_to_execute = f"DELETE FROM 법인세전자신고2 WHERE 과세년월='{wcKwase}' AND 사업자번호='{wcBizNo}'"
          #print(sql_to_execute)
          cursor.execute(sql_to_execute)
        str_ins = (
          "INSERT INTO 법인세전자신고2 VALUES ("
          f"'{wcKwase}', "
          f"'{wcCorpGB}', "
          f"'{wcSingoGB}', "
          f"'{wcChojung}', "
          f"'{wcSangho}', "
          f"'{wcBizNo}', "
          f"'{wcJubsuNum}', "
          f"'{wcIssueT}', "
          f"'{wcJupsuGB}', "
          "''"  # 마지막 값은 빈 문자열 (사용자ID 추가 필드 등)
          ")"
        )
        print(str_ins)
        try:
          cursor.execute(str_ins)
          return JsonResponse({"status": "success", "message": "저장완료"}, status=200)
        except:
          return JsonResponse({"error": "맨 앞에는 공백이 없어야 해요"}, status=500)

  return JsonResponse({"error": "Invalid request method"}, status=400)

# tbl_corporate2 테이블 업데이트
def mng_corp_update(request):
  if request.method == 'POST':
    seq_no   = request.POST.get("seq_no")
    target   = request.POST.get("target")
    work_YY = request.POST.get("work_YY")
    workmonth = 3
    val      = unquote(request.POST.get("val"))
    today = datetime.date.today().isoformat()        
    # target의 마지막 문자가 '6' 또는 '7'인 경우, val을 boolean 값에 따라 "1" 또는 "0"으로 변경
    if target and target[-1] in ("6", "7"):
      val = "1" if val in ["1", "true", True] else "0"
    if target and target[-2:] in ("10", "12"):
       val = val[:10]
    if target and target[-2:] in ("11", "13", "14", "15"):
       val = "1" if val in ["1", "true", True] else "0"
    # 커서 생성
    with connection.cursor() as cursor:
      cursor.execute("""
          SELECT COUNT(*) FROM tbl_corporate2 WHERE seq_no=%s AND work_YY=%s
      """, [seq_no, work_YY])
      row_count = cursor.fetchone()[0]
      print(row_count)
      if row_count > 0:
        val = val.replace(",","")
        sql_to_execute = f"UPDATE tbl_corporate2 SET {target}='{val}' WHERE seq_no={seq_no} AND work_YY={work_YY}"
        print(sql_to_execute)
        cursor.execute(sql_to_execute)
        
        if target=="YN_7" :
          if val=='1':
            sql_to_execute = f"UPDATE tbl_corporate2 SET YN_10='{today}' WHERE seq_no={seq_no} AND work_YY={work_YY}"
          else:  
            sql_to_execute = f"UPDATE tbl_corporate2 SET YN_10='' WHERE seq_no={seq_no} AND work_YY={work_YY}"
          print(sql_to_execute)
          cursor.execute(sql_to_execute)
        if target=="YN_11":
          if val=='1':
            sql_to_execute = f"UPDATE tbl_corporate2 SET YN_12='{today}' WHERE seq_no={seq_no} AND work_YY={work_YY}"
          else:  
            sql_to_execute = f"UPDATE tbl_corporate2 SET YN_12='' WHERE seq_no={seq_no} AND work_YY={work_YY}"
          print(sql_to_execute)
          cursor.execute(sql_to_execute)
        
        return JsonResponse({"status": "success", "message": " 업데이트"}, status=200)          

      else:

        sql_to_execute = f"INSERT INTO tbl_corporate2 (seq_no, work_YY, YN_1, YN_2, YN_3, YN_4, YN_5, YN_6, YN_7, YN_8, YN_9, YN_10, YN_11, YN_12, YN_13, YN_14, YN_15) VALUES ({seq_no}, {work_YY}"
                
        # target의 밑줄("_") 뒤의 모든 숫자를 정수로 변환 (예: "YN_6"이면 6, "YN_10"이면 10)
        target_field_num = int(target.split('_')[-1])

        # YN_1부터 YN_15까지 값을 순차적으로 추가
        for j in range(1, 16):  # 만약 15까지 포함하려면 range(1, 16)을 사용합니다.
            if j == target_field_num:
                # VBScript에서는 j가 9일 경우 따옴표를 추가하는 차이가 있으므로 그대로 재현
                if j==9 or j==10 or j==12:
                    sql_to_execute += f",'{val}'"
                else:
                    sql_to_execute += f",{val}"
            else:
                sql_to_execute += ",0"
        sql_to_execute += ")"
        print(sql_to_execute)
        cursor.execute(sql_to_execute)
        return JsonResponse({"status": "success", "message": "인서트"}, status=200)

  return JsonResponse({"error": "Invalid request method"}, status=400)

# 통장입력현황
def mng_corp_bank(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')
  request.session['ADID'] = ADID  
  request.session.save()

  work_YY = request.GET.get('work_YY', '')
  
  today = datetime.datetime.now()

  current_month = today.month
  current_day = today.day
  if current_day >= 25:  # 공휴일 감안
    work_mm = current_month
  else:
    work_mm = current_month - 1 if current_month > 1 else 12

  if not work_YY:
    if int(work_mm) <= 4 :
      work_YY = today.year - 1
    else:
      work_YY = today.year

  request.session['workyearCorp'] = work_YY

  if request.method == 'GET':
    s_sql = " order by  b.biz_manager,a.biz_name"
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}' order by a.biz_name"

    sql_query = f"""
      SELECT 
          b.biz_manager as groupManager,
          a.seq_no ,          
          a.biz_name,
          -- 월별 데이터 PIVOT으로 변환
          ISNULL(jan.[1], 0) AS 'YN_1',
          ISNULL(jan.[2], 0) AS 'YN_2',
          ISNULL(jan.[3], 0) AS 'YN_3',
          ISNULL(jan.[4], 0) AS 'YN_4',
          ISNULL(jan.[5], 0) AS 'YN_5',
          ISNULL(jan.[6], 0) AS 'YN_6',
          ISNULL(jan.[7], 0) AS 'YN_7',
          ISNULL(jan.[8], 0) AS 'YN_8',
          ISNULL(jan.[9], 0) AS 'YN_9',
          ISNULL(jan.[10], 0) AS 'YN_10',
          ISNULL(jan.[11], 0) AS 'YN_11',
          ISNULL(jan.[12], 0) AS 'YN_12',
          ISNULL(jan.[13], 0) AS 'YN_13',
          isnull(AdditionDC_JBcnt,0) as 'Jebon',
          ISNULL(bigo.bigo, '') AS bigo
      FROM 
          mem_user a
          INNER JOIN mem_deal b 
              ON a.seq_no = b.seq_no
          INNER JOIN mem_admin c 
              ON b.biz_manager = c.admin_id
          INNER JOIN tbl_discount J 
              ON a.seq_no = J.seq_no              
          -- 월별 데이터를 PIVOT으로 가져오기
          OUTER APPLY (
              SELECT *
              FROM (
                  SELECT work_MM, yn_9
                  FROM tbl_mng_jaroe
                  WHERE seq_no = a.seq_no 
                    AND work_yy = '{work_YY}'
              ) AS src
              PIVOT (
                  MAX(yn_9) 
                  FOR work_MM IN ([1], [2], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12], [13])
              ) AS pvt
          ) AS jan
          -- bigo는 별도로 처리 
          OUTER APPLY (
              SELECT TOP 1 bigo
              FROM tbl_mng_jaroe
              WHERE seq_no = a.seq_no 
                AND work_yy = '{work_YY}'
                AND work_mm =''
          ) AS bigo
      WHERE 
          a.duzon_ID <> '' 
          AND a.biz_type IN ('1', '2') 
          AND b.keeping_YN = 'Y' 
          AND a.Del_YN <> 'Y'
          {s_sql};
        """
    # print(sql_query)
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
  
@csrf_exempt  
def get_discount_data(request):
    """ tbl_Discount에서 데이터를 조회하여 JSON 응답 반환 (POST 방식) """
    if request.method == "POST":

      data = json.loads(request.body)  # JSON 데이터 파싱
      seq_no = data.get("seq_no")  # seq_no 가져오기
      response_data = {}
      with connection.cursor() as cursor:
          cursor.execute("SELECT seq_no, isnull(AdditionDC_JBCnt,0) AdditionDC_JBCnt, isnull(AdditionDC_Stnd,0) AdditionDC_Stnd, isnull(AdditionDC_YJ,0) AdditionDC_YJ, isnull(AdditionDC_Ddct,0) AdditionDC_Ddct "
                         ",isnull(SAddition_Rsn,'') SAddition_Rsn ,isnull(OAddition_Rsn,'') OAddition_Rsn,isnull(FAddition_Rsn,'') FAddition_Rsn"
                         ",isnull(SAddition_Amt,0) SAddition_Amt,isnull(OAddition_Amt,0) OAddition_Amt,isnull(FAddition_Amt,0) FAddition_Amt "
                         "FROM tbl_Discount WHERE seq_no = %s", [seq_no])
          row = cursor.fetchone()
          if row:
            response_data = {
                "seq_no": seq_no,
                "AdditionDC_JBCnt": row[1],
                "AdditionDC_Stnd": row[2],
                "AdditionDC_YJ": row[3],
                "AdditionDC_Ddct": row[4],
                "SAddition_Rsn":row[5],
                "OAddition_Rsn":row[6],
                "FAddition_Rsn":row[7],
                "SAddition_Amt":row[8],
                "OAddition_Amt":row[9],
                "FAddition_Amt":row[10],
            }
            # print(response_data)
            
          else:
            response_data = {
                "seq_no": seq_no,
                "AdditionDC_JBCnt": 0,
                "AdditionDC_Stnd": 0,
                "AdditionDC_YJ": 0,
                "AdditionDC_Ddct": 0,
                "SAddition_Rsn":'',
                "OAddition_Rsn":'',
                "FAddition_Rsn":'',
                "SAddition_Amt":0,
                "OAddition_Amt":0,
                "FAddition_Amt":0,
            }
          return JsonResponse(response_data)
    return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)

@csrf_exempt
def check_yn8(request):
    """YN_8 값 확인 API"""
    if request.method == "POST":
        seq_no = request.POST.get("seq_no")
        work_YY = request.POST.get("work_YY")

        if not seq_no or not work_YY:
            return JsonResponse({"exists": False, "error": "Missing parameters"}, status=400)

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT YN_8 FROM tbl_corporate2 WHERE seq_no=%s AND work_YY=%s
            """, [seq_no, work_YY])
            row = cursor.fetchone()  # 데이터 가져오기

        exists = row is not None and row[0] is not None  # YN_8 값이 존재하는지 확인
        return JsonResponse({"exists": exists})

    return JsonResponse({"error": "Invalid request"}, status=405)

@csrf_exempt
@transaction.atomic
def update_discount_data(request):
    """tbl_Discount의 특정 seq_no 데이터를 직접 SQL 쿼리로 업데이트 또는 삽입"""
    if request.method != "POST":
        return JsonResponse({"error": "POST 요청만 허용됩니다."}, status=405)

    try:
        data = json.loads(request.body)  # JSON 데이터 파싱
        try:
            seq_no = int(data.get("seq_no"))  # seq_no를 숫자로 변환
        except (TypeError, ValueError):
            return JsonResponse({"error": "seq_no는 숫자여야 합니다."}, status=400)

        if not seq_no:
            return JsonResponse({"error": "seq_no 값이 없습니다."}, status=400)

        # 변경할 필드를 담을 리스트
        update_fields = []
        insert_columns = []
        insert_values = []
        params = []

        # 업데이트할 필드 처리
        field_mappings = {
            "AdditionDC_JBCnt": "AdditionDC_JBCnt",
            "AdditionDC_Stnd": "AdditionDC_Stnd",
            "AdditionDC_YJ": "AdditionDC_YJ",
            "AdditionDC_Ddct": "AdditionDC_Ddct",
            "SAddition_Rsn": "SAddition_Rsn",
            "SAddition_Amt": "SAddition_Amt",
            "OAddition_Rsn": "OAddition_Rsn",
            "OAddition_Amt": "OAddition_Amt",
            "FAddition_Rsn": "FAddition_Rsn",
            "FAddition_Amt": "FAddition_Amt",
        }

        for key, column in field_mappings.items():
            if key in data:
                update_fields.append(f"{column} = %s")
                insert_columns.append(column)
                insert_values.append("%s")
                params.append(data[key])

        if not update_fields:
            return JsonResponse({"error": "변경할 필드가 없습니다."}, status=400)

        # seq_no가 존재하는지 확인
        check_query = "SELECT COUNT(*) FROM tbl_Discount WHERE seq_no = %s"
        with connection.cursor() as cursor:
            cursor.execute(check_query, [seq_no])
            exists = cursor.fetchone()[0] > 0  # 존재하면 True

        if exists:
            # UPDATE 실행
            update_query = f"""
                UPDATE tbl_Discount
                SET {", ".join(update_fields)}
                WHERE seq_no = %s
            """
            params.append(seq_no)  # WHERE 조건 추가
            print(f"Update query: {update_query}")
            print(f"Params: {params}")
            with connection.cursor() as cursor:
                cursor.execute(update_query, params)
                # print(f"Executed query: {update_query}")
            
            return JsonResponse({"success": True, "message": "데이터가 성공적으로 업데이트되었습니다."})

        else:
            # INSERT 실행
            insert_query = f"""
                INSERT INTO tbl_Discount (seq_no, {", ".join(insert_columns)})
                VALUES (%s, {", ".join(insert_values)})
            """
            insert_params = [seq_no] + params  # seq_no 포함하여 삽입
            print(f"Insert query: {insert_query}")
            print(f"Insert params: {insert_params}")
            with connection.cursor() as cursor:
                cursor.execute(insert_query, insert_params)
                print(f"Executed query: {insert_params}")
            
            return JsonResponse({"success": True, "message": "데이터가 성공적으로 삽입되었습니다."})

    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 데이터"}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"데이터 처리 중 오류 발생: {str(e)}", "traceback": traceback.format_exc()}, status=500)

# 고용증대 여부 검토
def func_cntGoyoungIncrease(seq_no,work_YY,reg_date,fiscalMM):
  work_YY = int(work_YY)
  fiscalMM = int(fiscalMM)
  Increase_UsualEmp = 0
  sum_YoungworkMM_Now = 0
  sum_YoungworkMM_Pre = 0
  sangsi_MM_Pre = 0
  sangsi_MM_Now = 0

  if fiscalMM == 12:
      reg_year = int(reg_date[:4])
      if reg_year < work_YY:
          sangsi_MM_Now = 12
          sangsi_MM_Pre = 1
          if reg_year > (work_YY - 1):
              sangsi_MM_Pre = 12
          elif reg_year == (work_YY - 1):
              sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1
          else:
              sangsi_MM_Pre = 12
      elif reg_year == work_YY:
          sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1
          sangsi_MM_Pre = 1
      else:
          sangsi_MM_Now = 1
          sangsi_MM_Pre = 1
  else:
      if int(reg_date[:4]) < work_YY:
          if (work_YY - int(reg_date[:4])) == 1:
              sangsi_MM_Now = 12
              sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1 + fiscalMM
          elif (work_YY - int(reg_date[:4])) == 0:
              if int(reg_date[5:7]) > fiscalMM:
                  sangsi_MM_Now = 1
                  sangsi_MM_Pre = 1
              else:
                  sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1 + fiscalMM
                  sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1 + fiscalMM
          elif (work_YY - int(reg_date[:4])) > 1:
              sangsi_MM_Now = 12
              sangsi_MM_Pre = 12
      elif int(reg_date[:4]) == work_YY:
          if int(reg_date[5:7]) > fiscalMM:
              sangsi_MM_Now = 1
              sangsi_MM_Pre = 1
          else:
              sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1 - fiscalMM
              sangsi_MM_Pre = 1
      else:
          sangsi_MM_Now = 1
          sangsi_MM_Pre = 1

  endDate = "-12-31" if fiscalMM == 12 else f"-0{fiscalMM}-30"
  startDate = "-01-01" if fiscalMM == 12 else f"-0{12-fiscalMM+1}-01"

  sql_query = f"""
      SELECT empRegDate,empExitdate FROM tbl_Employ
      WHERE seq_no = %s AND empReject = ''
      AND YEAR(empRegDate) <= %s
      AND (empExitdate = '' OR YEAR(empExitdate) >= %s)
      ORDER BY empName
  """
  with connection.cursor() as cursor:
      cursor.execute(sql_query, (seq_no, work_YY, work_YY - 1))
      employees = cursor.fetchall()

  sum_workMM_Pre = 0
  sum_YoungworkMM_Pre = 0
  sum_workMM_Now = 0
  sum_YoungworkMM_Now = 0

  for emp in employees:
      ExitDate = emp[1].strip()
      EnterDate = emp[0].strip()

      if not ExitDate or ExitDate >= f"{work_YY}{endDate}":
          ExitDate = f"{work_YY}{endDate}"
          ExitDate_Pre = f"{work_YY-1}{endDate}"
      else:
          if fiscalMM == 12:
              if ExitDate >= f"{work_YY}{startDate}":
                  ExitDate_Pre = f"{work_YY-1}{endDate}"
              else:
                  ExitDate = f"{work_YY}{startDate}"
                  ExitDate_Pre = (datetime.datetime.strptime(emp[1], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
          else:
              if ExitDate >= f"{work_YY-1}{startDate}":
                  ExitDate_Pre = f"{work_YY-1}{endDate}"
              else:
                  ExitDate_Pre = (datetime.datetime.strptime(emp[1], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

      workMM_Pre = max(0, min(12, abs((datetime.datetime.strptime(ExitDate_Pre, "%Y-%m-%d").year - int(EnterDate[:4])) * 12 + (datetime.datetime.strptime(ExitDate_Pre, "%Y-%m-%d").month - int(EnterDate[5:7])))))
      workMM_Now = max(0, min(12, abs((datetime.datetime.strptime(ExitDate, "%Y-%m-%d").year - int(EnterDate[:4])) * 12 + (datetime.datetime.strptime(ExitDate, "%Y-%m-%d").month - int(EnterDate[5:7])))))

      sum_workMM_Pre += workMM_Pre
      sum_workMM_Now += workMM_Now

  Increase_YoungEmp = round(sum_YoungworkMM_Now / sangsi_MM_Now, 2) - round(sum_YoungworkMM_Pre / sangsi_MM_Pre, 2)

  if Increase_YoungEmp > (round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)):
      Increase_YoungEmp = round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)

  if Increase_YoungEmp < 0:
      Increase_YoungEmp = 0

  Increase_UsualEmp = round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)

  # print(f"Increase_YoungEmp: {Increase_YoungEmp}")
  # print(f"Increase_UsualEmp: {Increase_UsualEmp}")   
  return (Increase_YoungEmp+Increase_UsualEmp)

def func_isKWAMIL(region):
  isKWAMIL = ""
  arrKWAMIL = ["서울", "인천", "의정부", "구리", "하남", "고양", "수원", "성남", "안양",
                "부천", "광명", "과천", "의왕", "군포", "시흥", "호평동", "평내동",
                "금곡동", "일패동", "이패동", "삼패동", "가운동", "수석동", "지금동", "도농동"]
  notKWAMIL = ["강화", "옹진", "대곡", "불로", "마전", "금곡", "오류", "왕길", "당하", "원당", "남동"]
  
  for kw in arrKWAMIL:
      if kw in region:
          isKWAMIL = "Y"
          for nw in notKWAMIL:
              if region.startswith("인천") and nw in region:
                  isKWAMIL = ""
  return isKWAMIL

def func_isSpecialDeductUpjong(upJong):
  isSpecialDeduct = "Y"
  arrSpecial = ["작물재배", "작물", "재배", "축산업", "어업", "광업",
                "도매", "소매", "도소매",
                 
                 "하수", "폐기물","원료재생", "재활용", "환경복원", 
                "제조업", "건설업", "정보통신공사", "전기통신업",

                "물류산업", "신성장", #세부 업종 추가 판단

                "여객운송업", "출판업", "영상", "오디오", "배급업", "방송업",  "프로그래밍",
                "시스템 통합", "소프트웨어", "프로그램", "정보서비스업", "연구개발업", "고업", "전문과학",
                "과학기술서비스업", "포장 및 충전업", "포장", "충전", "전문디자인업", "창작", "예술",
                "수탁생산업", "엔지니어링",  "직업기술", "자동차정비공장", "선박관리업",
                "의료기관 운영사업", "관광사업", "노인복지시설", "전시산업", "인력공급", "직업소개",
                "고용알선", "콜센터", "텔레마케팅", "에너지절약", "재가장기요양기관", "청소업",
                "경비", "경호", "시장조사", "여론조사", "사회복지", "무형재산", "연구개발지원업", "간병",
                "사회교육시설", "직원훈련기관", "도서관", "사적지", "주택임대관리업", 
                "재생에너지", "신재생에너지", "보안시스템", "임업", "통관", "자동차임대업", "여행"]
  for item in arrSpecial:
      if item in upJong:
          isSpecialDeduct = "Y"
          break
  return isSpecialDeduct

def  func_isSmall(upJong,saleAmt):
  isSmall = ""
  if any(x in upJong for x in ["전기", "가스", "수도"]):
      isSmall = "Y" if saleAmt < 12000000000 else ""
  if any(x in upJong for x in ["인쇄", "농업", "광업", "건설업","육상", "수상", "항공", "운송","운수", "화물", "퀵", "택배", "보관업", "창고업",
                "화물운송", "화물포장", "화물검수", "계량", "예선", "도선", "파렛트", "기계임대", "장비임대"]):
      isSmall = "Y" if saleAmt < 8000000000 else ""
  if "제조" in upJong:
      arr120Jejo = ["식료품", "음료", "의복", "가죽", "가방", "신발", "연탄", "코크스", "석유",
                      "화학물질", "의료용물질", "비금속", "광물", "금속", "전자부품", "컴퓨터",
                      "음향", "영상", "통신장비", "전기장비", "기계", "가구", "자동차", "트레일러",
                      "수도", "가스", "증기"]
      found = False
      for item in arr120Jejo:
          if item in upJong:
              isSmall = "Y" if saleAmt < 12000000000 else ""
              found = True
              break
      if not found:
          isSmall = "Y" if saleAmt < 8000000000 else ""
  if any(x in upJong for x in ["도매", "소매", "도소매", "출판", "영상", "방송", "방송통신", "정보서비스"]):
      isSmall = "Y" if saleAmt < 5000000000 else ""
  if any(x in upJong for x in ["인력공급", "직업소개", "고용알선", "콜센터", "텔레마케팅", "부동산",
                                "하수도", "폐기물 재상", "전문 과학", "전문과학", "사업시설", "사업지원",
                                "전문디자인업", "창작", "예술"]):
      isSmall = "Y" if saleAmt < 3000000000 else ""
  if isSmall == "":
      isSmall = "Y" if saleAmt < 1000000000 else ""
  return isSmall

def func_isKnowledge(upJong):
  isKnowledge = ""
  arrKnowledge = ["엔지니어링", "연구개발", "전기통신", "프로그래밍", "소프트웨어", "프로그램",
                  "시스템통합", "시스템관리", "영화", "방송", "전문디자인", "오디오", "원판녹음",
                  "광고물", "방송", "정보서비스", "출판", "창작", "예술", "인쇄출판", "경영컨설팅"]
  for item in arrKnowledge:
      if item in upJong:
          isKnowledge = "Y"
          break
  return isKnowledge

def func_isChangUp(upJong):
  isChangUp = ""
  arrChangUp = ["광업", "제조", "정보통신", "전문과학", "하수", "폐기물", "원료재생", "재활용",
                "환경복원", "건설업", "정보통신공사", "통신판매", "물류산업", "엔지니어링",
                "사업시설", "조경", "사업지원", "예술", "창작", "전문디자인업", "스포츠", "이용업",
                "미용업", "사회교육", "직원훈련", "직업기술", "과학기술서비스업", "전시산업",
                "노인복지", "간병", "관광사업", "여행", "숙박", "음식", "에너지", "창업보육센터",
                "통신판매", "금융"]
  notChangUp = ["세무사", "변호사", "변리사", "법무사", "회계사", "수의사", "행정사", "건축사",
                "감정평가사", "중개사", "블록체인", "뉴스제공", "감상실", "암호화폐", "암호화자산",
                "예술가", "오락", "유흥", "커피"]
  for item in arrChangUp:
    if item in upJong:
      isChangUp = "Y"
      break
  for item in notChangUp:
    if item in upJong:
      isChangUp = "N"
      break
  return isChangUp

def func_isMyulyu(upJong):
  isMyulyu = ""
  arrMyulyu = ["육상", "수상", "항공", "운송","운수", "화물", "퀵", "택배", "보관업", "창고업",
                "화물운송", "화물포장", "화물검수", "계량", "예선", "도선", "파렛트", "기계임대", "장비임대"]
  for item in arrMyulyu:
      if item in upJong:
          isMyulyu = "Y"
          break
  return isMyulyu

def func_isNewGroth(upJong):
  isNewGroth = ""
  arrNewGroth = ["엔지니어링", "연구개발", "전기통신", "정보서비스", "컴퓨터", "프로그래밍",
                  "소프트웨어", "프로그램", "시스템통합", "시스템관리", "영화", "방송",
                  "전문디자인", "보안시스템", "오디오", "원판녹음", "광고물", "방송", "정보서비스",
                  "출판", "창작", "예술", "인쇄출판", "경영컨설팅", "관광", "국제회의", "유원시설",
                  "관광객", "육상", "수상", "항공", "운송", "화물", "퀵", "택배", "보관업", "창고업",
                  "화물운송", "화물포장", "화물검수", "계량", "예선", "도선", "파렛트", "기계임대", "장비임대",
                  "전시산업", "시장조사", "여론조사", "광고업"]
  for item in arrNewGroth:
      if item in upJong:
          isNewGroth = "Y"
          break
  return isNewGroth

def func_ChangupDeduct(work_YY,kisu,isKWAMIL,isChangUpUpjong,isNewGroth,isVenture,saleAmt,reg_date,age):
  ChangUpDeduct = "N"
  ChangUpDeductRate = 0  
  if kisu is not None:
    if kisu < 6 and isChangUpUpjong == "Y" and isKWAMIL == "":
        ChangUpDeductRate = 50;ChangUpDeduct = "Y"
    if kisu < 6 and isChangUpUpjong == "Y" and (age > 0 and age < 36):
        ChangUpDeductRate = 100 if isKWAMIL == "" else 50
        ChangUpDeduct = "Y"
    if isChangUpUpjong == "Y" and isKWAMIL == "" and isNewGroth == "Y" and kisu is not None and kisu <= 3 and ChangUpDeductRate <= 50:
        ChangUpDeductRate = 75;ChangUpDeduct = "Y"
    if isVenture == "Y":
        ChangUpDeductRate = 50;ChangUpDeduct = "Y"
    # 소규모창업 (조특법 제6항)
    isLittle = ""
    reSale = saleAmt
    try:
        reg_dt = datetime.strptime(reg_date, "%Y-%m-%d")
        reg_year = reg_dt.year
        reg_month = reg_dt.month
    except Exception:
        reg_year, reg_month = 0, 0
    if reg_year == int(work_YY) and saleAmt > 0:
        reSale = saleAmt * 12 / (12 - reg_month + 1)
    if kisu < 6 and (isChangUpUpjong == "Y" ):
        if reg_date >= "2018-05-29" and reSale <= 48000000:
            isLittle = "Y";ChangUpDeduct = "Y"
            ChangUpDeductRate = 50 if isKWAMIL == "Y" else 100
        if reg_year >= 2022 and reSale <= 80000000:
            isLittle = "Y";ChangUpDeduct = "Y"
            ChangUpDeductRate = 50 if isKWAMIL == "Y" else 100
    #최종판단
    if ChangUpDeductRate==0:
      ChangUpDeduct = "N"  
  return ChangUpDeductRate,ChangUpDeduct ,isLittle

def func_SpecialDeduct(upJong,isSpecialUpjong,isRural,isSmall):
  SpecialDeductRate = 0;SpecialDeduct = "N"
  # 도매소매의료 여부
  isDoSoMedi = "Y" if any(x in upJong for x in ["도매", "소매", "도소매", "의료"]) else ""  
  if isSpecialUpjong == "Y":
    # 지방인 경우 - 중기업도 감면적용
    if isRural == "Y":  
        if isSmall == "Y":# 소기업인 경우/중기업 아님
            SpecialDeductRate = 10 if isDoSoMedi == "Y" else 30
            SpecialDeduct = "Y"
        else:
            SpecialDeductRate = 5 if isDoSoMedi == "Y" else 15
            SpecialDeduct = "Y"
    # 수도권인 경우 중기업은 감면 안됨 / 소기업만 적용
    else:  
        if isSmall == "Y":
            SpecialDeductRate = 10 if isDoSoMedi == "Y" else 20
            SpecialDeduct = "Y"
        # 수도권 중기업 지식기반산업 규정은 23년 귀속부터 폐지하였다
        # else:
        #     if isKnowledge == "Y":
        #         SpecialDeductRate = 10;SpecialDeduct = "Y"    
    #최종판단
    if SpecialDeductRate==0:
      SpecialDeduct = "N"  
  return SpecialDeductRate,SpecialDeduct
#cursor를 받아서 컬럼명과 함께 dict를 반환한다 "Return all rows from a cursor as a dict"
def dict_fetchall(cursor):
  columns = [col[0] for col in cursor.description]
  return [
      {col: (value.strip() if isinstance(value, str) else value) for col, value in zip(columns, row)}
      for row in cursor.fetchall()
  ]
