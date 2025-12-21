from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from app.models import MemDeal
from app.models import MemAdmin
from app.models import userProfile
from django.db import connection
import os
import imaplib
import imapclient
import email
import datetime
from datetime import date

now = datetime.datetime.now()

@login_required(login_url="/login/")
def index(request):
  global seq_no
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if userprofile:
    userprofile = userprofile.latest('description')
  if userprofile is not None:
    context['userProfile'] = userprofile
  if memuser.biz_type<4:
    context['isCorp'] = True
  seq_no = memuser.seq_no
  mem_deal = MemDeal.objects.get(seq_no=seq_no)
  mem_admin = MemAdmin.objects.get(admin_id=mem_deal.biz_manager)  
  context['memuser'] = memuser
  context['memadmin'] = mem_admin

  sql_MonthSale = "		select work_yy		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='01' then tranamt_dr-tranamt_cr else 0 end) as '1월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='02' then tranamt_dr-tranamt_cr else 0 end) as '2월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='03' then tranamt_dr-tranamt_cr else 0 end) as '3월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='04' then tranamt_dr-tranamt_cr else 0 end) as '4월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='05' then tranamt_dr-tranamt_cr else 0 end) as '5월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='06' then tranamt_dr-tranamt_cr else 0 end) as '6월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='07' then tranamt_dr-tranamt_cr else 0 end) as '7월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='08' then tranamt_dr-tranamt_cr else 0 end) as '8월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='09' then tranamt_dr-tranamt_cr else 0 end) as '9월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='10' then tranamt_dr-tranamt_cr else 0 end) as '10월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='11' then tranamt_dr-tranamt_cr else 0 end) as '11월'		"
  sql_MonthSale += "		,SUM(case when left(tran_dt,2)='12' then tranamt_dr-tranamt_cr else 0 end) as '12월'		"
  sql_MonthSale += "		,SUM(tranamt_dr-tranamt_cr) as '연합계'		"
  sql_MonthSale += "		from ds_slipledgr2 		"
  sql_MonthSale += "		where  seq_no="+memuser.seq_no+" and ( acnt_cd>=401 and acnt_cd<=430) and Remk <> '손익계정에 대체'		"
  sql_MonthSale += "		group by work_yy		"
  cursor = connection.cursor()
  result = cursor.execute(sql_MonthSale)
  wholeSale = cursor.fetchall()
  connection.commit()
  connection.close()
  saleMonthly = []
  for yearSale in wholeSale:
    saleMonthly.append({'x':yearSale[0]+"-01",'y':str(yearSale[1])})
    saleMonthly.append({'x':yearSale[0]+"-02",'y':str(yearSale[2])})
    saleMonthly.append({'x':yearSale[0]+"-03",'y':str(yearSale[3])})
    saleMonthly.append({'x':yearSale[0]+"-04",'y':str(yearSale[4])})
    saleMonthly.append({'x':yearSale[0]+"-05",'y':str(yearSale[5])})
    saleMonthly.append({'x':yearSale[0]+"-06",'y':str(yearSale[6])})
    saleMonthly.append({'x':yearSale[0]+"-07",'y':str(yearSale[7])})
    saleMonthly.append({'x':yearSale[0]+"-08",'y':str(yearSale[8])})
    saleMonthly.append({'x':yearSale[0]+"-09",'y':str(yearSale[9])})
    saleMonthly.append({'x':yearSale[0]+"-10",'y':str(yearSale[10])})
    saleMonthly.append({'x':yearSale[0]+"-11",'y':str(yearSale[11])})
    saleMonthly.append({'x':yearSale[0]+"-12",'y':str(yearSale[12])})
  context['saleMonthly'] = saleMonthly
 
  today = date.today()
  txt_Tax = "종소세"
  txt_Defict = "소득공제"
  sql_rep = ""
  if memuser.biz_type<=3:
    txt_Tax = "법인세"
    txt_Defict = "이월결손금"
  if mem_deal.fiscalmm=="12":
    sql_rep = "	select work_yy	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=401 and acnt_cd<=430 then tranAmt_dr-tranAmt_cr Else 0 End),0) as 매출액	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=451 and acnt_cd<=470 then tranAmt_cr Else 0 End),0) as 매출원가	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=146 and acnt_cd<=149 then tranAmt_cr Else 0 End),0) as 상품당기매입	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=501 and acnt_cd<=800 and Remk not like '%원가로 대체%' then tranAmt_cr-tranAmt_dr Else 0 End),0) as 제조당기매입	"
    sql_rep += "  , isnull(SUM(case when (acnt_cd>=801 and acnt_cd<=810)  then tranAmt_cr-tranAmt_dr Else 0 End),0) as 급여	"
    sql_rep += "  , isnull(SUM(case when (acnt_cd>=811 and acnt_cd<=900)  then tranAmt_cr-tranAmt_dr Else 0 End),0) as 기타판관비	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=901 and acnt_cd<=950 then tranAmt_dr-tranAmt_cr Else 0 End),0) as 영업외수익	"
    sql_rep += "  , isnull(SUM(case when acnt_cd>=951 and acnt_cd<=997 then tranAmt_cr-tranAmt_dr Else 0 End),0) as 영업외비용	"
    sql_rep += "  , isnull(SUM(case when acnt_cd=518 OR acnt_cd=618 OR acnt_cd=668  OR acnt_cd=718  OR acnt_cd=768  OR acnt_cd=818 then tranAmt_cr Else 0 End),0) as 감가상각비 "
    sql_rep += "  , isnull(SUM(case when acnt_cd>=998 and acnt_cd<=999 then tranAmt_cr-tranAmt_dr Else 0 End),0) as " + txt_Tax + "등	"
    sql_rep += "  , isnull(SUM(case when acnt_cd=253 and left(trader_code,1)='9' then tranAmt_dr  Else 0 End),0) as 신용카드	"
    sql_rep += "  from ds_slipledgr2	"
    sql_rep += "  where seq_no="+memuser.seq_no
    sql_rep += "  and (( acnt_cd>=401 and acnt_cd<=999)	or ( acnt_cd>=146 and acnt_cd<=253))	"
    sql_rep += "  and  acnt_cd <> '150'	"	
    sql_rep += "  and  Remk <> '손익계정에 대체'	"
    sql_rep += "  and tran_dt<>'00-00'	"
    sql_rep += "  group by work_yy		"
    sql_rep += "  order by work_yy	desc	"
  else:
    for m in range(5):
      sql_rep += "  	select "+str(today.year-m)+" work_yy	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=401 and acnt_cd<=430 then tranAmt_dr-tranAmt_cr Else 0 End),0) as 매출액	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=451 and acnt_cd<=470 then tranAmt_cr Else 0 End),0) as 매출원가	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=146 and acnt_cd<=149 then tranAmt_cr Else 0 End),0) as 상품당기매입	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=501 and acnt_cd<=800 and Remk not like '%원가로 대체%' then tranAmt_cr-tranAmt_dr Else 0 End),0) as 제조당기매입	"
      sql_rep += "  , isnull(SUM(case when (acnt_cd>=801 and acnt_cd<=810)  then tranAmt_cr-tranAmt_dr Else 0 End),0) as 급여	"
      sql_rep += "  , isnull(SUM(case when (acnt_cd>=811 and acnt_cd<=900)  then tranAmt_cr-tranAmt_dr Else 0 End),0) as 기타판관비	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=901 and acnt_cd<=950 then tranAmt_dr-tranAmt_cr Else 0 End),0) as 영업외수익	"
      sql_rep += "  , isnull(SUM(case when acnt_cd>=951 and acnt_cd<=997 then tranAmt_cr-tranAmt_dr Else 0 End),0) as 영업외비용	"
      sql_rep += "  , isnull(SUM(case when acnt_cd=518 OR acnt_cd=618 OR acnt_cd=668  OR acnt_cd=718  OR acnt_cd=768  OR acnt_cd=818 then tranAmt_cr Else 0 End),0) as 감가상각비 "
      sql_rep += "  , isnull(SUM(case when acnt_cd>=998 and acnt_cd<=999 then tranAmt_cr-tranAmt_dr Else 0 End),0) as " + txt_Tax + "등	"
      sql_rep += "  , isnull(SUM(case when acnt_cd=253 and left(trader_code,1)='9' then tranAmt_dr Else 0 End),0) as 신용카드	"
      sql_rep += "  from ds_slipledgr2	"
      sql_rep += "  where seq_no=" + memuser.seq_no
      sql_rep += "  and (( acnt_cd>=401 and acnt_cd<=999)	or ( acnt_cd>=146 and acnt_cd<=253))	"
      sql_rep += "  and  acnt_cd <> '150'	"
      sql_rep += "  and  Remk <> '손익계정에 대체'	"
      sql_rep += "  and tran_dt<>'00-00'	"
      sql_rep += "  and ( (Work_YY = "+str(today.year-m)+" and tran_dt < '0" + str(int(mem_deal.fiscalmm)+1) + "-01') or ( Work_YY = " + str(today.year-1-m) + " and tran_dt >= '0"+ str(int(mem_deal.fiscalmm)+1) + "-01')) 	"
      if m<4:
        sql_rep = sql_rep + "  union all "
  cursor = connection.cursor()
  result = cursor.execute(sql_rep)
  wholeLedgr = cursor.fetchall()
  connection.commit()
  connection.close()
  saleledgrs = []
  costledgrs = []
  for ledgr in wholeLedgr:
    saleledgrs.append([ledgr[0],str(ledgr[1])])
    costledgrs.append([ledgr[0],str(ledgr[2]+ledgr[5]+ledgr[6]-ledgr[7]+ledgr[8]+ledgr[10])])
  context['saleledgrs'] = saleledgrs
  context['costledgrs'] = costledgrs
  context['costledgrs'] = costledgrs
  beneSum = 0;beneNow=0;benePre=0
  if wholeLedgr:
    context['saleSum'] = wholeLedgr[0][1]
    beneSum = wholeLedgr[0][1] - (wholeLedgr[0][2]+wholeLedgr[0][5]+wholeLedgr[0][6]-wholeLedgr[0][7]+wholeLedgr[0][8]+wholeLedgr[0][10])
    beneNow = wholeLedgr[0][1] - (wholeLedgr[0][2]+wholeLedgr[0][5]+wholeLedgr[0][6]-wholeLedgr[0][7]+wholeLedgr[0][8]+wholeLedgr[0][10])
    if len(wholeLedgr)>1:
      benePre = wholeLedgr[1][1] - (wholeLedgr[1][2]+wholeLedgr[1][5]+wholeLedgr[1][6]-wholeLedgr[1][7]+wholeLedgr[1][8]+wholeLedgr[1][10])
  context['beneSum'] = beneSum
  if beneSum<0:
    context['beneTxtColor'] = "text-red"

  try:
    context['beneRate'] = round( (beneNow-benePre)/benePre*100 , 2)
  except:
    context['beneRate']=0
  if beneNow>=benePre:
    context['beneTxt'] = "증가"
    context['beneArrow'] = "up"
  else:
    context['beneTxt'] = "감소"
    context['beneArrow'] = "down"
  preSaleSum = 0
  nowSaleSum = 0
  forRange = 12
  work_qt=1
  if now.month<=3:
    forRange = 12
    work_qt=4
  elif now.month<=6:
     forRange = 3
     work_qt=1
  elif now.month<=9:
     forRange = 6
     work_qt=2
  elif now.month<=12:
     forRange = 9    
     work_qt=3
  if len(wholeSale)>0:
    for m in range(forRange):
      if m>0 and m<13:
        preSaleSum += wholeSale[len(wholeSale)-2][m]
        nowSaleSum += wholeSale[len(wholeSale)-1][m]
  try:
    if nowSaleSum>0:
      context['saleIncRate'] = round( (nowSaleSum-preSaleSum)/preSaleSum*100 , 2)
    else:
      context['saleIncRate'] = 0
  except ZeroDivisionError:
    context['saleIncRate'] = 0
  if nowSaleSum>=preSaleSum:
    context['saleIncTxt'] = "증가"
    context['saleArrow'] = "up"
  else:
    context['saleIncTxt'] = "감소"
    context['saleArrow'] = "down"
  valDefict = 0;PREvalKackRev=0;gongjeRate=0;PREvalSanse=0;
  if int(memuser.biz_type)<=3:
    strsql = "select 각사업연도소득,결손금누계,최저한세적용대상,최저한세적용제외 from tbl_EquityEval where 사업자번호='" + memuser.biz_no + "' and left(사업연도말,4)="+str(today.year-1)
    cursor = connection.cursor()
    result = cursor.execute(strsql)
    result2 = cursor.fetchall()
    connection.commit()
    connection.close()
   
    if result2:
      kacksa = int(0 if result2[0][0]=='' else result2[0][0])
      valDefict = int(0 if result2[0][1]=='' else result2[0][1])
      targetLimit = int(0 if result2[0][2]=='' else result2[0][2])
      nontargetLimit = int(0 if result2[0][3]=='' else result2[0][3])
      if kacksa>200000000:
        sanchul = kacksa*2/10 -20000000
      else:
        sanchul = kacksa*1/10
      gongjeRate = targetLimit/ sanchul
    valKackRev = beneNow
    if work_qt<4:
      PREvalKackRev = valKackRev*4/work_qt
    valKwase = valKackRev - valDefict
    PREvalKwase = PREvalKackRev - valDefict
    if valKwase<0:
      valKwase = 0
    if PREvalKwase<0:
      PREvalKwase = 0
    if valKwase>200000000:
      valTaxRate = 20
      valSanse = valKwase*2/10 -20000000
    else:
      valTaxRate = 10
      valSanse = float(valKwase)*0.1
    if PREvalKwase>200000000:
      PREvalSanse = PREvalKwase*2/10 -20000000
    else:
      PREvalSanse = PREvalKwase/10
    valGongje = float(valSanse) *  gongjeRate
    valBubTax = valSanse - int(valGongje)
    valRegalTax = valBubTax/10
    valTotalTax = valBubTax + valRegalTax

    PREvalGongje = float(PREvalSanse) *  gongjeRate
    PREvalBubTax = PREvalSanse - int(PREvalGongje)
    PREvalRegalTax = PREvalBubTax/10
    PREvalTotalTax = PREvalBubTax + PREvalRegalTax
  else:
    strsql = "select 소득공제,종합소득_산출세액,종합소득_세액감면,종합소득_세액공제 from elec_income where ssn='" + memuser.ssn + "' and work_YY=" + str(today.year-1)
    cursor = connection.cursor()
    result = cursor.execute(strsql)
    result3 = cursor.fetchall()
    connection.commit()
    connection.close()
    if result3:
      valDefict = int(0 if result3[0][0]=='' else result3[0][0])
      sanchul = int(0 if result3[0][1]=='' else result3[0][1])
      tax_kammyun = int(0 if result3[0][2]=='' else result3[0][2])
      tax_gongje = int(0 if result3[0][3]=='' else result3[0][3])
      if sanchul==0:
        gongjeRate = 0
      else:
        gongjeRate = tax_kammyun / sanchul
    else:
      valDefict = 1500000
      tax_gongje = 70000
    valKackRev = beneNow
    valKwase = valKackRev - valDefict
    if valKwase<0:
      valKwase = 0
    if valKwase<=12000000:
      valTaxRate = 6
      valSanse = float(valKwase)*0.06
    elif valKwase<=46000000:
      valTaxRate = 15
      valSanse = float(valKwase)*0.15 - 1080000
    elif valKwase<=88000000:
      valTaxRate = 24
      valSanse = float(valKwase)*0.24 - 5220000
    elif valKwase<=150000000:
      valTaxRate = 35
      valSanse = float(valKwase)*0.35 - 14900000
    elif valKwase<=500000000 :
      valTaxRate = 38
      valSanse = float(valKwase)*0.38 - 19400000
    else:
      valTaxRate = 42
      valSanse = float(valKwase)*0.42 - 29400000
    # '*****************************    산출세액		**********************************
    strSql = "         Select prgrs_ddct_amt,taxat_stand_min,taxrat "
    strSql += "  From WorkTax With (Nolock)  "
    strSql += " Where taxat_stand_min <= " + str(valKwase)
    strSql += "   And taxat_stand_max  > " + str(valKwase)
    strSql += "   And YY         = (select top 1 YY from worktax order by yy desc) "
    cursor = connection.cursor()
    result = cursor.execute(strSql)
    rsResult = cursor.fetchall()
    connection.commit()
    connection.close()
    if rsResult:
      valSanse = int(rsResult[0][0]) + float(valKwase - int(rsResult[0][1])) / 100 * float(rsResult[0][2])
      valTaxRate = float(rsResult[0][2])
    if work_qt<4:
      PREvalKackRev = valKackRev*4/work_qt
      PREvalKwase = PREvalKackRev - valDefict
      if PREvalKwase<0 :
        PREvalKwase = 0
      if PREvalKwase<=12000000 :
        PREvalSanse = float(PREvalKwase)*0.06
      elif PREvalKwase<=46000000 :
        PREvalSanse = float(PREvalKwase)*0.15 - 1080000
      elif PREvalKwase<=88000000 :
        PREvalSanse = float(PREvalKwase)*0.24 - 5220000
      elif PREvalKwase<=150000000 :
        PREvalSanse = float(PREvalKwase)*0.35 - 14900000
      elif PREvalKwase<=500000000 :
        PREvalSanse = float(PREvalKwase)*0.38 - 19400000
      else:
        PREvalSanse = float(PREvalKwase)*0.42 - 29400000
      strSql = "         Select prgrs_ddct_amt,taxat_stand_min,taxrat "
      strSql += "  From WorkTax With (Nolock)  "
      strSql += " Where taxat_stand_min <= " + str(PREvalKwase)
      strSql += "   And taxat_stand_max  > " + str(PREvalKwase)
      strSql += "   And YY         = (select top 1 YY from worktax order by yy desc) "
           
      cursor = connection.cursor()
      result = cursor.execute(strSql)
      rsResult2 = cursor.fetchall()
      connection.commit()
      connection.close()
      if rsResult2:
        PREvalSanse = int(rsResult2[0][0]) + float(PREvalKwase - int(rsResult2[0][1])) / 100 *float(rsResult2[0][2])
        valTaxRate = float(rsResult2[0][2])
 
    if tax_gongje>(valSanse - valSanse *  gongjeRate)  :
      valGongje = valSanse
    else:
      valGongje = valSanse *  gongjeRate + tax_gongje
    if tax_gongje>(PREvalSanse - PREvalSanse *  gongjeRate) :
      PREvalGongje = PREvalSanse
    else:
      PREvalGongje = PREvalSanse *  gongjeRate + tax_gongje	
    valBubTax = valSanse - valGongje
    valRegalTax = float(valBubTax) * 0.1
    valTotalTax = valBubTax + int(valRegalTax)
    PREvalBubTax = PREvalSanse - PREvalGongje
    PREvalRegalTax = float(PREvalBubTax) * 0.1
    PREvalTotalTax = PREvalBubTax + int(PREvalRegalTax)

  context['valKackRev'] = valKackRev
  context['valDefict'] = valDefict      #이월결손금/소득공제
  context['valKwase'] = valKwase        #과세표준
  context['valTaxRate'] = int(valTaxRate)    #세율
  context['valSanse'] = int(valSanse)        #산출세액
  context['valGongje'] = int(valGongje)      #공제감면
  context['valBubTax'] = int(valBubTax)      #결정세액
  context['valTotalTax'] = int(valTotalTax)      #총부담액
  context['valRegalTax'] = int(valRegalTax)      #주민세
  context['txt_Tax'] = txt_Tax
  context['txt_Defict'] = txt_Defict

  # 주요일정 - 최상단
  getTaxSchedule(memuser,context)
  getPresentTax(memuser,context)
  getOlderTax(memuser,context)
  # 주요업무리스트
  getMajorTimeline(memuser,str(now.year),context)
  getWonchunTimeline(memuser,str(now.year),context)
  getFolderTimeline(memuser,str(now.year),context,"요청")
  getZKZSTimeline(memuser,str(now.year),context)
 
  # 메일 가져오기
  # getGMailList(memuser)
  return render(request, "dashboard/main-dash.html",context)

