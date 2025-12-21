from django.shortcuts import render,redirect
from .forms import FileUploadForm
from django.http import JsonResponse,Http404,HttpResponse
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from app.models import MemDeal
from app.models import MemAdmin
from app.models import userProfile
from django.db import connection

import os
import natsort
import datetime
from pdf2image import convert_from_path
import glob
from PIL import Image

from django.core.mail import send_mail, EmailMessage

import smtplib
from django.conf import settings
from django.core.mail import send_mail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


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
    context['dateNow'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  if memuser.biz_type<4:
    context['isCorp'] = True
  seq_no = memuser.seq_no
  mem_deal = MemDeal.objects.get(seq_no=seq_no)
  mem_admin = MemAdmin.objects.get(admin_id=mem_deal.biz_manager)  
  root_dir = 'static/cert_DS/'+memuser.biz_name

  context['memuser'] = memuser
  
  context['isRND'] = "운영중" if memuser.isrnd=="Y" else "없음"
  context['colorRND'] = "info" if memuser.isrnd=="Y" else "danger"
  context['isVENTURE'] = "설치" if memuser.isventure=="Y" else "없음"  
  context['colorVENTURE'] = "success" if memuser.isventure=="Y" else "danger"
  context['regDate'] =  str(memuser.reg_date.year)+"년 "  + str(memuser.reg_date.month)+"월 " + str(memuser.reg_date.day)+"일"
  context['createdDate'] =  str(mem_deal.createddate.year)+"년 "  + str(mem_deal.createddate.month)+"월 " + str(mem_deal.createddate.day)+"일"
  context['memadmin'] = mem_admin
  now = datetime.datetime.now()
  if int(memuser.biz_type)<4:
    root_dir = 'static/cert_DS/'+memuser.biz_name+'/'+'등기서류'
    context['isCORP'] = True
    strsql =  " SELECT B.StckH_Num       sthNum "
    strsql += "      , MAX(B.StckH_Nm)    sthName	"
    strsql += "      , CASE WHEN B.StckH_RS = 0 THEN '지배주주'	"
    strsql += "             WHEN B.StckH_RS = 1 THEN '배우자'	"
    strsql += "             WHEN B.StckH_RS = 2 THEN '자녀'	"
    strsql += "             WHEN B.StckH_RS = 3 THEN '부모'	"
    strsql += "             WHEN B.StckH_RS = 4 THEN '형제자매'	"
    strsql += "             WHEN B.StckH_RS = 5 THEN '손자'	"
    strsql += "             WHEN B.StckH_RS = 6 THEN '조부모'	"
    strsql += "             WHEN B.StckH_RS = 7 THEN '친족의 배우자'	"
    strsql += "             WHEN B.StckH_RS = 8 THEN '기타 친족'	"
    strsql += "             WHEN B.StckH_RS = 9 THEN '기타'	"
    strsql += "             WHEN B.StckH_RS = 10 THEN '특수관계법인'	"
    strsql += "             ELSE '' END sthRelation	"
    strsql += "      , MIN(a.tran_Dt) sthGetDate 	"
    strsql += "      , SUM(Case When A.StckH_TranGB = 'B' Then A.StckH_FEquityNum * -1 Else A.StckH_FEquityNum End)		sthCnt	"
    strsql += "      , MAX(A.StckH_FEquityFP)																		sthFaceValue	"
    strsql += "      , SUM(Case When A.StckH_TranGB = 'B' Then A.StckH_FEquityGP * -1 Else A.StckH_FEquityGP End)       sthTotalValue	"
    strsql += "      , SUM(Case When A.StckH_TranGB = 'B' Then A.StckH_FEquityNum * -1 Else A.StckH_FEquityNum End) / 	"
    strsql += "        (SELECT SUM(Case When D.StckH_TranGB = 'B' Then D.StckH_FEquityNum * -1 Else D.StckH_FEquityNum End)	"
    strsql += "           FROM 	Tbl_StckHolderList C With (Nolock)	"
    strsql += "              , Tbl_StckHListTrn    D With (Nolock)	"
    strsql += " 		 WHERE C.Seq_No    = (select seq_no from mem_user where user_id='"+memuser.user_id+"')"
    strsql += " 		   AND C.Seq_No    = D.Seq_No	"
    strsql += " 		   AND C.StckH_Num = D.StckH_Num	"
    strsql += " 		   AND D.TRAN_DT   <= '" + now.strftime('%Y-%m-%d') + "' ) * 100       sthRate	"
    strsql += "       FROM Tbl_StckHolderList  B With (Nolock)	"
    strsql += "      , Tbl_StckHListTrn    A With (Nolock)	"
    strsql += "  WHERE B.Seq_No    = (select seq_no from mem_user where user_id='"+memuser.user_id+"')"
    strsql += "    AND B.Seq_No    = A.Seq_No	"
    strsql += "    AND B.StckH_Num = A.StckH_Num	"
    strsql += "    AND A.TRAN_DT   <= '" + now.strftime('%Y-%m-%d') + "' 	"
    strsql += "  Group By B.StckH_Num, B.StckH_RS	"
    strsql += "  Having SUM(Case When A.StckH_TranGB = 'B' Then A.StckH_FEquityNum * -1 Else A.StckH_FEquityNum End)  > 0 "
    strsql += "  Order by 5 desc"

    cursor = connection.cursor()
    result = cursor.execute(strsql)
    datas = cursor.fetchall()
    connection.commit()
    connection.close()
    # print(context['stockholders'])
    stockholders = []
    totalCap = 0
    for data in datas:
      colorSpec = "info"
      if data[2]=="기타":
        colorSpec = "warning"
      row = {'sthName': data[1]
            ,'sthRelation': data[2]
            ,'sthGetDate': data[3]
            ,'sthCnt': int(data[4])
            ,'sthFaceValue': data[5]
            ,'sthTotalValue': int(data[6])
            ,'sthRate': round(data[7],2)
            ,'colorSpec':colorSpec}
      stockholders.append(row)
      totalCap += int(data[6])
    context['stockHolders'] = stockholders
    context['stockTotal'] = totalCap

    strsql =  " select execflag, execNum, execName, execJumin, d.regDate as exec_regDate, extentDate, 	"
    strsql +=" case when execflag='감사' then	"
    strsql +=" 	case when extentDate<>'' 	"
    strsql +=" 		then  CONVERT(CHAR(4),left(extentDate,4)/1+3) + '-03-31'	"
    strsql +=" 		else CONVERT(CHAR(4),left(d.regDate,4)/1+3) + '-03-31'	"
    strsql +=" 	end 	"
    strsql +=" else	"
    strsql +=" 	case when extentDate<>'' 	"
    strsql +=" 		then  CONVERT(CHAR(4),left(extentDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(extentDate,5)) 	"
    strsql +=" 		else CONVERT(CHAR(4),left(d.regDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(d.regDate,5)) 	"
    strsql +=" 	end 	"
    strsql +=" end as duedate,	"
    strsql +=" case when execflag='감사' then	'warning'"
    strsql +="      when execflag='대표이사' then 'primary'   "
    strsql +="      else 'success' end as colorExec,"
    strsql +=" case when execflag='감사' then	"
    strsql +="     case when extentDate<>'' 	"
    strsql +="         then  datediff(dd,left(extentDate,10),CONVERT(CHAR(4),left(extentDate,4)/1+3) + '-03-31')"
    strsql +="         else datediff(dd,left(d.regDate,10),CONVERT(CHAR(4),left(d.regDate,4)/1+3) + '-03-31')"
    strsql +="     end 	"
    strsql +=" else	"
    strsql +="     case when extentDate<>'' 	"
    strsql +="         then  datediff(dd,left(extentDate,10),CONVERT(CHAR(4),left(extentDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(extentDate,5)) )"
    strsql +="         else datediff(dd,left(d.regDate,10),CONVERT(CHAR(4),left(d.regDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(d.regDate,5)) )"
    strsql +="     end 	"
    strsql +=" end as totalDD,"
    strsql +=" case when extentDate<>'' 	"
    strsql +="     then  datediff(dd,extentDate,getDate())"
    strsql +="     else datediff(dd,d.regDate,getDate())"
    strsql +=" end as passDD, "            
    strsql +=" case when extentDate<>'' "
    strsql +="     then  "
    strsql +="         case when datediff(dd,CONVERT(CHAR(4),left(extentDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(extentDate,5)) ,getdate())<30"
    strsql +="             then 'danger' else 'info' end"
    strsql +="     else "
    strsql +="         case when datediff(dd,CONVERT(CHAR(4),left(d.regDate,4)/1+3) + '-' + CONVERT(CHAR(5), right(d.regDate,5)) 	,getdate())<30"
    strsql +="             then 'danger' else 'info' end"
    strsql +=" end as colorProgress"
    strsql +=" from Mem_User a, mem_deal b ,mem_admin c, lawregistration d 	"
    strsql +=" where a.seq_no=b.seq_no and A.seq_no = d.seq_no and c.del_yn <>'Y' and duzon_ID <> '' and b.keeping_YN='Y' AND a.Del_YN<>'Y' and b.biz_manager=c.admin_id and biz_type in ('1','2','3') 	"
    strsql +=" and d.execflag in ('대표이사','사내이사','감사') 	"
    strsql +=" and d.fireDate='' 	"
    strsql +=" and a.seq_no=(select seq_no from mem_user where user_id='"+memuser.user_id+"')"
    strsql +=" order by d.regDate 	"
    # print(strsql)
    cursor = connection.cursor()
    result = cursor.execute(strsql)
    datas = cursor.fetchall()
    connection.commit()
    connection.close()
    exec = []
    for data in datas:
      txtPass = "미경과"
      badgeColorPass = "light"
      if int(data[9])>int(data[8]):
        txtPass = "경과"
        badgeColorPass = "danger"
      passedRate = int(data[9]/data[8]*100)
      remainDD = data[8]-data[9]
      row = {'execflag': data[0]
            ,'execName': data[2]
            ,'exec_regDate': data[4]
            ,'extentDate': data[5]
            ,'duedate': data[6]
            ,'colorProgress': data[7]
            ,'txtPass': txtPass
            ,'passedRate':passedRate
            ,'remainDD':remainDD
            ,'badgeColorPass': badgeColorPass}
      exec.append(row)
    context['execs'] = exec

# 인건비
  strsql =  " select	'정규직'  AS TITLE,	 "
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then a01m end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then a01m end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then a01m end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then a01m end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then a01m end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then a01m end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then a01m end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then a01m end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then a01m end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then a01m end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then a01m end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then a01m end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(a01m)/"
  strsql  += "(select convert(int,right(max(과세연월),2)) from 원천세전자신고 where left(과세연월,4)='"+str(now.year)+"' and 사업자등록번호=(select Biz_No from mem_user where User_ID='"+memuser.user_id+"')) "
  strsql  += ",0) 'TOT'	"
  strsql  += ",'blue' as COLOR	"
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'사업소득'  AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then a30m end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then a30m end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then a30m end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then a30m end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then a30m end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then a30m end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then a30m end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then a30m end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then a30m end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then a30m end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then a30m end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then a30m end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(a30m)/"
  strsql  += "(select convert(int,right(max(과세연월),2)) from 원천세전자신고 where left(과세연월,4)='"+str(now.year)+"' and 사업자등록번호=(select Biz_No from mem_user where User_ID='"+memuser.user_id+"')) "
  strsql  += ",0) 'TOT'	"
  strsql  += ",'primary' as COLOR	"
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'기타소득' AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then a40m end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then a40m end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then a40m end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then a40m end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then a40m end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then a40m end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then a40m end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then a40m end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then a40m end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then a40m end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then a40m end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then a40m end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(a40m)/"
  strsql  += "(select convert(int,right(max(과세연월),2)) from 원천세전자신고 where left(과세연월,4)='"+str(now.year)+"' and 사업자등록번호=(select Biz_No from mem_user where User_ID='"+memuser.user_id+"')) "
  strsql  += ",0) 'TOT'	"
  strsql  += ",'danger' as COLOR	"
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'일용직' AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then a03m end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then a03m end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then a03m end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then a03m end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then a03m end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then a03m end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then a03m end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then a03m end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then a03m end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then a03m end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then a03m end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then a03m end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(a03m)/"
  strsql  += "(select convert(int,right(max(과세연월),2)) from 원천세전자신고 where left(과세연월,4)='"+str(now.year)+"' and 사업자등록번호=(select Biz_No from mem_user where User_ID='"+memuser.user_id+"')) "
  strsql  += ",0) 'TOT'	" 
  strsql  += ",'warning' as COLOR	"                               
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  # print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  datas = cursor.fetchall()
  connection.commit()
  connection.close()
  workers = []
  for data in datas:
    row = {'TITLE': data[0]
          ,'JAN': data[1]
          ,'FEB': data[2]
          ,'MAR': data[3]
          ,'APR': data[4]
          ,'MAY': data[5]
          ,'JUN': data[6]
          ,'JUL':data[7]
          ,'AUG':data[8]
          ,'SET':data[9]
          ,'OCT':data[10]
          ,'NOV':data[11]
          ,'DEC':data[12]
          ,'TOT':round(data[13],2)
          ,'COLOR':data[14]}
    workers.append(row)
  context['workers'] = workers
  print(workers)
  strsql  = " select	'정규직급여'  AS TITLE,	 "
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then round(a01/10000,0) end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then round(a01/10000,0) end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then round(a01/10000,0) end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then round(a01/10000,0) end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then round(a01/10000,0) end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then round(a01/10000,0) end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then round(a01/10000,0) end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then round(a01/10000,0) end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then round(a01/10000,0) end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then round(a01/10000,0) end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then round(a01/10000,0) end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then round(a01/10000,0) end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(round(a01/10000,0)),0) 'TOT'"
  strsql  += ",'blue' as COLOR	"    
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'사업소득급여'  AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then round(a30/10000,0) end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then round(a30/10000,0) end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then round(a30/10000,0) end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then round(a30/10000,0) end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then round(a30/10000,0) end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then round(a30/10000,0) end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then round(a30/10000,0) end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then round(a30/10000,0) end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then round(a30/10000,0) end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then round(a30/10000,0) end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then round(a30/10000,0) end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then round(a30/10000,0) end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(round(a30/10000,0)),0) 'TOT'	"
  strsql  += ",'primary' as COLOR	"    
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'기타소득급여' AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then round(a40/10000,0) end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then round(a40/10000,0) end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then round(a40/10000,0) end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then round(a40/10000,0) end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then round(a40/10000,0) end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then round(a40/10000,0) end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then round(a40/10000,0) end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then round(a40/10000,0) end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then round(a40/10000,0) end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then round(a40/10000,0) end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then round(a40/10000,0) end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then round(a40/10000,0) end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(round(a40/10000,0)),0) 'TOT'	"
  strsql  += ",'danger' as COLOR	"    
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  strsql  += " UNION ALL	"
  strsql  += " select	'일용직급여' AS TITLE,	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='01' then round(a03/10000,0) end),0) as 'JAN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='02' then round(a03/10000,0) end),0) as 'FEB',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='03' then round(a03/10000,0) end),0) as 'MAR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='04' then round(a03/10000,0) end),0) as 'APR',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='05' then round(a03/10000,0) end),0) as 'MAY',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='06' then round(a03/10000,0) end),0) as 'JUN',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='07' then round(a03/10000,0) end),0) as 'JUL',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='08' then round(a03/10000,0) end),0) as 'AUG',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='09' then round(a03/10000,0) end),0) as 'SET',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='10' then round(a03/10000,0) end),0) as 'OCT',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='11' then round(a03/10000,0) end),0) as 'NOV',	"
  strsql  += " ISNULL(max(case when right(과세연월,2)='12' then round(a03/10000,0) end),0) as 'DEC',	"
  strsql  += " ISNULL(SUM(convert(numeric(13,0),round(a03/10000,0))),0) 'TOT'	"      
  strsql  += ",'warning' as COLOR	"                             
  strsql  += " from 원천세전자신고	"
  strsql  += " where 사업자등록번호=(select Biz_No from mem_user where user_id='"+memuser.user_id+"') and left(과세연월,4)='"+str(now.year)+"'"
  strsql  += " group by   left(과세연월,4)	"
  # print(strsql)
  cursor = connection.cursor()
  result = cursor.execute(strsql)
  datas = cursor.fetchall()
  connection.commit()
  connection.close()
  salarys = []
  for data in datas:
    row = {'TITLE': data[0]
          ,'JAN': data[1]
          ,'FEB': data[2]
          ,'MAR': data[3]
          ,'APR': data[4]
          ,'MAY': data[5]
          ,'JUN': data[6]
          ,'JUL':data[7]
          ,'AUG':data[8]
          ,'SET':data[9]
          ,'OCT':data[10]
          ,'NOV':data[11]
          ,'DEC':data[12]
          ,'TOT':data[13]
          ,'COLOR':data[14]}
    salarys.append(row)
  context['salarys'] = salarys
  context['fileArr'] = getFileArr(root_dir+'/')

  return render(request, "companyInfo/companyInfo.html",context)

