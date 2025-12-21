import json
import datetime
import copy
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
# from app.models import TblHometaxSaleexport
# from app.models import TblHometaxSalett
# from app.models import TblHometaxCashcost
from django.db import models,transaction

from django.db.models import Q

from admins.utils import send_kakao_notification,kijang_member_popup,sendKakao_Bulk

@login_required(login_url="/login/")
def index(request):
    context = {}
    admin_grade     = request.session.get('Admin_Grade')
    admin_biz_level = request.session.get('Admin_Biz_Level')
    admin_biz_area  = request.session.get('Admin_Area')
    admin_id        = request.session.get('Admin_Id')
    ADID = request.GET.get("ADID", "")
    flag = request.GET.get("flag", "")
    template_menu = ""
    grid_title = ""
    if flag == "Card":
        template_menu = 'admin/scrap_card_list.html'
        grid_title = '사업용 신용카드 공제설정'
    elif flag == "Mon":
        template_menu = 'admin/scrap_monthly_list.html'
        grid_title = "월별 스크래핑 결과발송"
    elif flag == "Qtr":
        template_menu = 'admin/scrap_quarter_list.html'
        grid_title = "분기별 부가세 예상세액 발송"
    context['gridTitle'] = grid_title

    arr_ADID = []

    if admin_grade != "SA":
        if admin_biz_level == "세무사":
            # Query for admin_id
            arr_ADID = MemAdmin.objects.filter(
                ~Q(grade="SA"),
                ~Q(biz_level="세무사"),
                ~Q(del_yn="y"),
                admin_area = admin_biz_area
            ).order_by('admin_id').values_list('admin_id', flat=True)
    else:  # admin_grade == "SA"
        arr_ADID = list(MemAdmin.objects.filter(
            ~Q(grade="SA"),
            ~Q(biz_level="세무사"),
            ~Q(del_yn="y")
        ).order_by("admin_id").values_list('admin_id', flat=True))
        arr_ADID.insert(0, "전체")
    if not ADID:
        ADID = request.session.get('ADID', "") 
    
    if not ADID:
        if ADID:
            targetIDno = arr_ADID.index(ADID) if ADID in arr_ADID else 0
        else:
            ADID = arr_ADID[0] if arr_ADID else ""
            targetIDno = 0

    context['admin_biz_level'] = admin_biz_level
    context['arr_ADID'] = json.dumps(list(arr_ADID))
    context['flag'] = flag
    context['ADID'] = ADID
    request.session['ADID'] = ADID  
    return render(request, template_menu,context)

