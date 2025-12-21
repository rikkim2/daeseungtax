from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from app.models import userProfile
import os
import time
import datetime
import json
from django.views.decorators.csrf import csrf_exempt
# from pdf2image.exceptions import (
#     PDFInfoNotInstalledError,
#     PDFPageCountError,
#     PDFSyntaxError
# )

selectedYear=''

@login_required(login_url="/login/")
def index_proofSheet(request):
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
  root_dir = request.GET.get('root_dir',False)
  if root_dir==False:
    root_dir = 'static/cert_DS/'+memuser.biz_name
    context['proofYears'] = setProofYears(root_dir)
    totalfolder = path_to_dict(root_dir +'/'+str(selectedYear))
  else:
    context['proofYears'] = setProofYears('static/cert_DS/'+memuser.biz_name)
    totalfolder = path_to_dict(root_dir)
  context['memuser'] = memuser
  context['selectedYear'] =selectedYear
  context['bizSize'] = round( sum(d.stat().st_size for d in os.scandir(root_dir) if d.is_file())/1024000,2)

  #javascript로 보낼때 dumps로 stringfy한다
  context['selectedJson'] = json.dumps(totalfolder)
  
  #django로 바로 출력시 딕셔너리를 보낸다
  #context['selectedJson'] = path_to_dict(root_dir +'/'+str(selectedYear))

  return render(request, "proofSheet.html",context)

def setSelectedProofYear(request):
  global selectedYear
  context = {}
  root_dir = request.GET.get('root_dir',False)
  memuser = MemUser.objects.get(user_id=request.user.username)
  if root_dir==False:
    root_dir = 'static/cert_DS/'+memuser.biz_name
    context['proofYears'] = setProofYears(root_dir)
    totalfolder = path_to_dict(root_dir +'/'+str(selectedYear))
    context['selectedYear'] =selectedYear
  else:
    context['proofYears'] = setProofYears('static/cert_DS/'+memuser.biz_name)
    totalfolder = path_to_dict(root_dir)
    context['selectedYear'] =root_dir[-4:]
  #context['memuser'] = memuser
    
  context['selectedJson'] = json.dumps(totalfolder)
  #context['totalfileArr'] = path_to_file(root_dir +'/'+str(selectedYear))

  return JsonResponse(context,safe=False)

def setProofYears(root_dir):
  global selectedYear
  resultArr = []
  if os.path.isdir(root_dir):
    for path in os.listdir(root_dir):
      if len(path)==4 and path.isnumeric():
        resultArr.append(int(path))
  resultArr.sort(reverse=True)
  selectedYear = resultArr[0]
  return resultArr

#사용안함
def setProofYears2(request):
  global selectedYear
  resultArr = []
  root_dir = request.GET['root_dir']
  if os.path.isdir(root_dir):
    for path in os.listdir(root_dir):
      if len(path)==4 and path.isnumeric():
        resultArr.append(int(path))
        
  resultArr.sort(reverse=True)
  selectedYear = resultArr[0]
  return JsonResponse(resultArr,safe=False)

@csrf_exempt
def setFileGrid(request):
  if request.method == 'POST':
    path = request.POST['path'].replace('\\','/')
    # print(path)
  totfileArr = []
  cnt=1
  if os.path.isdir(path):
    for x in os.listdir(path):
      if os.path.isfile(path+"/"+x) and x!="Thumbs.db":
        file_date = time.ctime(os.path.getctime(path+"/"+x))
        file_date = datetime.datetime.strptime(file_date,"%a %b %d %H:%M:%S %Y")
        fileArr = {'파일명':os.path.splitext(x)[0]}
        fileArr['유형'] = os.path.splitext(x)[1][1:]
        fileArr['크기'] = os.path.getsize(path+"/"+x)
        fileArr['날짜'] = file_date.strftime('%Y-%m-%d')
        fileArr['id'] = cnt
        fileArr['totalPath'] = path+"/"+x
        totfileArr.append(fileArr)
        cnt = cnt + 1
  rtnJson = {"current":1}
  rtnJson["rowCount"]=cnt
  rtnJson["rows"]=totfileArr
  return JsonResponse(rtnJson,safe=False)  


def path_to_dict(path):
  d = {'text': os.path.basename(path)}
  if os.path.isdir(path):
    d['isFolder'] = True
    d['totalPath'] = path
    d['nodes'] = [path_to_dict(os.path.join(path,x)) for x in os.listdir(path) if os.path.isdir(os.path.join(path,x)) and x!="기장보고서" and x!="인건비" and x!="세무조정계산서" and x!="부가세"]
  return d

def path_to_file(path):
  totalfileArr = []
  
  if os.path.isdir(path):
    for x in os.listdir(path):
      if os.path.isfile(path+"/"+x):
        fileArr = {'text':x}
        fileArr['totalPath'] = path+"/"+x
        fileArr['ext'] = os.path.splitext(x)[1][1:]
        fileArr['size'] = os.path.getsize(path+"/"+x)
        totalfileArr.append(fileArr)
  # print(totalfileArr)
  return totalfileArr