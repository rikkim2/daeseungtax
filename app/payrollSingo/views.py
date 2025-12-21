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

payrollYear=""
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

  root_dir = request.GET.get('root_dir',False)
  if root_dir==False:
    root_dir = 'static/cert_DS/'+memuser.biz_name
    context['payrollYears'] = setPayrollYears(root_dir)

    context['payrollYear'] =payrollYear
  else:
    context['payrollYears'] = setPayrollYears('static/cert_DS/'+memuser.biz_name)
    context['selectedYear'] =root_dir[-4:]
  context['root_dir'] = root_dir

  return render(request, "payroll/payrollSingo.html",context)


@csrf_exempt
def path_to_wonchun(request):
  path = request.GET.get('path',False)
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    totTitleArr = [];totfileArr = [];tmpNow="";tmpAfter=""
    cnt=0;
    for x in natsort.natsorted(os.listdir(path)):
      tmpExt = os.path.splitext(x)[1]
      if ("월" in x[:3]) and os.path.isfile(path+"/"+x) and x!="Thumbs.db" and (tmpExt==".pdf" or tmpExt==".jpg" or tmpExt==".png" or tmpExt==".jpeg" ):
        dueDate=""
        fileMM = int(os.path.splitext(x)[0].split(" ")[0].replace("월",""))
        if fileMM==12:
          dueDate = "1월 10일"
        else:
          dueDate = str(fileMM+1)+"월 10일"

        files = {
          'group':x.split(" ")[0]+" 원천징수",
          '파일명':os.path.splitext(x)[0].split(" ")[1],
          'id':str(cnt),
          'totalPath':path+"/"+x,
          'dueDate':dueDate
        }
        tmpNow = x.split(" ")[0]
        if tmpAfter!=tmpNow:
          titles = {
            'displayName':x.split(" ")[0]+" 원천징수",
          }
          totTitleArr.append(titles)
        tmpAfter = tmpNow

        if len(os.listdir(path))>0:
          totfileArr.append(files)
        cnt = cnt+1
    d['titles'] = totTitleArr    
    d['nodes'] = totfileArr
  return JsonResponse(d,safe=False)


def setPayrollYears(root_dir):
  global payrollYear
  resultArr = []
  if os.path.isdir(root_dir):
    for path in os.listdir(root_dir):
      if len(path)==4 and path.isnumeric():
        for f in os.listdir(root_dir+"/"+path):
          if f=="인건비":        
            resultArr.append(int(path))
  resultArr.sort(reverse=True)
  if resultArr:
    payrollYear = resultArr[0]
  return resultArr


def setPayrollYear(request):
  global payrollYear
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  selectedPeriod = request.GET.get('selectedPeriod',False)
  if selectedPeriod==False:
    context['payrollYear'] =payrollYear

  return JsonResponse(context,safe=False)