# 분기별 - 예상세액 통보
def scrap_quarter_list(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')
  request.session['ADID'] = ADID  
  request.session.save()

  work_YY = request.GET.get('work_YY', '')
  work_mm = request.GET.get('work_mm', '')
  today = datetime.datetime.now()
  if not work_mm:
      current_month = today.month
      current_day = today.day
      if current_day >= 25:  # 공휴일 감안
        work_mm = current_month
      else:
        work_mm = current_month - 1 if current_month > 1 else 12

  if not work_YY:
    if int(work_mm) < 2 or int(work_mm) == 12:
      work_YY = today.year - 1
    else:
      work_YY = today.year

  request.session['workyearScrap'] = work_YY
  request.session['work_mm']  = work_mm
  cur_date = today.strftime('%Y%m%d')

  work_qt = None
  work_period = ""
  work_mm = int(work_mm)

  if work_mm <= 3:
      work_qt = 1
      work_period = f"작성일자>='{work_YY}-01-01' and 작성일자<='{work_YY}-03-31'"
  elif work_mm <= 6:
      work_qt = 2
      work_period = f"작성일자>='{work_YY}-04-01' and 작성일자<='{work_YY}-06-30'"
  elif work_mm <= 9:
      work_qt = 3
      work_period = f"작성일자>='{work_YY}-07-01' and 작성일자<='{work_YY}-09-30'"
  elif work_mm <= 12:
      work_qt = 4
      work_period = f"작성일자>='{work_YY}-10-01' and 작성일자<='{work_YY}-12-31'"

  request.session['work_qt'] = work_qt
  stnd_GB = work_qt
  if work_qt == 1:
      kwasekikan = f"{work_YY}년 1기"
      ks2 = "예정(정기)"
      SKGB = "C17"
  elif work_qt == 2:
      kwasekikan = f"{work_YY}년 1기"
      ks2 = "확정(정기)"
      SKGB = "C07"
  elif work_qt == 3:
      kwasekikan = f"{work_YY}년 2기"
      ks2 = "예정(정기)"
      SKGB = "C17"
  elif work_qt == 4:
      kwasekikan = f"{work_YY}년 2기"
      ks2 = "확정(정기)"
      SKGB = "C07"

  txtStnd_GB = " stnd_gb "
  if stnd_GB in [1, 3]:
      txtStnd_GB = f"{txtStnd_GB} ='{stnd_GB}'"
  elif stnd_GB in [2, 4]:
      txtStnd_GB = f"{txtStnd_GB} in ('{int(stnd_GB)-1}','{stnd_GB}')"

  searchMM = int(work_mm) + 1
  searchYY = int(work_YY)
  if int(work_mm) == 12:
      searchMM = 1
      searchYY = int(work_YY) + 1      

  if request.method == 'GET':
    s_sql = f" AND b.biz_manager = '{ADID}'"
    if ADID=="화물":s_sql += " and biz_type=4 "
    searchMM = work_mm + 1
    searchYY = work_YY
    if work_mm==12 : 
      searchMM = 1 
      searchYY = work_YY+1    
    sql_query = f"""
        SELECT a.seq_no AS sqno,a.biz_name,a.biz_type, ISNULL(tot_ddct, 0) AS tot_ddct,
               ISNULL((SELECT Acnt_Nm FROM Financial_AcntCd RIGHT OUTER JOIN scrap_each d  ON d.tot_acntcd = Acnt_Cd WHERE d.seq_no = a.seq_no), '소모품비') AS tot_acntcd,
               ISNULL(car_ddct, 0) AS car_ddct, ISNULL(car_class, '') AS car_class, 
               ISNULL((SELECT TOP 1 과세기수 FROM 부가가치세통합조회 WHERE 사업자등록번호 = a.biz_no AND 과세기수 = '{kwasekikan}' AND 신고구분 = '{ks2[:2]}'), '') AS YN_Tong,
               ISNULL((SELECT TOP 1 (매출신용카드공급가액 + 매출신용카드세액) FROM 부가가치세통합조회 WHERE 사업자등록번호 = a.biz_no AND 과세기수 = '{kwasekikan}'  AND 신고구분 = '{ks2[:2]}'), 0) AS YN_TongCardSale,
               ISNULL((SELECT TOP 1 (매출현금영수증공급가액 + 매출현금영수증세액) FROM 부가가치세통합조회 WHERE 사업자등록번호 = a.biz_no AND 과세기수 = '{kwasekikan}'  AND 신고구분 = '{ks2[:2]}'), -1) AS YN_TongCashSale,
               Isnull((select top 1 매출판매대행 from 부가가치세통합조회 Where 사업자등록번호=a.biz_no and 과세기수='{kwasekikan}' and 신고구분='{ks2[:2]}'),-1) as YN_TongDaehangSale ,
               ISNULL((SELECT TOP 1 매입신용카드세액 FROM 부가가치세통합조회 WHERE 사업자등록번호 = a.biz_no AND 과세기수 = '{kwasekikan}'  AND 신고구분 = '{ks2[:2]}'), 0) AS YN_TongCardCost,
               Isnull((select top 1 매입현금영수증세액	from 부가가치세통합조회 Where 사업자등록번호=a.biz_no and 과세기수='{kwasekikan}' and 신고구분='{ks2[:2]}'),-1)  YN_TongCashCost,
               ISNULL((SELECT SUM(합계금액) FROM 전자세금계산서 WHERE seq_no = a.seq_no AND {work_period}), 0) AS scrapTI,
               ISNULL((SELECT SUM(합계금액) FROM 전자세금계산서합계표 WHERE seq_no = a.seq_no  AND work_yy = '{work_YY}' AND work_qt = '{work_qt}'), 0) AS scrapTI_sum,
               Isnull((select sum(합계금액) from 전자세금계산서 where  seq_no = a.seq_no and {work_period} and 매입매출구분 in ('2','4')  and (품목명 like '%리스료%' or 품목명 like '%렌트%' or 품목명 like '%자동차%' or 공급자상호 like '%자동차%' or 공급자상호 like '%캐피탈%' or 공급자상호 like '%모터스%' or 공급자상호 like '%폭스바겐%')  ), 0) as scrapTI_Car,
               Isnull((select sum(합계금액) from 전자세금계산서 where seq_no = a.seq_no and {work_period} and 발급일자 > case when DATEPART(dw, REPLACE(DATEADD(DAY, 9, DATEADD(MONTH, DATEDIFF(MONTH, 0, 작성일자) + 1, 0)), '-','')) in (1) then DATEADD(DAY, 9, DATEADD(MONTH, DATEDIFF(MONTH, 0, 작성일자) + 2, 0))     when DATEPART(dw, REPLACE(DATEADD(DAY, 9, DATEADD(MONTH, DATEDIFF(MONTH, 0, 작성일자) + 1, 0)), '-','')) in (7) then DATEADD(DAY, 9, DATEADD(MONTH, DATEDIFF(MONTH, 0, 작성일자) + 3, 0)) 	   else DATEADD(DAY, 9, DATEADD(MONTH, DATEDIFF(MONTH, 0, 작성일자) + 1, 0)) end ), 0) as scrapTI_Added,
               Isnull((select sum(합계금액) from 전자세금계산서 where  seq_no = a.seq_no and {work_period} and 매입매출구분 in ('2','4')  and slip_acnt_cd='848'  ), 0) as scrapTI_848,
               Isnull((select yn_1 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_TI,
               Isnull((select yn_2 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_CardSale,
               Isnull((select yn_3 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_CashSale,
               Isnull((select yn_4 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_DaehangSale,
               Isnull((select yn_7 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_CardCost,
               Isnull((select yn_8 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), 0) as state_CashCost,
               Isnull((select yn_11 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), '0') as YN_11 ,
               Isnull((select yn_12 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), '0') as YN_12 ,
               Isnull((select yn_13 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), '0') as YN_13 ,
               Isnull((select yn_14 from tbl_mng_jaroe where  seq_no = a.seq_no and work_yy={work_YY} and work_mm ='{13+int(stnd_GB)}'  ), '0') as YN_14 ,               
               isnull((select top 1 send_result from Tbl_OFST_KAKAO_SMS where seq_user=a.seq_no and  left(send_dt,4)={searchYY} and right(left(send_dt,7),2)={searchMM} and contents like '%{work_mm}월 귀속분 전자세금계산서%') ,'') as kakaoSentTI,
               ISNULL((SELECT TOP 1 send_result FROM Tbl_OFST_KAKAO_SMS WHERE seq_user = a.seq_no AND  AND LEFT(send_dt, 4) = '{searchYY}' AND RIGHT(LEFT(send_dt, 7), 2) = '{searchMM}' AND contents LIKE '%신용카드%'), '') AS kakaoSentCard,
               ISNULL(YN_14,-1) as tongGrade_Q,
               biz_manager
        from mem_user a
        INNER JOIN mem_deal b ON a.seq_no = b.seq_no
        left outer join scrap_each d on  b.seq_no = d.seq_no 
        left outer join tbl_vat as e on e.seq_no=b.seq_no and e.work_YY = '{work_YY}' and e.work_qt = '{stnd_GB}'
        WHERE a.duzon_id <> ''
          AND b.keeping_YN = 'Y'
          and a.biz_type < '6' 
          {s_sql}                
        ORDER BY biz_name
        """
    # print(sql_query)
    recordset = []
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        results = cursor.fetchall()    
        for row in results:
            ( sqno, biz_name, biz_type, tot_ddct, tot_acntcd, car_ddct, car_class,
              YN_Tong, YN_TongCardSale, YN_TongCashSale, YN_TongDaehangSale,YN_TongCardCost, YN_TongCashCost,
              scrapTI, scrapTI_sum, scrapTI_Car, scrapTI_Added, scrapTI_848,
              state_TI, state_CardSale, state_CashSale, state_DaehangSale,state_CardCost, state_CashCost,
              YN_11,YN_12,YN_13,YN_14,
              kakaoSentTI, kakaoSentCard, tongGrade_Q,biz_manager
            ) = row   

            #통합조회
            YN_Tong = fn_YN_Tong(YN_Tong,tongGrade_Q)
            #전자세금계산서
            img_scrapTI = FN_scrapTI(cursor,sqno,work_YY,stnd_GB,state_TI,scrapTI,scrapTI_sum,scrapTI_848,YN_11,YN_12,YN_13,YN_14)
            # 카드 매출 데이터 처리
            imgCardSale = FN_CardSale(cursor,sqno,work_YY,stnd_GB,txtStnd_GB,biz_type,YN_TongCardSale,state_CardSale)
            # 현영 매출 데이터 처리
            imgCashSale = FN_CashSale(cursor,sqno,work_YY,stnd_GB,biz_type,txtStnd_GB,YN_TongCashSale,state_CashSale)
            # 카드 매입 데이터 처리
            imgCardCost = FN_CardCost(cursor,sqno,work_YY,stnd_GB,biz_type,YN_TongCardCost,state_CardCost)
            # 대행매출
            imgDaehangSale = FN_DaehangSale(cursor,sqno,work_YY,stnd_GB,biz_type,txtStnd_GB,YN_TongDaehangSale,state_DaehangSale)
            # 현영매입
            imgCashCost = FN_CashCost(cursor,sqno,work_YY,stnd_GB,biz_type,txtStnd_GB,YN_TongCashCost,state_CashCost)

            # 수출실적명세서 처리
            imgSaleExport = FN_SaleExport(cursor,sqno,work_YY,stnd_GB,biz_type,txtStnd_GB)

            # 내국신용장/구매확인서 처리
            imgSaleTT = FN_SaleTT(cursor,sqno,work_YY,stnd_GB,biz_type,txtStnd_GB)
            
            # 카카오 결과 전송 처리
            imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
            if kakaoSentTI=="Y":
              imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-kko.png'>"    
            elif kakaoSentTI=="0":
              imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-sns.png'>"  

            imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
            if kakaoSentCard=="Y":  
              imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-kko.png'>"    
            elif kakaoSentCard=="0":
              imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-sns.png'>"    

            record_dict  =  {
              'seq_no'		      : sqno,
              'biz_name'			: biz_name,
              'biz_type'		  : biz_type,
              'tot_ddct'  		: tot_ddct,
              'tot_acntcd'  	: tot_acntcd,
              'car_ddct'  		: car_ddct,
              'car_class'  		: car_class,
              'YN_Tong'			  : YN_Tong,
              'scrapTI_Car'		: scrapTI_Car,
              'scrapTI_Added'	: scrapTI_Added,
              'state_TI'		  : img_scrapTI,
              'state_CardSale'	: imgCardSale,
              'state_CashSale'	: imgCashSale,
              'state_DaehangSale'	: imgDaehangSale,
              'state_CardCost'	: imgCardCost,
              'state_CashCost'	: imgCashCost,
              'state_SaleExport'	:imgSaleExport,
              'state_SaleTT'	:imgSaleTT,
              'kakaoSentTI'		: imgKakaoSentTI,
              'kakaoSentCard'	: imgCardkakaoSent,
              'biz_manager'		  : biz_manager
            }
            recordset.append(record_dict)    
    # print(recordset) 
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)



