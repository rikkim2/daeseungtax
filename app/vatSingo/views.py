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

vatYear=""
@login_required(login_url="/login/")
def index(request):
  global vatYear
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
    context['vatYears'] = setVatYears(root_dir)
    if vatYear:
      context['vatYear'] =vatYear
  else:
    context['vatYears'] = setVatYears('static/cert_DS/'+memuser.biz_name)
  context['root_dir'] = root_dir

  return render(request, "vat/vatSingoseo.html",context)

@login_required(login_url="/login/")
def indexAnaly_view(request):
  context={}
  return render(request, "vat/vatAnaly.html",context)

def originSizeSheet(request):
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
        x_size = page.size[0] #원래 사이즈 1653
        y_size = page.size[1] #원래 사이즈 2339
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

@csrf_exempt
def path_to_dict(request):
  memuser = MemUser.objects.get(user_id=request.user.username) 
  path = request.GET.get('path',False)
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    d['isFolder'] = True
    d['totalPath'] = path
    totfileArr = []
    for x in os.listdir(path):
      if os.path.isdir(os.path.join(path,x)):
        tmpDur="";tmpQuarter="";dueDate=""
        if x=="1기예정":
          tmpDur = "1월 1일 ~ " +  "3월 31일"
          tmpQuarter = "1Q"
          dueDate = "4월25일"
        elif x=="1기확정":
          tmpDur = "1월 1일 ~ " +  "6월 30일"
          if memuser.biz_type<4: tmpDur = "4월 1일 ~ " +  "6월 30일"
          tmpQuarter = "2Q"
          dueDate = "7월25일"
        elif x=="2기예정":
          tmpDur = "7월 1일 ~ " +  "9월 30일"
          tmpQuarter = "3Q"
          dueDate = "10월25일"
        elif x=="2기확정":
          tmpDur = "7월 1일 ~ " +  "12월 31일"
          if memuser.biz_type<4: tmpDur = "10월 1일 ~ " +  "12월 31일"
          tmpQuarter = "4Q"
          dueDate = "1월25일"
        row = {
          'displayName':x,
          'totalPath':path+"/"+x,
          'singoDur':tmpDur,
          'quarter':tmpQuarter,
          'dueDate':dueDate
        }
        if len(os.listdir(path+"/"+x))>0:
          totfileArr.append(row)
    d['nodes'] = totfileArr
  return JsonResponse(d,safe=False)

@csrf_exempt
def path_to_file(request):
  path = request.GET.get('path',False)
  singoPeriod = request.GET.get('singoPeriod',False)
  quarter = request.GET.get('quarter',False)
  totfileArr = []
  cnt=1
  arrFiles = getTblSheet("_vat")
  if os.path.isdir(path):
    for x in natsort.natsorted(os.listdir(path)):
      if os.path.isfile(path+"/"+x) and x!="Thumbs.db":
        tmpFileName=""
        for f in arrFiles:
          if f['fileName']==os.path.splitext(x)[0]:tmpFileName = f['sheetName']
        fileArr = {'파일명':tmpFileName}
        fileArr['fileNum'] = os.path.splitext(x)[0]
        fileArr['id'] = str(quarter)+"@" + os.path.splitext(x)[0]
        fileArr['totalPath'] = path+"/"+x
        totfileArr.append(fileArr)
        cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr
  return JsonResponse(rtnJson,safe=False)

def getTblSheet(flag):
  strsql = "SELECT seq,trim(fileName),trim(sheetName) from Tbl_Sheet"+flag+" order by seq"
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

def setVatYears(root_dir):
  global vatYear
  resultArr = []
  if os.path.isdir(root_dir):
    for path in os.listdir(root_dir):
      if len(path)==4 and path.isnumeric():
        for f in os.listdir(root_dir+"/"+path):
          if f=="부가세":        
            resultArr.append(int(path))
  resultArr.sort(reverse=True)
  if resultArr:
    vatYear = resultArr[0]
  return resultArr


def setVatYear(request):
  global vatYear
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  selectedPeriod = request.GET.get('selectedPeriod',False)
  if selectedPeriod==False:
    context['vatYear'] =vatYear

  return JsonResponse(context,safe=False)