def getZKZSTimeline(memuser,work_yy,context):
  strsql = "select 신고서종류,접수일시,과세년도,신고구분,'','',접수번호,'간이지급조서',접수일시,제출금액,제출건수,'' from  지급조서간이소득  "
  strsql += " where 사업자번호='"+memuser.biz_no+"' and year(접수일시)= "+work_yy#right(과세년도,2)="+ str(int(work_yy)-2000) + " and 
  strsql += " union all "
  strsql += " select 신고서종류,접수일시,과세년도,신고구분,'','',접수번호,'연간지급조서',접수일시,제출금액,제출건수,'' from  지급조서전자신고 where 사업자번호='"+memuser.biz_no+"' and  과세년도="+work_yy
  cursor = connection.cursor();print(strsql)
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  revList=[]
  if result:
    for r in result:
      if r[7]=="간이지급조서":
        tmpStr=""
        if r[2][:3].upper()=="JAN":
          tmpStr = "1월"
        elif  r[2][:3].upper()=="FEB":
          tmpStr = "2월"
        elif  r[2][:3].upper()=="MAR":
          tmpStr = "3월"
        elif  r[2][:3].upper()=="APR":
          tmpStr = "4월"
        elif  r[2][:3].upper()=="MAY":
          tmpStr = "5월"
        elif  r[2][:3].upper()=="JUN":
          tmpStr = "6월"
        elif  r[2][:3].upper()=="JUL":
          tmpStr = "7월"
        elif  r[2][:3].upper()=="AUG":
          tmpStr = "8월"
        elif  r[2][:3].upper()=="SEP":
          tmpStr = "9월"
        elif  r[2][:3].upper()=="OCT":
          tmpStr = "10월"
        elif  r[2][:3].upper()=="NOV":
          tmpStr = "11월"
        elif  r[2][:3].upper()=="DEC":
          tmpStr = "12월"
      else:
        tmpStr = r[2]+"년"

      txtTitle = tmpStr+" " + r[0] + "제출"
      txtColor="success"
      txt0 = r[2][:4]+tmpStr.replace("월","")
      if int(work_yy)<2024:
        txt0 = str(int(r[2][4:6])+2000)+tmpStr.replace("월","")
      txt1=txt0
      row = {
        'majorTaxFlag':r[0],
        'majorTaxDate':r[1],
        'majorTaxTitle':txtTitle,
        'majorTaxDesc':r[4],
        'majorTaxNum':r[6],
        'majorTaxIssue':r[3],
        'majorIcon':"file-text",
        'majorTitleColor':txtColor,
        'majorSort':int(r[1][5:7])*100 + int(r[1][8:10]),
        'majorBadge':True,
        'major0':txt0,
        'major1':txt1,
        'major2':r[8][0:4]+r[8][5:7],
        'major3':r[9],
        'major4':r[10],
        'major5':r[11],
        'major6':'',
        'major7':'',
        'major8':'',
        'major9':''
      }      
      revList.append(row)
  fileList = getFolderTimeline(memuser,str(now.year),context,"대보험")
  if fileList:
    for file in fileList:
      revList.append(file)
 
  revList = sorted(revList,key=lambda x: x['majorSort'],reverse=True)
  context['zkzsList'] = revList