# 월별 목록 보기
def scrap_monthly_list(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')
  request.session['ADID'] = ADID  

  work_YY = request.GET.get('work_YY', '')
  work_MM = request.GET.get('work_MM', '')
  request.session['workyearScrap'] = work_YY
  request.session['work_MM']  = work_MM

  work_qt = None
  work_period = ""
  work_MM = int(work_MM)

  if work_MM <= 3:
      work_qt = 1
      kwasekikan = f"{work_YY}년 1기"
      ks2 = "예정(정기)"
      work_period = f"작성일자>='{work_YY}-01-01' and 작성일자<='{work_YY}-03-31'"
      SKGB = "C17"
  elif work_MM <= 6:
      work_qt = 2
      kwasekikan = f"{work_YY}년 1기"
      ks2 = "확정(정기)"
      work_period = f"작성일자>='{work_YY}-04-01' and 작성일자<='{work_YY}-06-30'"
      SKGB = "C07"
  elif work_MM <= 9:
      work_qt = 3
      kwasekikan = f"{work_YY}년 2기"
      ks2 = "예정(정기)"
      work_period = f"작성일자>='{work_YY}-07-01' and 작성일자<='{work_YY}-09-30'"
      SKGB = "C17"
  elif work_MM <= 12:
      work_qt = 4;kwasekikan = f"{work_YY}년 2기";ks2 = "확정(정기)"
      work_period = f"작성일자>='{work_YY}-10-01' and 작성일자<='{work_YY}-12-31'"
      SKGB = "C07"
  request.session['work_qt'] = work_qt
  request.session.save()
  stnd_GB = work_qt
  txtStnd_GB = " stnd_gb "

  if stnd_GB in [1, 3]:
      txtStnd_GB = f"{txtStnd_GB} ='{stnd_GB}'"
  elif stnd_GB in [2, 4]:
      txtStnd_GB = f"{txtStnd_GB} in ('{int(stnd_GB)-1}','{stnd_GB}')"

  searchMM = int(work_MM) + 1
  searchYY = int(work_YY)
  if int(work_MM) == 12:
      searchMM = 1
      searchYY = int(work_YY) + 1      
  s_sql = ""
  if request.method == 'GET':
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"
    elif  ADID=="전체":
      s_sql = f" AND b.biz_manager != '화물'"
    if ADID=="화물":s_sql += " and biz_type=4 "
    searchMM = work_MM + 1
    searchYY = work_YY
    if work_MM==12 : 
      searchMM = 1 
      searchYY =  int(work_YY) + 1    
    sql_query = f"""
        SELECT a.seq_no AS sqno,a.biz_name,a.biz_type, ISNULL(tot_ddct, 0) AS tot_ddct,
               ISNULL((SELECT Acnt_Nm FROM Financial_AcntCd RIGHT OUTER JOIN scrap_each d  ON d.tot_acntcd = Acnt_Cd WHERE d.seq_no = a.seq_no), '소모품비') AS tot_acntcd,
               ISNULL(car_ddct, 0) AS car_ddct, ISNULL(car_class, '') AS car_class, 
               	isnull(f.YN_1,'0') as state_TI,
                isnull(f.YN_2,'0') as state_CardSale,
                isnull(f.YN_3,'0') as state_CashSale,
                isnull(f.YN_4, '0') as state_DaehangSale,
                isnull(f.YN_7, '0') as state_CardCost,
                isnull(f.YN_8, '0') as state_CashCost,
                isnull(f.YN_5, '0') as YN_5,
                isnull(f.YN_10, '0') as YN_10,
                isnull(f.YN_11, '0') as YN_11,
                isnull(f.YN_12, '0') as YN_12,
                isnull(f.YN_13, '0') as YN_13,
                isnull(f.YN_14, '0') as YN_14,
                isnull(f.bigo, '0/0/0') as bigo,
                isnull(과세기수,'')  AS YN_Tong,            
               isnull((select top 1 send_result from Tbl_OFST_KAKAO_SMS where seq_user=a.seq_no and   left(send_dt,4)={searchYY} and right(left(send_dt,7),2)={searchMM}  AND Kakao_tempCode ='023080000169') ,'') as kakaoSentTI,
               ISNULL((SELECT TOP 1 send_result FROM Tbl_OFST_KAKAO_SMS WHERE seq_user = a.seq_no AND  LEFT(send_dt, 4) = {searchYY} AND RIGHT(LEFT(send_dt, 7), 2) = {searchMM}  AND Kakao_tempCode in('023090000539','023090000535')), '') AS kakaoSentCard,
               ISNULL(e.YN_14,-1) as tongGrade_Q,
               biz_manager
        from mem_user a
        INNER JOIN mem_deal b ON a.seq_no = b.seq_no
        left outer join scrap_each d on  b.seq_no = d.seq_no 
        left outer join tbl_vat as e on e.seq_no=b.seq_no and e.work_YY = '{work_YY}' and e.work_qt = '{stnd_GB}'
        left outer join tbl_mng_jaroe as f on f.seq_no=b.seq_no and f.work_YY = '{work_YY}' and f.work_mm = '{13+int(stnd_GB)}'
        left outer join 부가가치세통합조회 as g on a.biz_no=사업자등록번호 AND 과세기수 = '{kwasekikan}' AND 신고구분 = '{ks2[:2]}'
        WHERE a.duzon_id <> ''
          AND b.keeping_YN = 'Y'
          and a.biz_type < '6' 
          {s_sql}                
        ORDER BY biz_name
        """
    # print(sql_query)
    recordset = []
    with connection.cursor() as cursor:
        cursor.execute(sql_query)
        results = cursor.fetchall()    
        for row in results:
            ( sqno, biz_name, biz_type, tot_ddct, tot_acntcd, car_ddct, car_class,
              state_TI, state_CardSale, state_CashSale, state_DaehangSale,state_CardCost, state_CashCost,
              YN_5,YN_10,YN_11,YN_12,YN_13,YN_14,bigo,             
              YN_Tong,  kakaoSentTI, kakaoSentCard, tongGrade_Q, biz_manager
            ) = row   

            #통합조회
            YN_Tong = fn_YN_Tong(YN_Tong,tongGrade_Q)
            #전자세금계산서
            if bigo.strip()=="":bigo="0/0/0"
            scrapTI_values = str(bigo).split('/')
            scrapTI_Car = scrapTI_values[0]
            scrapTI_Added = scrapTI_values[1]
            scrapTI_848 = scrapTI_values[2]
            img_scrapTI = FN_scrapTI(state_TI.strip(),scrapTI_848,YN_11.strip(),YN_12.strip(),YN_13.strip(),YN_14.strip())
            # 카드 매출 데이터 처리
            imgCardSale = FN_CardSale(state_CardSale.strip())
            # 현영 매출 데이터 처리
            imgCashSale = FN_CashSale(state_CashSale.strip())
            # 카드 매입 데이터 처리
            imgCardCost = FN_CardCost(state_CardCost.strip())
            # 대행매출
            imgDaehangSale = FN_DaehangSale(state_DaehangSale.strip())
            # 현영매입
            imgCashCost = FN_CashCost(state_CashCost.strip())
            # 수출실적명세서 처리
            imgSaleExport = FN_SaleExport(YN_5)
            # 내국신용장/구매확인서 처리
            imgSaleTT = FN_SaleTT(YN_10)
            
            # 카카오 결과 전송 처리
            imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
            if kakaoSentTI=="Y":
              imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-kko.png'>"    
            elif kakaoSentTI=="0":
              imgKakaoSentTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-sns.png'>"  

            imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
            if kakaoSentCard=="Y":  
              imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-kko.png'>"    
            elif kakaoSentCard=="0":
              imgCardkakaoSent = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-sns.png'>"    


            record_dict  =  {
              'groupManager'		  : biz_manager,
              'seq_no'		      : sqno,
              'biz_name'			: biz_name,
              'biz_type'		  : biz_type,
              'tot_ddct'  		: tot_ddct,
              'tot_acntcd'  	: tot_acntcd,
              'car_ddct'  		: car_ddct,
              'car_class'  		: car_class,
              'YN_Tong'			  : YN_Tong,
              'scrapTI_Car'		: scrapTI_Car,
              'scrapTI_Added'	: scrapTI_Added,
              'state_TI'		  : img_scrapTI,
              'state_CardSale'	: imgCardSale,
              'state_CashSale'	: imgCashSale,
              'state_DaehangSale'	: imgDaehangSale,
              'state_CardCost'	: imgCardCost,
              'state_CashCost'	: imgCashCost,
              'state_SaleExport'	:imgSaleExport,
              'state_SaleTT'	:imgSaleTT,
              'kakaoSentTI'		: imgKakaoSentTI,
              'kakaoSentCard'	: imgCardkakaoSent
            }
            recordset.append(record_dict)    
    # print(recordset) 
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)

