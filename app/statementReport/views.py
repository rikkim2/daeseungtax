from __future__ import print_function 
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import os
import natsort
import time
import datetime
from app.models import MemUser
from app.models import MemAdmin
from app.models import MemDeal
from app.models import userProfile
from pdf2image import convert_from_path

import glob
from PIL import Image
import tifffile
import numpy

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

reportYears = []
seq_no=""

@login_required(login_url="/login/")
def index(request):
  global seq_no
  context = {}
  memuser = MemUser.objects.get(user_id=request.user.username)
  userprofile = userProfile.objects.filter(title=memuser.seq_no)
  if memuser.biz_type<4:
    context['isCorp'] = True
  if userprofile:
    userprofile = userprofile.latest('description')
  if userprofile is not None:
    context['userProfile'] = userprofile
    context['dateNow'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  seq_no = memuser.seq_no
  context['memuser'] = memuser
  root_dir = 'static/cert_DS/'+memuser.biz_name

  context['reportAll'] = path_to_file(root_dir)
  context['reportYears'] = reportYears
  return render(request, "statementReport.html",context)

def path_to_file(path):
  global reportYears
  reportAll   = []
  reportYears2  =[]
  mem_deal = MemDeal.objects.get(seq_no=seq_no)
  mem_admin = MemAdmin.objects.get(admin_id=mem_deal.biz_manager)
  if os.path.isdir(path):
    for (root, dirs, files) in os.walk(path):
      if len(files)>0:
        for file_name in files:
          
          if file_name=="300.pdf" and root.find('기장보고서')!=-1:
            fileArr = {'file_name':file_name}
            tmpRoot = root.replace('\\','/')
           
            fileArr['file_path'] = tmpRoot+'/'+file_name
            file_date = time.ctime(os.path.getctime(tmpRoot+'/'+file_name))
            file_date = datetime.datetime.strptime(file_date,"%a %b %d %H:%M:%S %Y")
            fileArr['file_date'] = file_date.strftime('%Y-%m-%d')
            fileArr['admin_name'] = mem_admin.admin_name
            tmpYear = tmpRoot.replace(path+"/","")[:4]
            if tmpYear.isnumeric():
              fileArr['work_year'] = tmpYear
              a,b = divmod(int(tmpYear),4)
              if b==0:
                fileArr['file_color'] = "orange"
              elif b==1:
                fileArr['file_color'] = "info"
              elif b==2:
                fileArr['file_color'] = "success"
              elif b==3:
                fileArr['file_color'] = "warning"
              if tmpYear not in reportYears2:
                reportYears2.append(tmpYear)
            else:
              fileArr['work_year'] = ""
            if root.find('분기')!=-1:
              fileArr['work_qt'] = tmpRoot[-3:]
              if tmpRoot[-3:]=="1분기":
                fileArr['during'] = tmpYear + "년 1월 1일 ~ " + tmpYear + "년 3월 31일"
              elif tmpRoot[-3:]=="2분기":
                fileArr['during'] = tmpYear + "년 1월 1일 ~ " + tmpYear + "년 6월 30일"
              elif tmpRoot[-3:]=="3분기":
                fileArr['during'] = tmpYear + "년 1월 1일 ~ " + tmpYear + "년 9월 30일"
              elif tmpRoot[-3:]=="4분기":
                fileArr['during'] = tmpYear + "년 1월 1일 ~ " + tmpYear + "년 12월 31일"
            else:
              fileArr['work_qt'] = "4분기"
              fileArr['during'] = tmpYear + "년 1월 1일 ~ " + tmpYear + "년 12월 31일"
            if os.path.isdir(tmpRoot):
              cnt=1
              for x in os.listdir(tmpRoot):
                cnt = cnt + 1
              fileArr['file_size'] = cnt-4
            reportAll.append(fileArr)
  reportYears = sorted(reportYears2)
  # print(reportAll)
  return reportAll

def changePdf(request):
  context = {}
  FRAMES = []
  FIRST_SIZE = None
  
  totalFileName = request.GET.get('url',False)
  pureFilewithext = list(reversed(totalFileName.split('/')))[0]
  fileNameWithoutExt = pureFilewithext.split('.')[0]
  pathName = totalFileName.replace(pureFilewithext,"")
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
    # tiff이미지로 만드는 경우
    # for fn in natsort.natsorted(filelist):
    #     img = Image.open(fn)
    #     if FIRST_SIZE is None:
    #         FIRST_SIZE = img.size
    #     if img.size == FIRST_SIZE:
    #         print ("Adding:", fn)
    #         FRAMES.append(img)
    #     else:
    #         print ("Discard:", fn, img.size, "<>", FIRST_SIZE)

    # print("Writing", len(FRAMES), "frames to", OUT_NAME)
    # with tifffile.TiffWriter(OUT_NAME) as tiff:
    #   for img in FRAMES:
    #     tiff.save(PIL2array(img))


    [os.remove(f) for f in glob.glob("static/pdf2Image/*.jpg")]
  # print("성공")
  return JsonResponse(context,safe=False)

def PIL2array(img):
    return numpy.array(img.getdata(), numpy.uint8).reshape(img.size[1], img.size[0], 3)


def sendMail(request):
  context = {}
  # 세션생성, 로그인
  s = smtplib.SMTP('smtp.gmail.com', 587)
  s.starttls()
  s.login('daeseung23@gmail.com', 'zrncmbdvtrphknoa')

  # 제목, 본문 작성
  memuser = MemUser.objects.get(user_id=request.user.username)
  biz_name = memuser.biz_name
  msg = MIMEMultipart()
  msg['Subject'] = '[세무법인대승] '+biz_name+" " + request.GET.get('selectedPeriod',False) + ' 기장보고서 전달'
  tmpContent = "안녕하세요 세무법인대승입니다.  \n\r"
  tmpContent += "요청하신 "+ biz_name +"의 "+ request.GET.get('selectedPeriod',False) + ' 기장보고서를 전달드립니다.'  + " \n\r"
  tmpContent += "감사합니다. "
  msg.attach(MIMEText(tmpContent, 'plain'))

  emailAddr = request.GET.get('emailAddr',False)
  fileName = request.GET.get('fileName',False)
  totalFile = request.GET.get('totalFile',False)
  # 파일첨부 (파일 미첨부시 생략가능)
  attachment = open(totalFile, 'rb')
  part = MIMEBase('application', 'octet-stream')
  part.set_payload((attachment).read())
  encoders.encode_base64(part)
  part.add_header('Content-Disposition', "attachment; filename="+fileName )
  msg.attach(part)

  # 메일 전송

  senderAddr  = memuser.email
  receiveAddr = emailAddr
  s.sendmail(senderAddr, receiveAddr, msg.as_string())
  s.quit()
  return JsonResponse(context,safe=False)