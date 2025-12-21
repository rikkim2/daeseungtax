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


corpYear=""

@login_required(login_url="/login/")
def index(request):
  
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  memdeal = MemDeal.objects.get(seq_no=memuser.seq_no)
  fiscalMM = memdeal.fiscalmm  
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if memuser.biz_type<4:
    context['isCorp'] = True

  if userprofile:
    userprofile = userprofile.latest('description')
  if userprofile is not None:
    context['userProfile'] = userprofile
  
  context['memuser'] = memuser

  root_dir = request.GET.get('root_dir',False)
  if root_dir==False:
    root_dir = 'static/cert_DS/'+memuser.biz_name
    context['corpYears'] = setCorpYears(root_dir)
    context['corpYear'] =corpYear
  else:
    context['corpYears'] = setCorpYears('static/cert_DS/'+memuser.biz_name)
    context['corpYear'] = corpYear
  context['root_dir'] = root_dir

  return render(request, "corp/corpSingo.html",context)


@csrf_exempt
def path_to_corp(request):
  memuser = MemUser.objects.get(user_id=request.user.username)
  memdeal = MemDeal.objects.get(seq_no=memuser.seq_no)
  path = request.GET.get('path',False)
  fiscalMM = memdeal.fiscalmm
  isCorp = True
  if memuser.biz_type>=4: 
    isCorp = False
  print(isCorp)
  print(memuser.biz_type)
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    totTitleArr = [];totfileArr = [];tmpNow="";tmpAfter=""
    cnt=0;
    for x in natsort.natsorted(os.listdir(path)):
      tmpPureFile  = os.path.splitext(x)[0]
      pureOrder = tmpPureFile.split("-")[0]
      etcFileName = ""
      if "-" in tmpPureFile:
        etcFileName = tmpPureFile.split("-")[1]
      tmpExt = os.path.splitext(x)[1]
      if pureOrder.isnumeric() and os.path.isfile(path+"/"+x) and x!="Thumbs.db" and (tmpExt==".pdf" or tmpExt==".jpg" or tmpExt==".png" or tmpExt==".jpeg" ):
        dueDate=""
        if isCorp:
          if fiscalMM=="12":
            if tmpPureFile=="200":dueDate = " 3월 31일"
            if tmpPureFile=="201":dueDate = " 4월 30일"
            if tmpPureFile=="202":dueDate = " 5월 31일"
            if tmpPureFile=="203":dueDate = " 6월 30일"
            if tmpPureFile=="204":dueDate = " 8월 31일"
            if tmpPureFile=="205":dueDate = " 10월 31일"
          else:
            dueDate = str(int(fiscalMM)+3)+"월 30일"
            if fiscalMM=="3":
              if tmpPureFile=="200":dueDate = " 6월 30일"
              if tmpPureFile=="201":dueDate = " 7월 31일"
              if tmpPureFile=="202":dueDate = " 8월 31일"
              if tmpPureFile=="203":dueDate = " 9월 30일"
              if tmpPureFile=="204":dueDate = " 11월 30일"
              if tmpPureFile=="205":dueDate = " 1월 31일"
            elif fiscalMM=="6":
              if tmpPureFile=="200":dueDate = " 9월 30일"
              if tmpPureFile=="201":dueDate = " 4월 30일"
              if tmpPureFile=="202":dueDate = " 5월 31일"
              if tmpPureFile=="203":dueDate = " 6월 30일"
              if tmpPureFile=="204":dueDate = " 2월 28일"
              if tmpPureFile=="205":dueDate = " 4월 30일"              
        else:
          if tmpPureFile=="200":dueDate = " 5월 31일"
          if tmpPureFile=="201":dueDate = " 5월 31일"
          if tmpPureFile=="202":dueDate = " 7월 31일"
          if tmpPureFile=="204":dueDate = " 11월 30일"

        tmpTitle = ""
        if int(pureOrder)<100:    
          if isCorp:  tmpTitle = "법인세신고서"
          else:       tmpTitle = "종합소득세신고서"
        elif int(pureOrder)<127:  tmpTitle = "결산보고서"
        elif int(pureOrder)<198:  tmpTitle = "기타부속서류"
        elif int(pureOrder)<300:  tmpTitle = "접수증 및 납부서"
        elif int(pureOrder)==300:  tmpTitle = "전체서식"
        elif int(pureOrder)==400:  tmpTitle = "종합소득세 신고안내문"
        elif int(pureOrder)>=400:  tmpTitle = "기타부속서류"
        tmpNow = tmpTitle
        if tmpAfter!=tmpNow:
          titles = {
            'displayName':tmpTitle,
          }
          totTitleArr.append(titles)
        tmpAfter = tmpNow

        tmpSheet = ""
        if isCorp:  tmpSheet = "_corp"
        else:       tmpSheet = "_income"
        arrFiles = getTblSheet(tmpSheet)
        tmpFileName=""
        for f in arrFiles:
          if  f['fileName']==tmpPureFile:
            tmpFileName = f['sheetName']
          else:
            if etcFileName and (int(pureOrder)>=127 and int(pureOrder)<198 or int(pureOrder)>400):   tmpFileName=etcFileName
        files = {
          'group':tmpTitle,
          '파일명':tmpFileName,
          'id':str(cnt),
          'totalPath':path+"/"+x,
          'dueDate':dueDate
        }
        if len(os.listdir(path))>0:
          totfileArr.append(files)
        cnt = cnt+1
    d['titles'] = totTitleArr    
    d['nodes'] = totfileArr
  return JsonResponse(d,safe=False)

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

def setCorpYears(root_dir):
  global corpYear
  resultArr = []
  if os.path.isdir(root_dir):
    for path in os.listdir(root_dir):
      if len(path)==4 and path.isnumeric():
        for f in os.listdir(root_dir+"/"+path):
          if f=="세무조정계산서":
            resultArr.append(int(path))
  resultArr.sort(reverse=True)
  if resultArr:
    corpYear = resultArr[0]
  return resultArr


def setCorpYear(request):
  global corpYear
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  selectedPeriod = request.GET.get('selectedPeriod',False)
  if selectedPeriod==False:
    context['corpYear'] =corpYear

  return JsonResponse(context,safe=False)