def fn_YN_Tong(YN_Tong,tongGrade_Q):
    tongGrade = 4 - int(tongGrade_Q)
    if tongGrade < 1:                tongGrade = 1

    # YN_Tong 처리
    if YN_Tong.strip() == "":
        YN_Tong = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
    else:
        if int(tongGrade_Q) == -1:
            YN_Tong = '<img src="/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif">'
        else:
            YN_Tong = (
                '<img src="/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif">'
                + f'<img src="/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/feeling-{int(tongGrade)}.png">'
            )
    return YN_Tong

def FN_scrapTI(state_TI,scrapTI_848,YN_11,YN_12,YN_13,YN_14):
    img_scrapTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
    tblMngJaroeTI = 0
    if int(state_TI) == 3:
        img_scrapTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
        tblMngJaroeTI = 3
        if int(scrapTI_848) > 0:
            img_scrapTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog_edit.png'>"
            tblMngJaroeTI = 2
    else:
        img_scrapTI = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
        tblMngJaroeTI = 1
    if int(state_TI)==5 : img_scrapTI = "<img src=/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif>"
   
    
    img_scrapTI = f"{YN_11} {YN_12} {YN_13} {YN_14} {img_scrapTI}"  
    return img_scrapTI

def FN_CardSale(state_CardSale):
  imgCardSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if int(state_CardSale)==1:
    imgCardSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
  elif int(state_CardSale)==2:
    imgCardSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"    
  elif int(state_CardSale)==3:
    imgCardSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  return imgCardSale