def fileuploadCompanyInfo(request):
  if request.method == 'POST':
    form = FileUploadForm(request.POST, request.FILES)
    if form.is_valid():
      form.save()
    else:
      print(form)
    return redirect('companyInfo')
  return redirect('companyInfo')
    
def getFileArr(path):
  reportAll = []
  tmpList1 = []    #사업자등록증
  tmpList2 = []    #등기부등본
  tmpList3 = []    #주주명부
  tmpList4 = []    #임대차계약서
  tmpList5 = []    #정관
  if os.path.isdir(path):
    for f_name in os.listdir(f"{path}"):
      written_time = os.path.getctime(f"{path}{f_name}")
      if "사업자등록" in f_name and ("pdf" in f_name or "jpg" in f_name or "png" in f_name):
        tmpList1.append((f_name, written_time))
      if "등기부" in f_name and ("pdf" in f_name or "jpg" in f_name or "png" in f_name):
        tmpList2.append((f_name, written_time))
      if "주주" in f_name and ("pdf" in f_name or "jpg" in f_name or "png" in f_name):
        tmpList3.append((f_name, written_time))
      if "임대" in f_name and ("pdf" in f_name or "jpg" in f_name or "png" in f_name):
        tmpList4.append((f_name, written_time))
      if "정관" in f_name and ("pdf" in f_name or "jpg" in f_name or "png" in f_name):
        tmpList5.append((f_name, written_time))
    if len(tmpList1)>0:
      sorted_file_lst = sorted(tmpList1, key=lambda x: x[1], reverse=True)
      recent_file = sorted_file_lst[0]
      recent_file_name = recent_file[0]
      fileArr = {'file_path':path}
      fileArr['disp_name'] = "사업자등록증"
      fileArr['file_path'] = path+recent_file_name
      reportAll.append(fileArr)
    if len(tmpList2)>0:
      sorted_file_lst = sorted(tmpList2, key=lambda x: x[1], reverse=True)
      recent_file = sorted_file_lst[0]
      recent_file_name = recent_file[0]
      fileArr = {'file_path':path}
      fileArr['disp_name'] = "등기부등본"
      fileArr['file_path'] = path+recent_file_name
      reportAll.append(fileArr)
    if len(tmpList3)>0:
      sorted_file_lst = sorted(tmpList3, key=lambda x: x[1], reverse=True)
      recent_file = sorted_file_lst[0]
      recent_file_name = recent_file[0]
      fileArr = {'file_path':path}
      fileArr['disp_name'] = "주주명부"
      fileArr['file_path'] = path+recent_file_name
      reportAll.append(fileArr)
    if len(tmpList4)>0:
      sorted_file_lst = sorted(tmpList4, key=lambda x: x[1], reverse=True)
      recent_file = sorted_file_lst[0]
      recent_file_name = recent_file[0]
      fileArr = {'file_path':path}
      fileArr['disp_name'] = "임대차계약서"
      fileArr['file_path'] = path+recent_file_name 
      reportAll.append(fileArr)   
    if len(tmpList5)>0:
      sorted_file_lst = sorted(tmpList5, key=lambda x: x[1], reverse=True)
      recent_file = sorted_file_lst[0]
      recent_file_name = recent_file[0]
      fileArr = {'file_path':path}
      fileArr['disp_name'] = "정관"
      fileArr['file_path'] = path+recent_file_name 
      reportAll.append(fileArr) 
  return reportAll

