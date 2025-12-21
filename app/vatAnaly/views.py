from __future__ import print_function 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
from app.models import userProfile
import os
import natsort
import time
import datetime
from app.models import MemUser
from app.models import MemAdmin
from app.models import MemDeal
from pdf2image import convert_from_path

from pdf2image import convert_from_path
import glob
from PIL import Image

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

@login_required(login_url="/login/")
def index(request):
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if memuser.biz_type<4:
    context['isCorp'] = True
  if userprofile:
    userprofile = userprofile.latest('description')
  if userprofile is not None:
    context['userProfile'] = userprofile
  
  context['memuser'] = memuser
  getTotalIssueList(memuser,context)
  return render(request, "vat/vatAnaly.html",context)


def getTotalIssueList(memuser, context):
    t0 = time.perf_counter()
    print("\n[VAT][getTotalIssueList] START")
    print(f"[VAT] seq_no={memuser.seq_no}, biz_no={memuser.biz_no}, biz_type={memuser.biz_type}")

    def safe_slice(val, a, b):
        """val이 None이거나 문자열 길이가 짧아도 안전하게 슬라이스"""
        if val is None:
            return ""
        s = str(val)
        if len(s) < a:
            return ""
        return s[a:b]

    # biz_type에 따라 카드합계 계산 CASE 분기
    if memuser.biz_type < 4:
        card_sum_case = """
            Sum((
                CASE
                    WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN CASE WHEN b.stnd_gb = '1' THEN splCft ELSE 0 END
                    WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN CASE WHEN b.stnd_gb = '2' THEN splCft ELSE 0 END
                    WHEN LTRIM(a.과세유형) = 'C17' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN CASE WHEN b.stnd_gb = '3' THEN splCft ELSE 0 END
                    WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN CASE WHEN b.stnd_gb = '4' THEN splCft ELSE 0 END
                END
            )) AS 카드합계
        """
        biz_type_filter = "c.biz_type < 4"
    else:
        card_sum_case = """
            Sum((
                CASE
                    WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '1' THEN CASE WHEN b.stnd_gb IN ('1','2') THEN splCft ELSE 0 END
                    WHEN LTRIM(a.과세유형) = 'C07' AND SUBSTRING(LTRIM(A.과세기간), 7, 1) = '2' THEN CASE WHEN b.stnd_gb IN ('3','4') THEN splCft ELSE 0 END
                END
            )) AS 카드합계
        """
        biz_type_filter = "c.biz_type > 3"

    sql = f"""
    WITH STT AS (
        SELECT
            a.사업자등록번호,
            a.과세기간,
            LTRIM(a.과세유형) AS 과세유형,
            {card_sum_case}
        FROM 부가가치세전자신고3 A WITH (NOLOCK)
        LEFT OUTER JOIN TBL_HOMETAX_SCRAP B WITH (NOLOCK)
            ON a.사업자등록번호 = b.biz_no
           AND LEFT(a.과세기간, 4) = b.tran_YY
        WHERE a.사업자등록번호 = %s
          AND a.과세유형 <> ''
          AND a.사업자등록번호 IN (
              SELECT biz_no
              FROM mem_user C WITH (NOLOCK)
              WHERE a.사업자등록번호 = c.biz_no
                AND {biz_type_filter}
          )
        GROUP BY a.사업자등록번호, a.과세기간, LTRIM(a.과세유형)
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
        b.카드합계 AS 카드현영사용총액
    FROM 부가가치세전자신고3 A
    JOIN STT B
      ON A.사업자등록번호 = B.사업자등록번호
     AND A.과세기간 = B.과세기간
     AND A.과세유형 = B.과세유형
    ORDER BY a.과세기간 DESC, a.신고구분 DESC, a.신고시각 DESC, a.과세유형
    """

    params = [memuser.biz_no]
    print("[VAT] SQL PARAMS:", params)
    print("[VAT] SQL (head 400 chars):", sql[:400].replace("\n", " "))

    total_list = []
    try:
        with connection.cursor() as cursor:
            q0 = time.perf_counter()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            print(f"[VAT] DB fetch rows={len(rows)} elapsed={time.perf_counter()-q0:.3f}s")

        # rows가 있으면 샘플 로그
        if rows:
            print("[VAT] first row sample (0..5 cols):", rows[0][:6])

        for i, r in enumerate(rows or []):
            # r[0]=과세기간, r[1]=과세유형
            wcCorpGB_txt = "확정" if r[1] in ("C03", "C07") else ("예정" if r[1] in ("C13", "C17") else "")
            tmpKi = (r[0][6:7] if (r[0] and len(r[0]) >= 7) else "")
            work_qt = ""
            startDt, endDt = "", ""

            if r[1] == "C03":
                startDt, endDt = "1월 1일", "12월 31일"
            elif r[1] == "C13":
                startDt, endDt = "1월 1일", "6월 30일"
            elif r[1] == "C07":
                if memuser.biz_type < 4:
                    startDt, endDt, work_qt = ("4월 1일", "6월 30일", "2분기") if tmpKi == "1" else ("10월 1일", "12월 31일", "4분기")
                else:
                    startDt, endDt, work_qt = ("1월 1일", "6월 30일", "상반기") if tmpKi == "1" else ("7월 1일", "12월 31일", "하반기")
            elif r[1] == "C17":
                startDt, endDt, work_qt = ("1월 1일", "3월 31일", "1분기") if tmpKi == "1" else ("7월 1일", "9월 30일", "3분기")

            # 숫자 None 대비
            actual_pay = int(r[16] or 0)
            예정세액 = int(r[17] or 0)

            row = {
                "과세기간": (r[0] or "") + wcCorpGB_txt,
                "과세유형": r[1],
                "매출세금계산서": r[2],
                "매출세금계산서세액": r[3],
                "카드매출": r[4],
                "기타매출": r[5],
                "영세율매출": r[6],
                "매입세금계산서": r[7],
                "매입세금계산서세액": r[8],
                "기타매입": r[9],
                "기타매입세액": r[10],
                "불공제": r[11],
                "불공제세액": r[12],
                "경감공제세액": r[13],
                "면세매출": r[14],
                "면세매입": r[15],
                "실제납부할세액": actual_pay,
                "예정세액": 예정세액,
                "납부세액": actual_pay + 예정세액,
                "매입세금계산서수취고정자산금액": r[18],
                "매출합계": r[19],
                "매입합계": r[20],

                # 원본이 문자열/바이너리/None일 수 있으니 안전 슬라이스
                "신용카드수취기타카드": safe_slice(r[21], 60, 73),
                "신용카드수취현금영수증": safe_slice(r[22], 60, 73),
                "신용카드수취화물복지": safe_slice(r[23], 60, 73),
                "신용카드수취사업용카드": safe_slice(r[24], 60, 73),

                "공제받지못할매입세액명세": r[25],
                "의제매입세액공제": safe_slice(r[26], 40, 54),
                "재활용폐자원등매입세액": safe_slice(r[27], 40, 54),

                "납부환급세액": r[28],
                "매입세금계산서수취고정자산세액": r[29],
                "산출세액": r[30],
                "가산세액계": r[31],

                "카드현영사용총액": str(r[32] or 0),

                "startDt": startDt,
                "endDt": endDt,
                "seq_no": memuser.seq_no,
                "work_YY": (r[0][:4] if r[0] else ""),
                "work_QT": work_qt,
            }

            # 너무 많은 로그 방지: 처음 3개만 상세 출력
            if i < 3:
                print(f"[VAT] row[{i}] 과세기간={row['과세기간']} 과세유형={row['과세유형']} 납부세액={row['납부세액']} work_QT={row['work_QT']}")

            total_list.append(row)

    except Exception as e:
        print("[VAT][ERROR] getTotalIssueList 실패:", e)
        total_list = []

    context["totIssueList"] = total_list
    print(f"[VAT][getTotalIssueList] END rows={len(total_list)} elapsed={time.perf_counter()-t0:.3f}s\n")