def FN_DaehangSale(state_DaehangSale):
  imgDaehangSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if int(state_DaehangSale)==1:
    imgDaehangSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
  elif int(state_DaehangSale)==2:
    imgDaehangSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"    
  elif int(state_DaehangSale)==3:
    imgDaehangSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  return imgDaehangSale    

def FN_CashSale(state_CashSale):
  imgCashSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if int(state_CashSale)==1:
    imgCashSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
  elif int(state_CashSale)==2:
    imgCashSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"    
  elif int(state_CashSale)==3:
    imgCashSale = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  return imgCashSale

def FN_CardCost(state_CardCost):
  imgCardCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if int(state_CardCost)==1:
    imgCardCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
  elif int(state_CardCost)==2:
    imgCardCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"    
  elif int(state_CardCost)==3:
    imgCardCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  return imgCardCost

def FN_CashCost(state_CashCost):
  imgCashCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"  
  if int(state_CashCost)==1:
    imgCashCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/skeleton.gif'>"
  elif int(state_CashCost)==2:
    imgCashCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"    
  elif int(state_CashCost)==3:
    imgCashCost = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"    
  return imgCashCost

def FN_SaleExport(YN_5):
  imgSaleExport = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if YN_5 == 1:
      imgSaleExport = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  elif YN_5 == 2:
      imgSaleExport = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"
  return imgSaleExport