def changeSheet(request):
  context = {}
  FRAMES = []
  FIRST_SIZE = None
  
  totalFileName = request.GET.get('url',False)
  pureFilewithext = list(reversed(totalFileName.split('/')))[0]
  fileNameWithoutExt = pureFilewithext.split('.')[0]
  pathName = totalFileName.replace(pureFilewithext,"")
  if "jpg" in totalFileName or "png" in totalFileName:
    context['fileName'] = totalFileName
    context['onlyFileName'] = pureFilewithext
    context['onlyFileExt'] = pureFilewithext.split('.')[1]
    context['onlyFilePath'] = pathName
  elif "pdf" in totalFileName:

    imgfilenameToSearch = pathName.replace("/","##")+fileNameWithoutExt+"(1).jpg"
    OUT_NAME = "static/pdfImage/"+pathName.replace("/","@")+fileNameWithoutExt+".jpg"
    context['fileName'] = OUT_NAME
    context['onlyFileName'] = pureFilewithext
    context['onlyFileExt'] = pureFilewithext.split('.')[1]
    context['onlyFilePath'] = pathName

    if not os.path.exists(OUT_NAME):
      images = convert_from_path(totalFileName,poppler_path='C:\\poppler-22.04.0\\Library\\bin')
      y_sum=0
      x_size=0
      y_size=0
      for i,page in enumerate(images):
        page.save("static/pdf2Image/"+pathName.replace("/","##")+fileNameWithoutExt+"@"+str(i)+".jpg","JPEG")
        x_size = 759 #page.size[0] 원래 사이즈 1653
        y_size = 1074 #page.size[1] 원래 사이즈 2339
        y_sum = y_sum + y_size
        # page.save("static/pdf2Image/"+str(i)+".jpg","JPEG")

      filelist = glob.glob("static/pdf2Image/*.jpg")
      new_Image = Image.new("RGB",(x_size,y_sum),(256,256,256))
      for fn in natsort.natsorted(filelist):
        img = Image.open(fn)
        resized_file = img.resize((x_size,y_size))
        FRAMES.append(resized_file)

          # if FIRST_SIZE is None:
          #   FIRST_SIZE = img.size
          # if img.size == FIRST_SIZE:
          #   resized_file = img.resize((x_size,y_size))
          #   FRAMES.append(resized_file)
          # else:
          #     print ("Discard:", fn, img.size, "<>", FIRST_SIZE)

      for index in range(len(FRAMES)):
        area = (0,(index*y_size),x_size,y_size*(index+1))
        print ("Adding:", area)
        new_Image.paste(FRAMES[index],area)
      new_Image.save(OUT_NAME)

      [os.remove(f) for f in glob.glob("static/pdf2Image/*.jpg")]
  # print("성공")
  return JsonResponse(context,safe=False)