def getFolderTimeline(memuser,work_yy,context,flag):
  tmpfolder=""
  if os.path.isdir('static/cert_DS/'+memuser.biz_name+'/'+work_yy):
    for dir in os.listdir('static/cert_DS/'+memuser.biz_name+'/'+work_yy):
      if  flag in dir:
        tmpfolder = dir
        break
  path = 'static/cert_DS/'+memuser.biz_name+'/'+work_yy+'/'+tmpfolder+'/'
  totalfileArr=[]
  if os.path.isdir(path):
    for r in os.listdir(path):
      if os.path.isfile(path+"/"+r) and r!="Thumbs.db":
        dtime = datetime.datetime.fromtimestamp(os.path.getctime(f"{path}{r}"))
        dtime.month
        row = {
          'majorTaxFlag':r,
          'majorTaxDate':str(dtime.year)+"-"+str(dtime.month)+"-"+str(dtime.day),
          'majorTaxTitle':os.path.splitext(r)[0],
          'majorTaxDesc':'',
          'majorTaxNum':'',
          'majorTaxIssue':'',
          'majorIcon':"user-check",
          'majorTitleColor':"warning",
          'majorSort':dtime.month*100 + dtime.day,
          'majorBadge':False
        }        
        totalfileArr.append(row)  
    revList = sorted(totalfileArr,key=lambda x: x['majorSort'],reverse=True)
    if flag=="요청":
      context['workRequest'] = revList  
    elif flag=="대보험":
      return  revList  

