from __future__ import print_function 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
import os
import datetime
import time
from app.models import MemUser
from app.models import MemDeal
from app.models import userProfile
selectedYear="";selectedKi=""
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
  context['statementYears'] = setStatementYears(memuser.user_id)
  context['selectedYear'] =selectedYear
  context['selectedKi'] =selectedKi
  # getFinancialData(memuser.seq_no,context)
  return render(request, "statementMajor/statementBS.html",context)


@csrf_exempt
def getFinancialData(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  seq_no = memuser.seq_no
  flag = request.GET.get('flag',False)
  selYear = request.GET.get('selYear',False)
  now = datetime.datetime.now()
  A00 = [0, 0, 0, 0, 0, 0]	#자산총액
  A10 = [0, 0, 0, 0, 0, 0]	#유동자산
  A20 = [0, 0, 0, 0, 0, 0]	#고정자산
  B00 = [0, 0, 0, 0, 0, 0]	#부채총액
  B10 = [0, 0, 0, 0, 0, 0]	#유동부채
  B20 = [0, 0, 0, 0, 0, 0]	#고정부채
  C00 = [0, 0, 0, 0, 0, 0]	#자본총액
  C10 = [0, 0, 0, 0, 0, 0]	#자본금
  Z108 = [0, 0, 0, 0, 0, 0] #매출채권
  Z260 = [0, 0, 0, 0, 0, 0] #단기차입금
  Z293 = [0, 0, 0, 0, 0, 0] #장기차입금

  E10 = [0, 0, 0, 0, 0, 0]  #매출액
  F10 = [0, 0, 0, 0, 0, 0]  #매출원가
  H10 = [0, 0, 0, 0, 0, 0]  #판관비
  J10 = [0, 0, 0, 0, 0, 0]  #영업이익
  L10 = [0, 0, 0, 0, 0, 0]  #영업외비용
  N10 = [0, 0, 0, 0, 0, 0]  #법인세차감전이익
  O10 = [0, 0, 0, 0, 0, 0]  #법인세비용
  Q10 = [0, 0, 0, 0, 0, 0]  #당기순이익

  for i in range(0,6,2):
    strsql = "exec up_Act_BSInquiry '"+str(now.year-i)+"','"+seq_no+"' "  
    cursor = connection.cursor()
    result = cursor.execute(strsql)
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    if result:
      for r in result:
        acnt_cd		= r[0]
        rightAmt = r[2]
        rightAmt_pre= r[3]
        if acnt_cd == "A00" :
          A00[i] = rightAmt;
          A00[i+1] = rightAmt_pre
        elif acnt_cd == "A10" :
          A10[i] = rightAmt	#유동자산
          A10[i+1] = rightAmt_pre	#유동자산
        elif acnt_cd == "A20" :
          A20[i] = rightAmt	#고정자산
          A20[i+1] = rightAmt_pre	#고정자산
        elif acnt_cd == "B00" :
          B00[i] = rightAmt	#부채총액
          B00[i+1] = rightAmt_pre	#부채총액
        elif acnt_cd == "B10" :
          B10[i] = rightAmt	#유동부채
          B10[i+1] = rightAmt_pre	#유동부채
        elif acnt_cd == "B20" :
          B20[i] = rightAmt	#고정부채
          B20[i+1] = rightAmt_pre	#고정부채
        elif acnt_cd == "C00" :
          C00[i] = A00[i] - B00[i]	#자본총액
          C00[i+1] = A00[i+1] - B00[i+1]	#자본총액
          if C00[i]== 0 : C00[i]=1
          if C00[i+1]== 0 : C00[i+1]=1
        elif acnt_cd == "C10" :
          C10[i] = 1 if rightAmt==0  else rightAmt 
          C10[i+1] = 1 if rightAmt_pre==0  else rightAmt_pre 				
        elif acnt_cd == "108" :
          Z108[i] = rightAmt	
          Z108[i+1] = rightAmt_pre	
        elif acnt_cd == "260" :
          Z260[i] = rightAmt	
          Z260[i+1] = rightAmt_pre	
        elif acnt_cd == "293" :
          Z293[i] = rightAmt	
          Z293[i+1] = rightAmt_pre	
  for i in range(0,6,2):
    strsql = "exec up_Act_PLInquiry '"+str(now.year-i)+"','"+seq_no+"' "  
    cursor = connection.cursor()
    result = cursor.execute(strsql)
    result = cursor.fetchall()
    connection.commit()
    connection.close()
    if result:
      for r in result:
        acnt_cd		= r[0]
        rightAmt = r[2]
        rightAmt_pre= r[3]          
        if acnt_cd == "E10" :
          E10[i] = rightAmt	
          E10[i+1] = rightAmt_pre	
        elif acnt_cd == "F10" :
          F10[i] = rightAmt	
          F10[i+1] = rightAmt_pre	
        elif acnt_cd == "H10" :
          H10[i] = rightAmt	
          H10[i+1] = rightAmt_pre	
        elif acnt_cd == "J10" :
          J10[i] = rightAmt	
          J10[i+1] = rightAmt_pre	
        elif acnt_cd == "L10" :
          L10[i] = rightAmt	
          L10[i+1] = rightAmt_pre	
        elif acnt_cd == "N10" :
          N10[i] = rightAmt	
          N10[i+1] = rightAmt_pre	
        elif acnt_cd == "Q10" :
          if i==0 :
            Q10[i] = N10[i] - O10[i]
            Q10[i+1] = N10[i+1] - O10[i+1]
          else:
            Q10[i] = rightAmt	#당기순이익
            Q10[i+1] = rightAmt_pre	#당기순이익
  #법인세/종소세비용
  for i in range(0,6):  
    if int(memuser.biz_type)<4:
      strsql = "select left(사업연도말,4) "
      strsql += " ,CASE WHEN ISNULL(법인세,'') = '' THEN 0 ELSE  CAST(법인세 AS BIGINT) END 법인세 "
      strsql += " ,CASE WHEN ISNULL(지방세,'') = '' THEN 0 ELSE  CAST(지방세 AS BIGINT) END 지방세 "
      strsql += " ,CASE WHEN ISNULL(농특세,'') = '' THEN 0 ELSE   left(농특세,15) END 농특세 "
      strsql += " from tbl_EquityEval where 사업자번호='"+memuser.biz_no+"' order by 사업연도말 desc "  
      cursor = connection.cursor()
      result = cursor.execute(strsql)
      result = cursor.fetchall()
      connection.commit()
      connection.close()
      if result:
        for r in result:
          if str(now.year-i)==r[0]:
            tmpTax = int(r[1])+int(r[2])+int(r[3])
            print(tmpTax)
            O10[i] = tmpTax
    else:
      strsql = "select b.work_yy, "  
      strsql += " CASE WHEN ISNULL(종합소득_합계,'') = '' THEN 0 ELSE case when left(종합소득_합계,1)='-' then (-1)&substring(종합소득_합계,1,len(종합소득_합계)) else 종합소득_합계 end END 종합소득_합계 , "
      strsql += " CASE WHEN ISNULL(지방소득세_신고기한내납부할세액,'') = '' THEN 0 ELSE case when left(지방소득세_신고기한내납부할세액,1)='-' then (-1)&substring(지방소득세_신고기한내납부할세액,1,len(지방소득세_신고기한내납부할세액)) else 지방소득세_신고기한내납부할세액 end END 지방소득세_신고기한내납부할세액 , "
      strsql += " yn_4/10 지방세중간예납, "
      strsql += " CASE WHEN ISNULL(농특세_합계,'') = '' THEN 0 ELSE case when left(농특세_합계,1)='-' then (-1)&substring(농특세_합계,1,len(농특세_합계)) else 농특세_합계 end END 농특세_합계 "
      strsql += " from mem_user a,elec_income b,tbl_income2 c "
      strsql += " where a.ssn='"+memuser.ssn+"' "
      strsql += " and a.ssn=b.ssn and a.seq_no=c.seq_no and b.work_yy=c.work_yy"
      strsql += " order by c.work_yy desc     "
      cursor = connection.cursor()
      result = cursor.execute(strsql)
      result = cursor.fetchall()
      connection.commit()
      connection.close()
      if result:
        for r in result:
          if str(now.year-i)==r[0]:
            tmpTax = int(r[1])+int(r[2])+int(r[3])+int(r[4])
            O10[i] = tmpTax
  currentRatioA = {}  #유동비율
  currentRatioR = {}  #부채비율
  saleCostYears = []  #연도별매출/비용
  totalData = []
  for i in range(0,6):
    currentRA = 0;currentRR = 0;curRatio1=0;curRatio2=0;curRatio3=0;curRatio4=0;curRatio5=0;curRatio6=0
    try:currentRA = round(A10[i]/B10[i]*100,2)  #유동비율
    except:currentRA = ''
    try:currentRR = round(B00[i]/C00[i]*100,2)  #부채비율
    except:currentRR = ''
    try:curRatio1 = round(A10[i]/A00[i]*100,2)  #유동자산비율
    except:curRatio1 = ''
    try:curRatio2 = round(C00[i]/(C00[i]+B00[i])*100,2)  #자기자본비율
    except:curRatio2 = ''
    try:curRatio3 = round((Z260[i]+Z293[i])/A00[i]*100,2)  #차입금의존도
    except:curRatio3 = ''
    try:curRatio5 = round((C00[i]-C00[i+1])/C00[i+1]*100,2)  #자기자본증가율
    except:curRatio5 = ''
    try:curRatio6 = round((A00[i]-A00[i+1])/A00[i+1]*100,2)  #총자산증가율
    except:curRatio6 = ''
    row = [
      {
        'year':str(now.year-i),
        'curRatioA':str(currentRA),  #유동비율
        'curRatioR':str(currentRR),  #부채비율
        'curRatio1':str(curRatio1),  #유동자산비율
        'curRatio2':str(curRatio2),  #자기자본비율
        'curRatio3':str(curRatio3),  #차입금의존도
        'curRatio5':str(curRatio5),  #자기자본증가율
        'curRatio6':str(curRatio6),  #총자산증가율
        'A00':str(A00[i]),
        'A10':str(A10[i]),
        'A20':str(A20[i]),
        'B00':str(B00[i]),
        'B10':str(B10[i]),
        'B20':str(B20[i]),
        'C00':str(C00[i]),
        'C10':str(C10[i]),
        'Z108':str(Z108[i]),
        'Z260':str(Z260[i]),
        'Z293':str(Z293[i]),
        'E10' : str(E10[i]),  #매출액
        'F10' : str(F10[i]),  #매출원가
        'H10' : str(H10[i]),  #판관비
        'J10' : str(J10[i]),  #영업이익
        'L10' : str(L10[i]),  #영업외비용
        'N10' : str(N10[i]),  #법인세차감전이익
        'O10' : str(O10[i]),  #법인세비용
        'Q10' : str(Q10[i])  #당기순이익
      }
    ]
    totalData.append(row)
    currentRatioA[str(now.year-i)] = [{'sector':'유동자산','size':str(A10[i])},{'sector':'유동부채','size':str(B10[i])}]
    currentRatioR[str(now.year-i)] = [{'sector':'부채총액','size':str(B00[i])},{'sector':'자본총액','size':str(C00[i])}]
    saleCostYears.append({'year':str(now.year-i),'income':str(E10[i]),'expenses':str(E10[i]-N10[i])})
    # resultArr[str(now.year-i)]=row
  rtnJson = {"current":1}
  rtnJson["totalData"] = totalData
  rtnJson["currentRatioA"] = currentRatioA
  rtnJson["currentRatioR"] = currentRatioR
  rtnJson["saleCostYears"] = saleCostYears
  return JsonResponse(rtnJson,safe=False)
  

@csrf_exempt
def getStatementList(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  mem_deal = MemDeal.objects.get(seq_no=memuser.seq_no)
  selYear = request.GET.get('selYear',False)
  flag = request.GET.get('flag',False)
  strsql = "exec up_Act_"+flag+"Inquiry '"+selYear+"','"+memuser.seq_no+"' "
  time1 = time.time()
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  resultArr = []
  time2 = time.time()
  if result:
    for r in result:
      row = {}
      if flag=="CS":
        row={
          'acnt_cd':r[2],
          'acnt_nm':r[3],
          'amt_now':str(r[4]),
          'amt_bef':str(r[5])
        }        
      else:
        row={
          'acnt_cd':r[0],
          'acnt_nm':r[1],
          'amt_now':str(r[2]),
          'amt_bef':str(r[3])
        }
      resultArr.append(row)
  time3 = time.time()
  print("1 실행 시간: ",time1, "초")
  print("2 실행 시간: ",time2, "초")
  print("3 실행 시간: ",time3, "초")
  rtnJson = {"current":1}
  print(f'fiscalmm?{mem_deal.fiscalmm}')
  rtnJson["rowDuration"]=getLastFiscalDate(memuser.seq_no,selYear,mem_deal.fiscalmm)
  print('Duration?')
  rtnJson["rows"]=resultArr   
  print('resultArr?')
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getTraderDetailGrid(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  selYear = request.GET.get('selYear',False)
  selAcntcd = request.GET.get('selAcntcd',False)
  Trd_Cd = request.GET.get('Trd_Cd',False)

  strsql = "Select Trader_Code, slip_no, tran_dt,  remk, 0 Start, tranAmt_Cr, tranAmt_Dr  	 "                    
  strsql += "from DS_SlipLedgr2 "
  strsql += "where work_yy = '"+selYear+"' and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"'  and Trader_Code='"+Trd_Cd+"' "
  strsql += "        and cncl_Dt = '' and tran_dt <> '00-00' "
  strsql += "union all "	
  strsql += "Select Trader_Code  , ''  ,  '' , '[ 전 기 이 월 ]'  	"
  strsql += ", Sum(Case When Acnt_cd> = 101 and acnt_cd<=250 Then tranAmt_Cr-tranAmt_Dr "
  strsql += "        When Acnt_cd>= 251 and acnt_cd<=330 Then tranAmt_Dr-tranAmt_Cr  end) , 0  , 0  " 
  strsql += "from DS_SlipLedgr2 "
  strsql += "where work_yy < '"+selYear+"' and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"' and Trader_Code='"+Trd_Cd+"' "
  strsql += "    and cncl_Dt = '' and tran_dt <> '00-00' "	
  strsql += "Group by  Trader_Code,Trader_Bizno	"
  strsql += "order by tran_dt"
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
        'Trader_Code':r[0],
        'slip_no':r[1],
        'tran_dt':r[2],
        'remk':r[3],
        'TStart':r[4],
        'tranAmt_Cr':r[5],
        'tranAmt_Dr':r[6],
        'tranAmt_Sum':transum(int(selAcntcd),int(r[4]),int(r[5]),int(r[6]))
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr   
  # print(totfileArr)
  totSum=0 
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getTraderGrid(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  selYear = request.GET.get('selYear',False)
  selAcntcd = request.GET.get('selAcntcd',False)

  totfileArr = []
  strsql = "Select X.거래처코드 Trd_Cd "
  strsql += ", MAX(X.거래처명) CompanyName "
  strsql += ", sum(X.전기이월)    TStart "
  strsql += ", sum(X.차변)    TCr "
  strsql += ", sum(X.대변)    TDr "
  strsql += ", SUM(CASE WHEN X.acnt_cd<=250 or X.acnt_cd>=451 and not (X.acnt_cd>=901 and X.acnt_cd<=950) THEN X.전기이월 + X.차변 - X.대변 ELSE X.전기이월 + X.대변 - X.차변 end )  TEnd "
  strsql += " from ( "
  strsql += "       Select acnt_cd, Trader_Code 거래처코드 "
  strsql += "            , trader_name 거래처명 "
  strsql += "            , 0 전기이월 "
  strsql += "            , isnull(sum(Case When  tran_dt <> '00-00'	Then tranAmt_Cr end), 0) 차변 	"
  strsql += "            , isnull(sum(Case When  tran_dt <> '00-00'	Then tranAmt_Dr end), 0) 대변 	"
  strsql += "       from DS_SlipLedgr2 "
  strsql += "       where work_yy = '"+selYear+"' and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"' "
  strsql += "       and cncl_Dt = '' and  tran_dt <> '00-00'"
  strsql += "       group by acnt_cd, trader_code, trader_name "
  strsql += "       union all "
  strsql += "       Select acnt_cd, Trader_Code 거래처코드 "
  strsql += "            , trader_name 거래처명 "
  strsql += "            , SUM(CASE WHEN acnt_cd<=250 or acnt_cd>=451 and not (acnt_cd>=901 and acnt_cd<=950) THEN tranAmt_Cr - tranAmt_Dr ELSE tranAmt_Dr - tranAmt_Cr  end ) 전기이월 	"
  strsql += "            , 0 차변 "
  strsql += "            , 0 대변 "
  strsql += "       from DS_SlipLedgr2 "
  strsql += "       where work_yy <= ("+selYear+"-1) and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"' "
  strsql += "       and cncl_Dt = '' and  tran_dt <> '00-00'	"
  strsql += "       group by acnt_cd, trader_code, trader_name "
  strsql += "   ) X  "
  strsql += "group by X.거래처코드 "
  strsql += "HAVING SUM(CASE WHEN X.acnt_cd<=250 or X.acnt_cd>=451 and not (X.acnt_cd>=901 and X.acnt_cd<=950) THEN X.전기이월 + X.차변 - X.대변 ELSE X.전기이월 + X.대변 - X.차변 end ) <> 0 "
  strsql += "order by 거래처코드   "  
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
        'Trd_Cd':r[0],
        'CompanyName':r[1],
        'TStart':r[2],
        'TCr':r[3],
        'TDr':r[4],
        'TEnd':r[5]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr    
  return JsonResponse(rtnJson,safe=False)

totSum=0
def transum(acnt_cd,s,a,b):
  global totSum
  if acnt_cd<251:
    totSum = totSum +  a - b + s
  elif acnt_cd<431:
    totSum = totSum -  a + b + s
  elif acnt_cd<901:
    totSum = totSum + a - b  + s
  elif acnt_cd<951:
    totSum = totSum -  a + b + s  
  else:
    totSum = totSum + a - b + s     
  return totSum

def getLastFiscalDate(seq_no,work_yy,fiscalmm):
  strsql = f"select top 1 max(tran_dt) from DS_SlipLedgr2 where seq_no={seq_no} and work_yy={work_yy}  group by tran_dt order by tran_dt desc"
  print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  if result:
    print(f"Maxdate:{result[0][0]}")
    start_date="";end_date=""
    if fiscalmm=="12":
      start_date = "1월 1일"
      thisEndDate = result[0][0].replace("-","월 ")+"일"
      lastEndDate = "12월 31일"
    elif fiscalmm=="3":
      start_date = str(int(fiscalmm)+1) + "월 1일"
      thisEndDate = "3월 31일"
      lastEndDate = "3월 31일"
    elif fiscalmm=="6":
      start_date = str(int(fiscalmm)+1) + "월 1일"
      thisEndDate = "6월 30일"
      lastEndDate = "6월 30일"
    row = {
      'start_dt':start_date,
      'thisEndDate':thisEndDate,
      'lastEndDate':lastEndDate
    }
    print('getLastFiscalDate 이상없음')
  return row

def setStatementYears(user_id):
  global selectedYear
  global selectedKi
  
  strsql = "SELECT a.work_yy as work_yy,(a.work_yy-year(b.reg_date)+1) as ki "
  strsql += " from Ds_slipledgr2 a, mem_user b "
  strsql += " where a.seq_no=b.seq_no and b.user_id='"+user_id+"' "
  strsql += " group by a.work_yy,year(b.reg_date) order by a.work_yy desc";
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  resultArr = []
  if result:
    for r in result:
      row={
        'work_yy':r[0],
        'ki':r[1]
      }
      resultArr.append(row)
    selectedYear = resultArr[0]['work_yy']
    selectedKi = resultArr[0]['ki']
  return resultArr


def setSelectedYear(request):
  global selectedYear
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  selectedKejung = request.GET.get('selectedKejung',False)
  if selectedKejung==False:
    context['selectedYear'] =selectedYear
    context['statementList'] =getStatementList(memuser.user_id,'BS',selectedYear)
  else:
    context['statementList'] =getStatementList(memuser.user_id,'BS',selectedYear)

  return JsonResponse(context,safe=False)