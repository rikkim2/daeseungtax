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
  # context['kejungList'] =getKejungList(memuser.user_id,selectedYear)

  return render(request, "Ledgrs/slipLedgr.html",context)


@csrf_exempt
def setLedgrGrid(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  mem_deal = MemDeal.objects.get(seq_no=memuser.seq_no)
  selYear = request.GET.get('selYear',False)
  selAcntcd = request.GET.get('selAcntcd',False)

  totfileArr = []
  strsql = "select left(Tran_dt,2),max(Remk),sum(TranAmt_Cr),sum(TranAmt_Dr) "
  strsql += " from DS_slipledgr2  with(index(IDX1_ds_slipledgr2), nolock)  "
  strsql += " where seq_no=" + memuser.seq_no
  strsql += "  and work_yy=" + str(selYear)
  strsql += "  and acnt_cd='" + str(selAcntcd)+"'"
  strsql += "  group by left(Tran_dt,2) order by left(Tran_dt,2)";  
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = []
  cnt=1  
  if result:
    for r in result:
      tmpMM=""
      if(r[0]=="00"):
        tmpMM=r[1]
      else:
        tmpMM=str(int(r[0]))+"월"
      row={
        'Real_MM':r[0],
        'Work_MM':tmpMM,
        'TranAmt_Cr':r[2],
        'TranAmt_Dr':r[3],
        'TranAmt_Sum':transum(int(selAcntcd),int(r[2]),int(r[3]),0),
        'acnt_cd':str(selAcntcd)
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr    
  rtnJson["rowDuration"]=getLastFiscalDate(memuser.seq_no,selYear,mem_deal.fiscalmm)
  totSum=0
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getLedgrDetail(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  selYear2 = request.GET.get('selYear2')
  selAcntcd = request.GET.get('selAcntcd')
  selMM = request.GET.get('selMonth')
  startNum = request.GET.get('startNum')

  totfileArr = []
  strsql = "select Tran_Dt,Remk,Trader_Name,Slip_No,TranAmt_Cr,TranAmt_Dr,Trader_Code "
  strsql += " from DS_slipledgr2  with(index(IDX1_ds_slipledgr2), nolock)  "
  strsql += " where seq_no="+memuser.seq_no
  strsql += "  and work_yy="+selYear2
  strsql += "  and acnt_cd='"+str(selAcntcd)+"'"
  strsql += "  and left(Tran_Dt,2)='"+selMM+"'"
  strsql += "  order by tran_dt";  
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = [] 
  cnt=1  
  if result:
    for r in result:
      if cnt>1:startNum=0
      row={
        'Tran_Dt':r[0],
        'Remk':r[1],
        'Trader_Name':r[2],
        'Slip_No':r[3],
        'TranAmt_Cr':r[4],
        'TranAmt_Dr':r[5],
        'TranAmt_Sum':transum(int(selAcntcd),int(r[4]),int(r[5]),int(startNum)),
        'Trader_Code':r[6]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rows"]=totfileArr    
  totSum=0
  return JsonResponse(rtnJson,safe=False)
totSum=0
def transum(acnt_cd,a,b,s):
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

@csrf_exempt
def getLedgrMoreDetail(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  selYear2 = request.GET.get('selYear2')
  slip_no = request.GET.get('slip_no')
  Tran_Dt = request.GET.get('Tran_Dt')

  totfileArr = []
  strsql = "select work_yy,Tran_Dt,crdr,acnt_nm,Trader_Name,TranAmt_Cr,TranAmt_Dr,Remk,Tran_Stat "
  strsql += " from DS_slipledgr2  with(index(IDX1_ds_slipledgr2), nolock)  "
  strsql += " where seq_no="+memuser.seq_no
  strsql += "  and work_yy="+selYear2
  strsql += "  and tran_dt='"+Tran_Dt+"'"
  strsql += "  and slip_no='"+slip_no+"'"
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = [] 
  cnt=1  
  if result:
    for r in result:
      if cnt>1:startNum=0
      row={
        'Tran_Dt':r[1],
        'CrDr':r[2],
        'Acnt_Nm':r[3],
        'Trader_Name':r[4],
        'TranAmt_Cr':r[5],
        'TranAmt_Dr':r[6],
        'Remk':r[7],
        'Tran_Stat':r[8]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rows"]=totfileArr    
  totSum=0
  return JsonResponse(rtnJson,safe=False)

@csrf_exempt
def getYearlyTradeLedgr(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  Trader_Code = request.GET.get('Trader_Code')
  totfileArr = []
  strsql = "select work_yy,acnt_cd,max(acnt_nm) ,sum(tranAmt_Cr), sum(tranAmt_Dr)   "
  strsql += " from DS_slipledgr2  with(index(IDX1_ds_slipledgr2), nolock)  "
  strsql += " where seq_no="+memuser.seq_no
  strsql += "  and Trader_Code='"+Trader_Code+"'"
  strsql += "  and cncl_Dt = '' and tran_dt <> '00-00'  group by work_yy,acnt_cd order by work_yy,acnt_cd"
  # print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = [] 
  cnt=1;start_sum=0;end_sum=0
  if result:
    for r in result:
      if cnt==1:start_sum=0
      row={
        'work_yy':r[0],
        'acnt_cd':r[1],
        'acnt_nm':r[2],
        'TranAmt_Cr':r[3],
        'TranAmt_Dr':r[4]
      }
      totfileArr.append(row)
      cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rows"]=totfileArr    
  totSum=0
  return JsonResponse(rtnJson,safe=False)  

@csrf_exempt
def getYearlyTradeDetail(request):
  global totSum
  memuser = MemUser.objects.get(user_id=request.user.username)
  selAcntcd = request.GET.get('selAcntcd')
  Trader_Code = request.GET.get('Trader_Code')
  totfileArr = []
  strsql = "select work_yy ,sum(tranAmt_Cr), sum(tranAmt_Dr)  "
  strsql += " from DS_slipledgr2  with(index(IDX1_ds_slipledgr2), nolock)  "
  strsql += " where seq_no="+memuser.seq_no
  strsql += "  and acnt_cd="+selAcntcd
  strsql += "  and Trader_Code='"+Trader_Code+"'"
  strsql += "  and cncl_Dt = '' and tran_dt <> '00-00'  group by work_yy order by work_yy"
  # print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  totfileArr = [] 
  cnt=1;start_sum=0;end_sum=0
  if result:
    for r in result:
      if cnt==1:start_sum=0
      if int(selAcntcd)<=250:
        end_sum = start_sum + r[1] - r[2]
      else:
        end_sum = start_sum - r[1] + r[2]
      row={
        'work_yy':r[0],
        'Start_Amt':start_sum,
        'TranAmt_Cr':r[1],
        'TranAmt_Dr':r[2],
        'End_Amt':end_sum
      }
      totfileArr.append(row)
      cnt = cnt + 1
      start_sum = end_sum
  rtnJson = {"current":1}
  rtnJson["rows"]=totfileArr    
  totSum=0
  return JsonResponse(rtnJson,safe=False)  

# def getKejungList(user_id,work_yy):
def getKejungList(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  work_yy = request.GET.get('selYear')
  strsql = "select max(A.work_yy) work_yy,A.acnt_cd acnt_cd, max(A.acnt_nm) acnt_nm,count(*) from DS_slipledgr2 A "
  strsql += " where A.seq_no=(select seq_no from mem_user where user_id='"+memuser.user_id+"') "
  strsql += "  and A.work_yy='"+work_yy+"'"
  strsql += "  group by A.acnt_cd  order by A.acnt_cd ";    
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
      if  int(r[1])<384 and r[3]<=1 and totSum==0:
        a=0
      else:
        resultArr.append(row)
  rtnJson = {"current":1}
  rtnJson["rows"]=resultArr  
  return JsonResponse(rtnJson,safe=False)
  # return resultArr


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
  #   context['kejungList'] =getKejungList(memuser.user_id,selectedYear)
  # else:
  #   context['kejungList'] =getKejungList(memuser.user_id,selectedYear)

  return JsonResponse(context,safe=False)