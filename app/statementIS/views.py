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
  mem_deal = MemDeal.objects.get(seq_no=memuser.seq_no)
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
  context['selectedKi'] =selectedKi
  context['fiscalMM'] = getLastFiscalDate(memuser.seq_no,selectedYear,mem_deal.fiscalmm)['fiscalMM']
  getCostFinancialData(memuser.seq_no,context)
  return render(request, "statementMajor/statementIS.html",context)

def getCostFinancialData(seq_no,context):
  # memuser = MemUser.objects.get(user_id=request.user.username)
  # seq_no = memuser.seq_no
  cnt=0;firstYear=""
  costYears = {}
  strsql = "select work_yy from ds_slipledgr2 where seq_no="+seq_no+" group by work_yy order by work_yy"
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  result = cursor.fetchall()
  connection.commit()
  connection.close()
  if result:
    cost=[]
    for year in result:
      if cnt==0:firstYear=str(year[0])
      cost = [0 for i in range(17)]
      strsql = "exec up_Act_PLInquiry '"+str(year[0])+"','"+seq_no+"' "  
      cursor = connection.cursor()
      result = cursor.execute(strsql)
      result = cursor.fetchall()
      connection.commit()
      connection.close()
      if result:
        for r in result:
          acnt_cd = r[0]
          if acnt_cd.isnumeric():  
            acnt_cd		= int(r[0])
            acnt_nm = r[1].replace(" ","")
            thisAmt = int(r[2])
            if acnt_cd==462: cost[0] = thisAmt
            elif acnt_cd>=801 and acnt_cd<=810: cost[1] += thisAmt
            elif acnt_cd==811: cost[2] = thisAmt
            elif acnt_cd==812: cost[3] = thisAmt
            elif acnt_cd==813: cost[4] = thisAmt
            elif acnt_cd==814: cost[5] = thisAmt
            elif acnt_cd==815 or acnt_cd==816: cost[6] += thisAmt
            elif acnt_cd==817: cost[7] = thisAmt
            elif acnt_cd==818: cost[8] = thisAmt
            elif acnt_cd==819: cost[9] = thisAmt
            elif acnt_cd==821: cost[10] = thisAmt
            elif acnt_cd==822: cost[11] = thisAmt
            elif acnt_cd==830: cost[12] = thisAmt
            elif acnt_cd==831: cost[13] = thisAmt
            elif acnt_cd==823: cost[14] = thisAmt
            elif acnt_cd>823 and acnt_nm=="외주비": cost[15] = thisAmt
            elif acnt_cd>823 and acnt_cd<850: cost[16] += thisAmt
            # print(str(year) + " : " + acnt_nm + " : " + str(acnt_cd) + " : " + str(r[2]))
            # print(str(year) + " : " + acnt_nm + " : " + str(acnt_cd) + " : " + str(cost[1]))

      strsql = "exec up_Act_CSInquiry '"+str(year[0])+"','"+seq_no+"' "   
      cursor = connection.cursor()
      result = cursor.execute(strsql)
      result = cursor.fetchall()
      connection.commit()
      connection.close()
      if result:
        for c in result:
          acnt_cdC		= c[2]
          if acnt_cdC.isnumeric():  
            acnt_cdC		= int(c[2])
            acnt_nmC = c[3].replace(" ","")
            thisAmtC = int(c[4])
            if acnt_cdC==598 or acnt_cdC==698: cost[0] += thisAmtC
            elif (acnt_cdC>=503 and acnt_cdC<=510) or (acnt_cdC>=602 and acnt_cdC<=610) or (acnt_cdC>=703 and acnt_cdC<=710): cost[1] += thisAmtC
            elif acnt_cdC==511 or acnt_cdC==611 or acnt_cdC==661 or acnt_cdC==711 or acnt_cdC==761: cost[2] += thisAmtC
            elif acnt_cdC==512 or acnt_cdC==612 or acnt_cdC==662 or acnt_cdC==712 or acnt_cdC==762: cost[3] += thisAmtC
            elif acnt_cdC==513 or acnt_cdC==613 or acnt_cdC==663 or acnt_cdC==713 or acnt_cdC==763: cost[4] += thisAmtC
            elif acnt_cdC==514 or acnt_cdC==614 or acnt_cdC==664 or acnt_cdC==714 or acnt_cdC==764: cost[5] += thisAmtC
            elif acnt_cdC==515 or acnt_cdC==615 or acnt_cdC==665 or acnt_cdC==715 or acnt_cdC==765 : cost[6] += thisAmtC
            elif acnt_cdC==516 or acnt_cdC==616 or acnt_cdC==666 or acnt_cdC==716 or acnt_cdC==766 : cost[6] += thisAmtC
            elif acnt_cdC==517 or acnt_cdC==617 or acnt_cdC==667 or acnt_cdC==717 or acnt_cdC==767: cost[7] += thisAmtC
            elif acnt_cdC==518 or acnt_cdC==618 or acnt_cdC==668 or acnt_cdC==718 or acnt_cdC==768: cost[8] += thisAmtC
            elif acnt_cdC==519 or acnt_cdC==619 or acnt_cdC==669 or acnt_cdC==719 or acnt_cdC==769: cost[9] += thisAmtC
            elif acnt_cdC==521 or acnt_cdC==621 or acnt_cdC==671 or acnt_cdC==721 or acnt_cdC==771: cost[10] += thisAmtC
            elif acnt_cdC==522 or acnt_cdC==622 or acnt_cdC==672 or acnt_cdC==722 or acnt_cdC==772: cost[11] += thisAmtC
            elif acnt_cdC==530 or acnt_cdC==630 or acnt_cdC==680 or acnt_cdC==730 or acnt_cdC==780: cost[12] += thisAmtC
            elif acnt_cdC==531 or acnt_cdC==631 or acnt_cdC==681 or acnt_cdC==731 or acnt_cdC==781: cost[13] += thisAmtC
            elif acnt_cdC==523 or acnt_cdC==623 or acnt_cdC==673 or acnt_cdC==723 or acnt_cdC==773: cost[14] += thisAmtC
            elif ((acnt_cdC>523 and acnt_cdC<600) or (acnt_cdC>623 and acnt_cdC<650) or (acnt_cdC>673 and acnt_cdC<700) or (acnt_cdC>723 and acnt_cdC<750) or (acnt_cdC>773 and acnt_cdC<800)) and acnt_nmC=="외주비": cost[15] = thisAmtC
            elif (acnt_cdC>523 and acnt_cdC<598) or (acnt_cdC>623 and acnt_cdC<648) or (acnt_cdC>673 and acnt_cdC<698) or (acnt_cdC>723 and acnt_cdC<748) or (acnt_cdC>773 and acnt_cdC<798): cost[16] += thisAmtC     
            # print(str(year) + " : " + acnt_nmC + " : " + str(acnt_cdC) + " : " + str(c[4]))
            # print(str(year) + " : " + acnt_nmC + " : " + str(acnt_cdC) + " : " + str(cost[4]))
      row = {
          "#상품·원재료#":str(cost[0]),
          "#급여·일용·퇴직#":str(cost[1]),
          "#복리후생비#":str(cost[2]),
          "#여비교통비#":str(cost[3]),
          "#접대비#":str(cost[4]),
          "#통신비#":str(cost[5]),
          "#전력·수도광열#":str(cost[6]),
          "#세금과공과#":str(cost[7]),
          "#감가상각비#":str(cost[8]),
          "#임차료#":str(cost[9]),
          "#보험료#":str(cost[10]),
          "#차량유지비#" : str(cost[11]),  
          "#소모품비#" : str(cost[12]),  
          "#지급수수료#" : str(cost[13]),  
          "#연구개발비#" : str(cost[14]),  
          "#외주비#" : str(cost[15]),  
          "#기타#" : str(cost[16])
        }
      cnt = cnt + 1
      costYears["#"+str(year[0])+"#"]=row
    # resultArr[str(now.year-i)]=row
  context["firstYear"] = firstYear
  context["costYears"] = costYears
  # print(rtnJson)  
  return costYears
  # return JsonResponse(rtnJson,safe=False)

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
      'lastEndDate':lastEndDate,
      'fiscalMM':thisEndDate[:2]
    }
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
    context['statementList'] =getStatementList(memuser.user_id,'IS',selectedYear)
  else:
    context['statementList'] =getStatementList(memuser.user_id,'IS',selectedYear)

  return JsonResponse(context,safe=False)


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
  rtnJson["rowDuration"]=getLastFiscalDate(memuser.seq_no,selYear,mem_deal.fiscalmm)
  rtnJson["rows"]=resultArr   
  return JsonResponse(rtnJson,safe=False)