def FN_SaleTT(YN_10):
  imgSaleTT = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cross.gif'>"
  if YN_10 == 1:
      imgSaleTT = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/cog.png'>"
  elif YN_10 == 2:
      imgSaleTT = "<img src='/static/assets/plugins/ext422/extjs-build/examples/shared/icons/fam/connect.gif'>"
  return imgSaleTT


# 카드공제 설정
def scrap_card_list(request):
  return
def get_tax_period(seq_no,work_YY,work_MM):
    memuser = get_object_or_404(MemUser, seq_no=seq_no)
    scrapkikan = ""
    kwasekikan = ""
    read_qt = None
    
    # work_qt 계산
    if work_MM in [1, 2, 3]:
        work_qt = 1
    elif work_MM in [4, 5, 6]:
        work_qt = 2
    elif work_MM in [7, 8, 9]:
        work_qt = 3
    elif work_MM in [10, 11, 12]:
        work_qt = 4
    else:
        raise ValueError("Invalid work_MM value")
    read_qt = work_qt
    if work_qt == 1:
        scrapkikan = f"{work_YY} 년 1 월 1 일부터 {work_YY} 년 3 월 31 일까지"
        kwasekikan = f"{work_YY} 년 1기예정"
    
    elif work_qt == 2:
        query = f"SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = '{memuser.biz_no}' AND 과세기간 = '{work_YY}년 1기' AND 과세유형 = 'C17'"
        print(query)
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
        if result:
            scrapkikan = f"{work_YY} 년 4 월 1 일부터 {work_YY} 년 6 월 30 일까지"
            kwasekikan = f"{work_YY} 년 1기확정"
        else:
            scrapkikan = f"{work_YY} 년 1 월 1 일부터 {work_YY} 년 6 월 30 일까지"
            kwasekikan = f"{work_YY} 년 1기확정"
            read_qt = 5
        
        if memuser.biz_type in [5, 6]:
            read_qt = 5
    
    elif work_qt == 3:
        scrapkikan = f"{work_YY} 년 7 월 1 일부터 {work_YY} 년 9 월 30 일까지"
        kwasekikan = f"{work_YY} 년 2기예정"
    
    elif work_qt == 4:
        query = f"SELECT * FROM 부가가치세전자신고3 WHERE 사업자등록번호 = '{memuser.biz_no}' AND 과세기간 = '{work_YY}년 2기' AND 과세유형 = 'C17'"
        
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            
        if result:
            scrapkikan = f"{work_YY} 년 10 월 1 일부터 {work_YY} 년 12 월 31 일까지"
            kwasekikan = f"{work_YY} 년 2기확정"
        else:
            scrapkikan = f"{work_YY} 년 7 월 1 일부터 {work_YY} 년 12 월 31 일까지"
            kwasekikan = f"{work_YY} 년 2기확정"
            read_qt = 6
        
        if memuser.biz_type in [5, 6]:
            read_qt = 6
    
    return scrapkikan, kwasekikan, read_qt

