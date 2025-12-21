from django.shortcuts import render,redirect
from django.http import JsonResponse,Http404,HttpResponse
from django.contrib.auth.decorators import login_required
from app.models import MemUser
from app.models import MemDeal
from app.models import MemAdmin
from app.models import userProfile
from django.db import connection
from pathlib import Path
import os
import os.path
import natsort
import datetime
from pdf2image import convert_from_path
import glob
from PIL import Image

import oauth2client
from oauth2client import client, tools, file

import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from apiclient import errors, discovery
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pickle

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request 

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
  
  # print(get_service())
  return render(request, "bizMail/mail-inbox.html",context)


  # credential_path = os.path.join(credential_dir, 'credentials.json')
  # store = oauth2client.file.Storage(credential_path)
  # credentials = store.get()
    
  
  # if not credentials or credentials.invalid:
  #   print('here')
  #   CLIENT_SECRET_FILE = 'credentials.json'
  #   APPLICATION_NAME = 'Gmail API Python Send Email'
  #   SCOPES = 'https://www.googleapis.com/auth/gmail.send'
  #   flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
  #   flow.user_agent = APPLICATION_NAME
  #     credentials = tools.run_flow(flow, store)
  # return credentials

def get_service():
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

  # If modifying these scopes, delete the file token.pickle.
  SCOPES = ['https://mail.google.com/']
  creds = None
  # The file token.pickle stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
      creds = pickle.load(token)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          os.path.join(BASE_DIR, 'Google/credentials.json'), SCOPES)
      creds = flow.run_local_server(port=8001)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
      pickle.dump(creds, token)

  service = build('gmail', 'v1', credentials=creds)

  return service