def getMajorTimeline(memuser,work_yy,context):
  revList=[]
  vatList = getSummitList(memuser.biz_no,memuser.ssn,work_yy,"vat")
  if vatList:
    for vat in vatList:
      revList.append(vat)
  if memuser.biz_type<4:
    revList1= getSummitList(memuser.biz_no,memuser.ssn,work_yy,"corp")
    if revList1:
      for rev in revList1:
        revList.append(rev)
  else:
    revList2= getSummitList(memuser.biz_no,memuser.ssn,work_yy,"income")
    if revList2:
      for rev in revList2:
        revList.append(rev)
  mailList = getMajorMailList(memuser.seq_no,work_yy,"major")
  if mailList:
    for mail in mailList:
      revList.append(mail)
  # print(revList)
  revList = sorted(revList,key=lambda x: x['majorSort'],reverse=True)
  context['majorTaxList'] = revList
  # context['majorTaxList'] = revList

def getWonchunTimeline(memuser,work_yy,context):
  revList = []
  strsql = "select 신고서종류,접수일시,과세연월,신고구분,신고유형,접수번호,접수여부,지급연월,제출연월,A99,a99m,a99t from 원천세전자신고 A "
  strsql  += " where A.사업자등록번호='"+memuser.biz_no+"' "
  strsql  += "  and left(A.과세연월,4)="+work_yy
  strsql  += "  order by A.과세연월 asc"
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()

  if result:
    for r in result:
      tmpTime=''
      try:
        tmpTime = int(r[1][5:7])*100 + int(r[1][8:10])
      except:
        tmpTime=''
      row = {
        'majorTaxFlag':"원천징수이행상황",
        'majorTaxDate':r[1],
        'majorTaxTitle':str(int(r[2][4:6])) + "월 원천세신고",
        'majorTaxDesc':r[4],
        'majorTaxNum':r[5],
        'majorTaxIssue':r[6],
        'majorIcon':"file-text",
        'majorTitleColor':"primary",
        'majorSort':tmpTime,
        'majorBadge':True,
        'major0':r[2],
        'major1':r[7],
        'major2':r[8],
        'major3':r[9],
        'major4':r[10],
        'major5':r[11],
        'major6':'',
        'major7':'',
        'major8':'',
        'major9':''
      }
      revList.append(row)
  mailList = getMajorMailList(memuser.seq_no,work_yy,"wonchun")
  if mailList:
    for mail in mailList:
      revList.append(mail)
  try:
    revList = sorted(revList,key=lambda x: x['majorSort'],reverse=True)
  except:
    revList = revList
  context['wonchunList'] = revList
 
