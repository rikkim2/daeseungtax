from __future__ import print_function 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection
import os
import json
from app.models import MemUser
from app.models import MemAdmin
from app.models import MemDeal
from app.models import userProfile
selectedYear=""
@login_required(login_url="/login/")
def index(request):
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  if memuser.biz_type<4:
    context['isCorp'] = True
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if userprofile:
    userprofile = userprofile.latest('description')
  if userprofile is not None:
    context['userProfile'] = userprofile
  
  context['memuser'] = memuser
  context['statementYears'] = setStatementYears(memuser.user_id)
  context['selectedYear'] =selectedYear
  context['kejungList'] =getKejungList(memuser.user_id,selectedYear)

  return render(request, "Ledgrs/traderLedgr.html",context)

@csrf_exempt
def getTraderDetailGrid(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  selYear = request.GET.get('selYear',False)
  selAcntcd = request.GET.get('selAcntcd',False)
  Trd_Cd = request.GET.get('Trd_Cd',False)

  strsql = "Select Trader_Code, slip_no, tran_dt,  remk, 0 Start, tranAmt_Cr, tranAmt_Dr  	 "                    
  strsql += "from DS_SlipLedgr2 "
  strsql += "where work_yy = '"+selYear+"' and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"'  and Trader_Code='"+str(Trd_Cd)+"' "
  strsql += "        and cncl_Dt = '' and tran_dt <> '00-00' "
  strsql += "union all "	
  strsql += "Select Trader_Code  , ''  ,  '' , '[ 전 기 이 월 ]'  	"
  strsql += ", isnull(Sum(Case When Acnt_cd> = 101 and acnt_cd<=250 Then tranAmt_Cr-tranAmt_Dr "
  strsql += "        When Acnt_cd>= 251 and acnt_cd<=330 Then tranAmt_Dr-tranAmt_Cr  end),0) , 0  , 0  " 
  strsql += "from DS_SlipLedgr2 "
  strsql += "where work_yy < '"+selYear+"' and seq_no = '"+memuser.seq_no+"' and acnt_cd = '"+selAcntcd+"' and Trader_Code='"+str(Trd_Cd)+"' "
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
  mem_deal = MemDeal.objects.get(seq_no=memuser.seq_no)
  selYear = request.GET.get('selYear',False)
  selAcntcd = request.GET.get('selAcntcd',False)
  # if request.method == 'POST':
  #   selYear = request.POST['selYear']
  #   selAcntcd = request.POST['selAcntcd']

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
  rtnJson["rowDuration"]=getLastFiscalDate(memuser.seq_no,selYear,mem_deal.fiscalmm)
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


def getKejungList(user_id,work_yy):
  strsql = "select  a.work_yy work_yy,a.acnt_cd acnt_cd, a.acnt_nm from DS_slipledgr2 A "
  strsql += " where A.seq_no=(select seq_no from mem_user where user_id='"+user_id+"') "
  strsql += "  and A.work_yy='"+work_yy+"'"
  strsql +=  " and (a.acnt_cd<=145  "		
  strsql +=  " or (a.acnt_cd>=176 and a.acnt_cd<=194) "		
  strsql +=  " or (a.acnt_cd>=231 and a.acnt_cd<=330)) "		
  strsql +=  " and a.acnt_cd not in ('101','135','138','254','255') "
  strsql +=  " group by a.work_yy,a.acnt_cd,a.acnt_nm"
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  resultArr = []
  if result:
    for r in result:
      row={
        'acnt_cd':r[1],
        'acnt_nm':r[2]
      }
      resultArr.append(row)
  return resultArr

def setStatementYears(user_id):
  global selectedYear
  
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
  return resultArr

def getLastFiscalDate(seq_no,work_yy,fiscalmm):
  strsql = "select max(tran_dt) from DS_SlipLedgr2 where seq_no="+seq_no+" and work_yy="+work_yy
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  if result:
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
  return row
  
def setSelectedYear(request):
  global selectedYear
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  selectedKejung = request.GET.get('selectedKejung',False)
  if selectedKejung==False:
    context['selectedYear'] =selectedYear
    context['kejungList'] =getKejungList(memuser.user_id,selectedYear)
  else:
    context['kejungList'] =getKejungList(memuser.user_id,selectedYear)

  return JsonResponse(context,safe=False)