from django.shortcuts import render,redirect
from .forms import FileUploadForm
from django.http import JsonResponse,Http404,HttpResponse
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from app.models import MemDeal
from app.models import MemAdmin
from app.models import userProfile
from django.db import connection
from admins.utils import render_tab_template

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
  mem_admin = MemAdmin.objects.get(admin_id=request.user.username)

  root_dir = 'static/cert_DS/'+mem_admin.admin_name

  context['isRND'] = "운영중"
  context['colorRND'] = "info"
  context['isVENTURE'] = "설치"
  context['colorVENTURE'] = "success"
  context['regDate'] =  str(mem_admin.reg_date.year)+"년 "  + str(mem_admin.reg_date.month)+"월 " + str(mem_admin.reg_date.day)+"일"


  return render(request, "admin/staffInfo.html",context)

@login_required(login_url="/login/")
def staffHoliday(request):
  """직원 휴가 및 일정 관리 페이지"""
  context = {}
  return render_tab_template(request, "admin/staffHoliday.html", context)

@login_required(login_url="/login/")
def fileupload(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # 사용자의 userProfile 인스턴스가 이미 있는지 확인
            if hasattr(request.user, 'profile'):
                user_profile_instance = request.user.profile
                form = FileUploadForm(request.POST, request.FILES, instance=user_profile_instance)
                form.save()
            else:
                user_profile_instance = form.save(commit=False)
                user_profile_instance.user = request.user
                user_profile_instance.save()
            return redirect('staffInfo')
        else:
            print(form.errors)
    return redirect('staffInfo')
    
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