def getMajorMailList(seq_no,work_yy,flag):
  tmpTxt=""
  if flag=="wonchun":
      tmpTxt = "'pay','mail'"
  elif flag=="major":
      tmpTxt = "'vat','incometax','corp'"

  strsql = "select mail_date,mail_subject from tbl_mail "
  strsql += " where seq_no="+seq_no
  strsql += "  and year(mail_date)="+ work_yy
  strsql += "and mail_class in("+tmpTxt+") "
  strsql += " order by mail_date"
  # print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  summitList=[]
  if result:
    for m in result:
      tmpTitle = "부가가치세"
      tmpSubject = m[1].replace("[세무법인 대승]","");
      tmpSubject = tmpSubject.replace("[세무법인대승]","");
      tmpSubject = tmpSubject.split("(")[0]    
      if m[1].find("부가가치세")!=-1: tmpTitle = tmpSubject    
      if m[1].find("법인세")!=-1:     tmpTitle = tmpSubject
      if m[1].find("종합소득세")!=-1: tmpTitle = tmpSubject
      if m[1].find("급여")!=-1:       tmpTitle = "원천세"      
      row = {
        'majorTaxFlag':"",
        'majorTaxDate':str(m[0].year) + "-" + str(m[0].month) + "-" + str(m[0].day),
        'majorTaxTitle':tmpTitle+" 메일 발송",
        'majorTaxDesc':tmpSubject,
        'majorTaxNum':'',
        'majorTaxIssue':'',
        'majorIcon':"mail",
        'majorTitleColor':"info",
        'majorSort':m[0].month*100 + m[0].day,
        'majorBadge':False
      }
      summitList.append(row)
  return summitList

