from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models import MemAdmin
from app.models import userProfile
from django.db import connection
import os
import imaplib
import imapclient
import email
import datetime
from datetime import date

now = datetime.datetime.now()

@login_required(login_url="/login/")
def index(request):
  context={}
  mem_admin = MemAdmin.objects.get(admin_id=request.user.username)  
  userprofile = userProfile.objects.filter(title=mem_admin.seq_no)
  if userprofile:    userprofile = userprofile.latest('description')
  if userprofile is not None:    context['userProfile'] = userprofile  
  context['memadmin'] = mem_admin  
  return render(request, "admin/main-dash.html",context)