@csrf_exempt
def getTraderList(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  seq_no = request.GET.get('seq_no',False)
  work_YY = request.GET.get('work_YY',False)
  period = request.GET.get('period',False)
  youhyung = request.GET.get('youhyung',False)
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
    select AA.trader_code
        , AA.trader_name
        , AA.total_amount
        , AA.supply_amount
        , AA.tax_amount
      from (
          SELECT isnull(( select trader_code  from DS_SlipLedgr2 with (nolock)
                        where seq_no = '{seq_no}'  and  work_yy = '{int(work_YY)-1}'  
                          and Trader_Bizno = e.공급받는자사업자등록번호  
                          and seq_no = e.SEQ_NO
                        group by trader_code ), '')   AS trader_code,  
                MAX(e.공급받는자상호)     AS trader_name,        
                SUM(e.합계금액)          AS total_amount,   
                SUM(e.공급가액)          AS supply_amount,
                SUM(e.세액)              AS tax_amount
            FROM 전자세금계산서   e  with (nolock) 
            WHERE e.seq_no = '{seq_no}'
              AND e.매입매출구분 in ('1','3') 
              AND e.작성일자 BETWEEN '{work_YY}-{startDt}' AND '{work_YY}-{endDt}'
            GROUP BY e.SEQ_NO, e.공급받는자사업자등록번호
    )  AA
    WHERE AA.trader_code <> '' 
    ORDER BY total_amount DESC
  """
  totSaleArr = []

  with connection.cursor() as cursor:
      # ✅ 1차 쿼리 실행
      cursor.execute(sql_main, [seq_no, work_YY, startDt, endDt])
      rows = cursor.fetchall()

      # ✅ 결과 없으면 fallback 쿼리 실행
      if not rows:
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
     select AA.trader_code
        , AA.trader_name
        , AA.total_amount
        , AA.supply_amount
        , AA.tax_amount
      from (
          SELECT isnull(( select trader_code  from DS_SlipLedgr2 with (nolock)
                        where seq_no = '{seq_no}'  and  work_yy = '{int(work_YY)-1}'  
                          and Trader_Bizno = e.공급자사업자등록번호  
                          and seq_no = e.SEQ_NO
                        group by trader_code ), '')   AS trader_code,  
                MAX(e.공급자상호)     AS trader_name,        
                SUM(e.합계금액)          AS total_amount,   
                SUM(e.공급가액)          AS supply_amount,
                SUM(e.세액)              AS tax_amount
            FROM 전자세금계산서   e  with (nolock) 
            WHERE e.seq_no = '{seq_no}'
              AND e.매입매출구분 in ('2','4') 
              AND e.작성일자 BETWEEN '{work_YY}-{startDt}' AND '{work_YY}-{endDt}'
            GROUP BY e.SEQ_NO, e.공급자사업자등록번호
    )  AA
    WHERE AA.trader_code <> '' 
    ORDER BY total_amount DESC
  """
  totCostArr = []

  with connection.cursor() as cursor:
      # ✅ 1차 쿼리 실행
      cursor.execute(sql_main_Cost)
      rows = cursor.fetchall()

      # ✅ 결과 없으면 fallback 쿼리 실행
      if not rows:
          cursor.execute(sql_fallback_Cost)
          rows = cursor.fetchall()

  # ✅ 결과를 JSON 형태로 변환
  totCostArr = [
      {'거래처코드': r[0], '거래처명': r[1], '금액': float(r[3] or 0)}
      for r in rows
  ]

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
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
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

# 거래처 클릭시 모달 그래프
def get_QuarteredGraph(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  seq_no = memuser.seq_no
  trader_code = request.GET.get("trader_code")  # 특정 매출처
  trader_flag = request.GET.get("trader_flag")  # 매출처? 매입처?
  today = datetime.datetime.now()   # ✅ 오늘 날짜와 시간
  current_year = today.year         # ✅ 연도만 추출
  years = [str(current_year - i) for i in range(4, -1, -1)]  # 최근 5개년
  flag_TranAmt = "TranAmt_Dr"
  if trader_flag=="cost": flag_TranAmt = "TranAmt_Cr"

  sql = f"""
      SELECT 
          Work_YY AS year,
          CASE 
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 1 AND 3 THEN 'Q1'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 4 AND 6 THEN 'Q2'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 7 AND 9 THEN 'Q3'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 10 AND 12 THEN 'Q4'
          END AS quarter,
          SUM({flag_TranAmt}) AS total_amount
      FROM DS_SlipLedgr2
      WHERE seq_no = {seq_no}
        AND Trader_Code = %s
        AND Work_YY IN ({','.join(['%s'] * 5)})
        and tran_dt<>'00-00'	
        AND Tran_Stat = '매입매출전표'
      GROUP BY Work_YY,
          CASE 
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 1 AND 3 THEN 'Q1'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 4 AND 6 THEN 'Q2'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 7 AND 9 THEN 'Q3'
              WHEN CAST(SUBSTRING(Tran_Dt, 1, 2) AS INT) BETWEEN 10 AND 12 THEN 'Q4'
          END
      ORDER BY Work_YY, quarter
  """

  params = [trader_code] + years
  with connection.cursor() as cursor:
      cursor.execute(sql, params)
      rows = cursor.fetchall()

  # 👉 연도별 Q1~Q4 초기화
  data = {year: {"Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0} for year in years}

  for row in rows:
      year, quarter, total_amount = row
      data[year][quarter] = float(total_amount)

  # 👉 JSON 형식 변환
  json_result = [
      {"year": year, **data[year]} for year in years
  ]

  return JsonResponse(json_result, safe=False)

# 월별 비교그래프
@csrf_exempt
def get_monthly_comparison(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  seq_no = memuser.seq_no
  trader_code = request.GET.get("trader_code")
  trader_flag = request.GET.get("trader_flag")  # 매출처? 매입처?
  flag_TranAmt = "TranAmt_Dr"
  if trader_flag=="cost": flag_TranAmt = "TranAmt_Cr"
  # 올해, 작년 기준 연도 계산
  today = datetime.date.today()
  this_year = today.year
  last_year = this_year - 1

  # 📌 DS_SlipLedgr2 테이블에서 월별 매출 합계 가져오기
  sql = f"""
      SELECT LEFT(Tran_Dt, 2) AS month,
              SUM(CASE WHEN Work_YY = {this_year} THEN {flag_TranAmt} ELSE 0 END) AS thisYear,
              SUM(CASE WHEN Work_YY = {last_year} THEN {flag_TranAmt} ELSE 0 END) AS lastYear
      FROM DS_SlipLedgr2
      WHERE seq_no = %s AND trader_code = %s AND Tran_Stat='매입매출전표' and tran_dt<>'00-00'	
      GROUP BY LEFT(Tran_Dt, 2)
      ORDER BY month
  """
  cursor = connection.cursor()
  cursor.execute(sql, [seq_no, trader_code])
  rows = cursor.fetchall()
  connection.close()

  # 📌 JSON 형태로 가공
  data = []
  for row in rows:
      data.append({
          "month": f"{int(row[0])}월",
          "thisYear": int(row[1] or 0),
          "lastYear": int(row[2] or 0)
      })

  return JsonResponse(data, safe=False)