def get_work_period(work_YY, read_qt, flag):
    periods_TI = {
        1: f"작성일자 >= '{work_YY}-01-01' AND 작성일자 <= '{work_YY}-03-31'",
        2: f"작성일자 >= '{work_YY}-04-01' AND 작성일자 <= '{work_YY}-06-30'",
        3: f"작성일자 >= '{work_YY}-07-01' AND 작성일자 <= '{work_YY}-09-30'",
        4: f"작성일자 >= '{work_YY}-10-01' AND 작성일자 <= '{work_YY}-12-31'",
        5: f"작성일자 >= '{work_YY}-01-01' AND 작성일자 <= '{work_YY}-06-30'",
        6: f"작성일자 >= '{work_YY}-07-01' AND 작성일자 <= '{work_YY}-12-31'",
    }

    periods_TIsum = {
        1: "work_qt = 1",
        2: "work_qt = 2",
        3: "work_qt = 3",
        4: "work_qt = 4",
        5: "work_qt in (1,2)",
        6: "work_qt in (3,4)",
    }

    if flag == "TI":
        return periods_TI.get(read_qt, "")
    elif flag == "TIsum":
        return periods_TIsum.get(read_qt, "")
    else:
        return ""

def fetch_results(query, params):
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def calculate_differences(h_data, i_data):
    # 리스트를 딕셔너리 형태로 변환
    h_data_dict = {str(item['매입매출구분']): item for item in h_data}
    i_data_dict = {str(item['매입매출구분']): item for item in i_data}
    
    diffs = {}
    for key in h_data_dict:
        diffs[key] = {
            '합계금액': h_data_dict[key].get('합계금액', 0) - i_data_dict.get(key, {}).get('합계금액', 0),
            '공급가액': h_data_dict[key].get('공급가액', 0) - i_data_dict.get(key, {}).get('공급가액', 0),
            '세액': h_data_dict[key].get('세액', 0) - i_data_dict.get(key, {}).get('세액', 0),
            '건수': h_data_dict[key].get('건수', 0) - i_data_dict.get(key, {}).get('건수', 0)
        }
    return diffs


#세금계산서합계표
@csrf_exempt 
def getTISummation(request):
  if request.method == "POST":
    seq_no = request.POST.get("seq_no")  
    work_YY = int(request.POST.get("work_YY"))
    work_MM = int(request.POST.get("work_MM"))
    scrapkikan, kwasekikan, read_qt = get_tax_period(seq_no,work_YY,work_MM)  
    work_period_TI = get_work_period(work_YY, read_qt, "TI")
    work_period_TIsum = get_work_period(work_YY, read_qt, "TIsum")

    sql_right = ("SELECT CASE 매입매출구분 "
                 "WHEN 1 THEN '1 : 매출 세금계산서' "
                 "WHEN 2 THEN '2 : 매입 세금계산서' "
                 "WHEN 3 THEN '3 : 매출 계산서' "
                 "WHEN 4 THEN '4 : 매입 계산서' END AS 매입매출구분, "
                 "SUM(합계금액) AS 합계금액, "
                 "CASE WHEN 매입매출구분 in (3,4) THEN SUM(합계금액) ELSE SUM(공급가액) END AS 공급가액, "
                 "SUM(세액) AS 세액, SUM(건수) AS 건수 FROM 전자세금계산서합계표 "
                 "WHERE seq_no=%s AND work_yy=%s AND  " + work_period_TIsum + " "
                 "GROUP BY 매입매출구분 ORDER BY 매입매출구분")
    # print(sql_right, work_YY, read_qt,work_period_TIsum)
    h_data = fetch_results(sql_right, (seq_no, work_YY))
    
    sql_final = ("SELECT CASE 매입매출구분 "
                 "WHEN 1 THEN '1 : 매출 세금계산서' "
                 "WHEN 2 THEN '2 : 매입 세금계산서' "
                 "WHEN 3 THEN '3 : 매출 계산서' "
                 "WHEN 4 THEN '4 : 매입 계산서' END AS 매입매출구분, "
                 "SUM(합계금액) AS 합계금액, SUM(공급가액) AS 공급가액, "
                 "SUM(세액) AS 세액, COUNT(*) AS 건수 FROM 전자세금계산서 "
                 "WHERE seq_no=%s AND " + work_period_TI + " "
                 "GROUP BY 매입매출구분 ORDER BY 매입매출구분")
    i_data = fetch_results(sql_final, (seq_no,))
    
    differences = calculate_differences(h_data, i_data)

    return JsonResponse({
        "scrapkikan": scrapkikan, 
        "kwasekikan": kwasekikan, 
        "differences": differences,
        "h_data": h_data,
        "i_data": i_data
    })

def get_stndGB_period( work_QT):
    periods = {
        1: ("stnd_GB = 1"),
        2: ("stnd_GB = 2"),
        3: ("stnd_GB = 3"),
        4: ("stnd_GB = 4"),
        5: ("stnd_GB IN (1,2)"),
        6: ("stnd_GB IN (3,4)")
    }
    return periods.get(work_QT, "")