def getSummitList(bizNo,ssn,work_yy,flag):
  txt_Tax = "";strsql=""
  if flag=="vat":
    txt_Tax = "부가가치세"
    strsql = "select 신고시각,과세기간,신고구분,신고번호,접수여부,과세유형,환급구분,환급구분코드,과세표준금액,차감납부할세액,'','','' from 부가가치세전자신고3   "
    strsql +=  " where 사업자등록번호='"+bizNo+"' "
    strsql += "  and left(과세기간,4)="+work_yy
    strsql += "  order by 신고시각 asc"
  elif flag=="corp":
    txt_Tax = "법인세"
    strsql = "select a.신고시각, a.과세년월,a.신고서종류,a.신고번호,a.접수여부,a.신고구분,a.신고유형,b.사업연도,b.과세표준_합계,농특세,차감납부세액_합계,분납세액,차감납부세액 from 법인세전자신고2 a,tbl_EquityEval b  "
    strsql +=  " where a.사업자번호='"+bizNo+"' and a.사업자번호=b.사업자번호 "
    strsql += "  and left(a.과세년월,4)="+str(int(work_yy)-1)
    strsql += "  and left(b.사업연도말,4)="+str(int(work_yy)-1)
    strsql += "  order by a.신고시각 asc"
  elif flag=="income":
    txt_Tax = "종합소득세"
    strsql = "select a.신고시각, a.과세년월,a.신고서종류,a.신고번호,a.접수여부,a.신고구분,농특세_합계,work_yy+'년',"
    strsql += " 종합소득_합계,농특세_분납할세액,종합소득_과세표준,종합소득_분납할세액,농특세_신고기한내납부할세액,종합소득_기납부세액,종합소득_신고기한내납부할세액 from 종합소득세전자신고2 a,elec_income b "
    strsql += "  where left(a.주민번호,6)='"+ssn[:6]+"' and left(a.주민번호,6)=left(b.ssn,6) "
    strsql += "  and left(a.과세년월,4)="+str(int(work_yy)-1)
    strsql += "  and b.work_yy="+str(int(work_yy)-1)
    strsql += "  order by a.신고시각 asc"
  cursor = connection.cursor()
  #print(strsql)
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  summitList=[]
  if result:
    for r in result:
      tmpTitle="";tmpDesc = "";tmpMajor3=r[6];tmpMajor4=r[8];tmpMajor5=r[9];tmpMajor6=r[11];tmpMajor7='0';tmpMajor8=r[12];tmpMajor9='0'
      major4=r[8]
      if flag=="vat":
        tmpTitle=r[1] + r[2] +" 접수"
        tmpDesc = r[2] + " / " + r[6]
      elif flag=="corp":
        tmpTitle = r[1][0:4]+"년 귀속 " + r[5] +"신고서 접수"
        tmpDesc = r[5] + " / " + r[6]
      elif flag=="income":
        tmpTitle = r[1][0:4]+"년 귀속 " + r[5] +"신고서 접수"
        tmpDesc = r[5]
        tmpMajor3=r[6];tmpMajor4=r[8];tmpMajor5=r[9];tmpMajor6=r[11];tmpMajor7=r[12];tmpMajor8=r[13];tmpMajor9=r[14]
      majorTaxDate = r[0]
      if majorTaxDate=='':majorTaxDate = r[1][0:4]+"-00-25"
      row = {
        'majorTaxFlag':txt_Tax,
        'majorTaxDate':r[0],
        'majorTaxTitle':tmpTitle,
        'majorTaxDesc':tmpDesc,
        'majorTaxNum':r[3],
        'majorTaxIssue':r[4],
        'majorIcon':"clipboard",
        'majorTitleColor':"secondary",
        'majorSort':int(majorTaxDate[5:7])*100 + int(majorTaxDate[8:10]),
        'majorBadge':True,
        'major0':r[1],
        'major1':r[7],
        'major2':r[10], #                          법인:차감납부세액
        'major3':tmpMajor3, #                          법인:신고유형
        'major4':tmpMajor4, #format(int(r[8]),','),    법인:과표           개인:농특세
        'major5':tmpMajor5, #format(int(r[9]),','),    법인:농특세
        'major6':tmpMajor6,
        'major7':tmpMajor7,
        'major8':tmpMajor8,
        'major9':tmpMajor9
      }
      summitList.append(row)
  return summitList