def sendMailCompInfo(request):
  context = {}
  # 세션생성, 로그인
  s = smtplib.SMTP('smtp.gmail.com', 587)
  s.starttls()
  s.login('daeseung23@gmail.com', 'zrncmbdvtrphknoa')
 
  # 제목, 본문 작성
  memuser = MemUser.objects.get(user_id=request.user.username)
  biz_name = memuser.biz_name
  msg = MIMEMultipart()
  msg['Subject'] = '[세무법인대승] '+biz_name+" " + request.GET.get('selectedPeriod',False) + ' 전달의 건2'
  Subject = '[세무법인대승] '+biz_name+" " + request.GET.get('selectedPeriod',False) + ' 전달의 건2'
  tmpContent = "안녕하세요 세무법인대승입니다. \n\r"
  tmpContent += "요청하신 "+ biz_name +"의 "+ request.GET.get('selectedPeriod',False) + '  전달드립니다.'  + "\n\r"
  tmpContent += "감사합니다. "
  msg.attach(MIMEText(tmpContent, 'plain'))

  emailAddr = request.GET.get('emailAddr',False)
  fileName = request.GET.get('fileName',False)
  totalFile = request.GET.get('totalFile',False)
  
  # print("fileName:"+fileName)
  # 파일첨부 (파일 미첨부시 생략가능)
  attachment = open(totalFile, 'rb')
  part = MIMEBase('application', 'octet-stream')
  part.set_payload((attachment).read())
  encoders.encode_base64(part)
  ## part.add_header('Content-Disposition', "attachment; filename="+fileName ) # 한글첨부파일 안됨  <========================  중요
  part.add_header('Content-Disposition', "attachment",filename=fileName )
  msg.attach(part)

  # 메일 전송

  senderAddr  = memuser.email
  receiveAddr = emailAddr

  s.sendmail(senderAddr, receiveAddr, msg.as_string())
  s.quit()


  return JsonResponse(context,safe=False)