@csrf_exempt
def getCardSummation(request):
    if request.method == "POST":
        seq_no = request.POST.get("seq_no")
        work_YY = int(request.POST.get("work_YY"))
        work_MM = int(request.POST.get("work_MM"))
        scrapkikan, kwasekikan, read_qt = get_tax_period(seq_no,work_YY,work_MM)  
        work_period = get_stndGB_period(read_qt)
        

        sql_total = (
            "SELECT Biz_Card_TY, ddcYnNm, File_DdctGB, totaTrsAmt, splCft, vaTxamt "
            "FROM tbl_hometax_scrap "
            "WHERE seq_no = %s AND tran_yy = %s AND " + work_period
        )
        total_data = fetch_results(sql_total, (seq_no, work_YY))

        categorized_data_template = {
            "합계금액": 0, "공급가액": 0, "세액": 0, "건수": 0
        }

        categorized_h = {
            "공제": copy.deepcopy(categorized_data_template),
            "불공제": copy.deepcopy(categorized_data_template),
            "확인대상": copy.deepcopy(categorized_data_template),
            "복지카드": copy.deepcopy(categorized_data_template)
        }
        
        categorized_i = {
            "공제": copy.deepcopy(categorized_data_template),
            "불공제": copy.deepcopy(categorized_data_template),
            "확인대상": copy.deepcopy(categorized_data_template)
        }

        for row in total_data:
            # categorized_h 집계
            if row["Biz_Card_TY"] == "3":
                category_h = row["ddcYnNm"]
            else:
                category_h = "복지카드"
            
            if category_h in categorized_h:
                categorized_h[category_h]["합계금액"] += float(row["totaTrsAmt"])
                categorized_h[category_h]["공급가액"] += float(row["splCft"])
                categorized_h[category_h]["세액"] += float(row["vaTxamt"])
                categorized_h[category_h]["건수"] += 1

            # categorized_i 집계
            category_i = row["File_DdctGB"].strip()
            if category_i in categorized_i:
                categorized_i[category_i]["합계금액"] += float(row["totaTrsAmt"])
                categorized_i[category_i]["공급가액"] += float(row["splCft"])
                categorized_i[category_i]["세액"] += float(row["vaTxamt"])
                categorized_i[category_i]["건수"] += 1


        sort_order = ["공제", "불공제", "확인대상", "복지카드"]
        categorized_diff = {
            key: {
                "합계금액": categorized_i.get(key, {"합계금액": 0})["합계금액"] - categorized_h.get(key, {"합계금액": 0})["합계금액"] ,
                "공급가액": categorized_i.get(key, {"공급가액": 0})["공급가액"] - categorized_h.get(key, {"공급가액": 0})["공급가액"],
                "세액": categorized_i.get(key, {"세액": 0})["세액"] - categorized_h.get(key, {"세액": 0})["세액"],
                "건수": categorized_i.get(key, {"건수": 0})["건수"] - categorized_h.get(key, {"건수": 0})["건수"]
            } for key in sort_order if key in categorized_h or key in categorized_i
        }
        return JsonResponse({
            "scrapkikan": scrapkikan, 
            "kwasekikan": kwasekikan, 
            "differences": categorized_diff,
            "h_data":  [{"매입매출구분": key, **values} for key, values in categorized_h.items()],
            "i_data":[{"매입매출구분": key, **values} for key, values in categorized_i.items()]     
        })

# scrap_each 테이블 업데이트
@csrf_exempt 
def update_scrap_each(request):
    if request.method == "POST":
        seq_no = request.POST.get("seq_no")
        target = request.POST.get("target", "").strip()
        val = unquote(request.POST.get("val", ""))  # URL 디코딩

        # "ddct"로 끝나는 경우 True/False를 "1"/"0"으로 변환
        if target == "tot_acntcd":
            acnt_cd = val
 
        # DB 연결
        with connection.cursor() as cursor:
            # 데이터 존재 여부 확인
            cursor.execute("SELECT seq_no FROM scrap_each WHERE seq_no = %s", [seq_no])
            existing_record = cursor.fetchone()

            if existing_record:
                # 업데이트
                if target == "tot_acntcd":
                    sql = """
                        UPDATE scrap_each  SET tot_acntcd = %s WHERE seq_no = %s
                    """
                    params = [acnt_cd, seq_no]
                else:
                    sql = "UPDATE scrap_each SET {} = %s WHERE seq_no = %s".format(target)
                    params = [val, seq_no]

            else:
                # 삽입
                if target == "tot_acntcd":
                    sql = "INSERT INTO scrap_each (seq_no, {}) VALUES (%s, %s)".format(target)
                    params = [seq_no, acnt_cd]
                else:
                    sql = "INSERT INTO scrap_each (seq_no, {}) VALUES (%s, %s)".format(target)
                    params = [seq_no, val]
            cursor.execute(sql, params)
        return JsonResponse({"status": "success", "query": sql, "params": params})
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)