def getTaxSchedule(memuser,context):
  context['monthNow'] = now.month
  if now.month==12:
    context['monthNext'] = str(now.year-2000+1)+"년 1"
  else:
    context['monthNext'] = now.month+1

  majorWork = [
    [1,{'desc':"부가가치세 신고납부기한",'dueDay':25}],
    [2,{'desc':"연말정산 자료제출",'dueDay':28}],
    [3,{'desc':"법인세 정기신고납부기한",'dueDay':31}],
    [4,{'desc':"부가가치세 신고납부기한",'dueDay':25}],
    [5,{'desc':"종합소득세 신고납부기한",'dueDay':31}],
    [6,{'desc':"성실신고 종합소득세 신고납부기한",'dueDay':30}],
    [7,{'desc':"부가가치세 신고납부기한",'dueDay':25}],
    [8,{'desc':"법인세 중간예납 신고납부기한",'dueDay':31}],
    [9,{'desc':"법인세 정기신고납부기한 - 6월말법인",'dueDay':30}],
    [10,{'desc':"부가가치세 신고납부기한",'dueDay':25}],
    [11,{'desc':"종합소득세 중간예납 신고납부기한",'dueDay':30}],
    [12,{'desc':"연말 가결산",'dueDay':31}],
    [13,{'desc':"부가가치세 신고납부기한",'dueDay':25}]
  ]
  for major in majorWork:
    if major[0]==now.month:
      context['majorNow'] = major[1]
    if major[0]==now.month+1:
      context['majorNext'] = major[1]

def getPresentTax(memuser,context):
  nowYear=now.year
  if now.month==1 and now.day<=10 :
    nowYear = now.year-1
  nowMonth = now.month  
  if now.month==1 and now.day<=10 :
    nowMonth = 12
  # 부가세 설정
  strsql_V = None
  if  memuser.biz_type<4:
    if nowMonth in [1,4,7,10]:
      strsql_V = "select '부가가치세' taxMok,'"+str(nowYear)+"년 "+str(nowMonth)+"월 25일' dueDate,납부환급세액 as dueAmt from 부가가치세전자신고3 where 사업자등록번호='"+memuser.biz_no+"' and left(과세기간,4)='"+str(nowYear)+"' and month(신고시각)="+str(nowMonth)
  else:
    if nowMonth in [1,7]:
      strsql_V = "select '부가가치세' taxMok,'"+str(nowYear)+"년 "+str(nowMonth)+"월 25일' dueDate,납부환급세액 as dueAmt from 부가가치세전자신고3 where 사업자등록번호='"+memuser.biz_no+"' and left(과세기간,4)='"+str(nowYear)+"' and month(신고시각)="+str(nowMonth)
  if strsql_V:
    print(strsql_V)
    cursor = connection.cursor()
    result_v = cursor.execute(strsql_V)
    result_V = cursor.fetchall()
    connection.commit()
    connection.close()
    nowTaxes=[]
    if result_V:
      wonchunRow = {'taxMok':result_V[0][0]
        ,'taxAmt': format(result_V[0][2],',')
        ,'taxDate':result_V[0][1][:2]+"월 "+result_V[0][1][4:6]+"일 "    }
      nowTaxes.append(wonchunRow)
    if nowTaxes:
      context['nowTaxes']= nowTaxes
      context['NowTaxMok'] = nowTaxes[0]['taxMok']
      context['NowTaxDate'] = nowTaxes[0]['taxDate']
      context['NowTaxAmt'] = nowTaxes[0]['taxAmt']    
  # 원천세 설정
  if now.day<25:
    nowMonth = nowMonth-1
  sql_wonchun = "select '원천세' taxMok,convert(INT,A99T) as dueAmt  ,'"+str(nowMonth+1)+"월 10일' dueDate from 원천세전자신고 where 사업자등록번호='"+memuser.biz_no+"' and 과세연월="+str(nowYear)+str(nowMonth)
  # print(sql_wonchun)
  cursor = connection.cursor()
  result = cursor.execute(sql_wonchun)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  nowTaxes=[]
  if result:
    wonchunRow = {'taxMok':result[0][0]
      ,'taxAmt': format(result[0][1],',')
      ,'taxDate':result[0][2][:2]+"월 "+result[0][2][4:6]+"일 "    }
    nowTaxes.append(wonchunRow)
  if nowTaxes:
    context['nowTaxes']= nowTaxes
    context['NowTaxMok'] = nowTaxes[0]['taxMok']
    context['NowTaxDate'] = nowTaxes[0]['taxDate']
    context['NowTaxAmt'] = nowTaxes[0]['taxAmt']

def getOlderTax(memuser,context):
  strsql = "select  '고지' as title, taxMok,taxAmt,taxNapbuNum,taxOffice,taxDuedate "
  strsql += " from tbl_goji where year(taxDuedate)="+str(now.year)+" and (month(taxDuedate)="+str(now.month)+" or (work_yy="+str(now.year)+" and work_mm="+str(now.month)+"))  and seq_no='"+memuser.seq_no+"'"
  strsql += " union all "
  strsql += " select  '체납' as title, taxMok,taxAmt,taxNapbuNum,taxOffice,taxDuedate "
  strsql += " from tbl_chenap where year(taxDuedate)="+str(now.year)+" and (month(taxDuedate)="+str(now.month)+" or (work_yy="+str(now.year)+" and work_mm="+str(now.month)+"))  and seq_no='"+memuser.seq_no+"'"
  strsql += " order by taxDuedate "
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  OlderTaxes = []
  if result:
    context['OlderTax'] = result[0][1]
    context['OlderTaxAmt'] = format(result[0][2],',')
    context['OlderTaxDate']= result[0][5][5:10].replace("-","월 ")+"일"
    for data in result:
      row = {'title':data[0]
        ,'taxMok':data[1]
        ,'taxAmt':data[2]
        ,'taxNum':data[3]
        ,'taxOffice':data[4]
        ,'taxDate':data[5][:4]+"년 "+data[5][5:7]+"월 "+data[5][8:10]+"일"
      }
      OlderTaxes.append(row)
    context['OlderTaxes']= OlderTaxes
    # print(row)
#get_key_from_mail과 세트. 메일을 읽을 때
def findEncodingInfo(txt):    
  info = email.header.decode_header(txt)
  s, encoding = info[0]
  return s, encoding

def getGMailList(memuser):
 
  global api_key
  sendto = 'daeseung23@gmail.com'
  user = 'daeseung23@gmail.com'
  password = "zrncmbdvtrphknoa"

  # 메일서버 로그인
  imapsrv = "smtp.gmail.com"
  #아래행 imap = imaplib.IMAP4_SSL('imap.gmail.com')에서 수정
  imap = imaplib.IMAP4_SSL(imapsrv, "993")
  id = user
  pw = password
  imap.login(id, pw)
  # for folder in imap.list():
  #   print(folder[1])
  #   print(type(folder))

  # typ, data = imap.search(None, '(FROM "memuser.")')
  # for num in data[0].split():
  #   typ, data = imap.fetch(num, '(RFC822)')
  #   print('Message %s\n%s\n' % (num, data[0][1]))

  imap_obj = imapclient.IMAPClient('imap.gmail.com', ssl=True)
  imap_obj.login(user, password)
  for i in imap_obj.list_folders():
    if i[2]==memuser.biz_name:
      imap_obj.select_folder(i[2])
      messages = imap_obj.search('ALL')
    # messages = server.search("UNSEEN")
      for uid, message_data in imap_obj.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        # email_message = email.message_from_bytes(message_data, policy=policy.default)
        #이메일 정보 keys
        #print(email_message.keys())
        print('FROM:', email_message['From'])
        print('SENDER:', email_message['Sender'])
        print('TO:', email_message['To'])
        print('DATE:', email_message['Date'])
   
        b, encode = findEncodingInfo(email_message['Subject'])
        subject = str(b, encode)
        print('SUBJECT:', subject)

        text = ''
        print('[CONTENT]')
        if email_message.is_multipart():
            for part in email_message.get_payload():
                bytes = part.get_payload(decode = True)    
                encode = part.get_content_charset()    
                # print(bytes.decode('utf-8'))
                # if bytes is not None:  
                #   print(str(bytes, encode))
                #   text=str(bytes, encode)
                # # break
        print('='*80)