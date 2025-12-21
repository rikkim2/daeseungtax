from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import connection

from app.models import MemUser
from app.models import MemAdmin
from app.models import MemDeal
from app.models import 전자세금계산서
from app.models import userProfile

from app.test import utils
from app.test import jsHometax
from app.test import jsHometax_Screen_UTXPPAAA24 #개인TIN값
from app.test import jsHometax_Screen_UTECRCB013 #현금영수증 매출

from app.test import elecResult_Save

import socket
import os,glob

import pandas as pd
from pandas import DataFrame
import tkinter
from tkinter.filedialog import askopenfilename
import pyautogui
import pyperclip
import img2pdf
import mouse
import subprocess
import psutil
import pywinauto
from pywinauto.keyboard import send_keys
from pywinauto import keyboard    # 단축키 기능을 이용하기 위해서
from pywinauto import Desktop, Application, timings
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException,NoAlertPresentException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import UnexpectedAlertPresentException

import time
import math
import xlwt
from openpyxl import Workbook
from selenium.webdriver.support.ui import Select
from datetime import datetime
from datetime import timedelta 
from selenium.webdriver.chrome.service import Service
import multiprocessing
from glob import glob

pyautogui.FAILSAFE = False#마우스가 모서리로 이동하여 에러발생시키는 것을 방지
semusarangID='daeseung4';htxLoginID = 'daeseung20'
isSemusarangOn = False
myIP = socket.gethostbyname(socket.gethostname())
if myIP=='115.88.70.130':  semusarangID='daeseung6';  htxLoginID = "daeseung23"  #서버                    
if myIP=='123.142.103.148': semusarangID='daeseung1'; htxLoginID = "daeseung20"  #디비서버                    
if myIP=='192.168.0.3':   semusarangID='daeseung15';  htxLoginID = "daeseung29"  #i9-13900   - 세무사랑 전용
if myIP=='192.168.0.18':  semusarangID='daeseung20';  htxLoginID = "daeseung27"  #i7-4790-1  - 세무사랑 전용 / 312설치로 escape literal err 발생           
if myIP=='192.168.0.19':  semusarangID='daeseung21';  htxLoginID = "daeseung22"  #i7-4790-2  - 세무사랑 전용 / 312설치로 escape literal err 발생

if myIP=='192.168.0.10':  semusarangID='daeseung14';  htxLoginID = "daeseung31"  #i7-8700 - 스크래핑 전용               
if myIP=='192.168.0.16':  semusarangID='daeseung3';   htxLoginID = "daeseung32"  #i5-6600 - 스크래핑 전용
if myIP=='192.168.0.20':  semusarangID='daeseung10';  htxLoginID = "daeseung35"  #i7-7700 - 스크래핑 전용 /  / 312설치로 escape literal err 발생
               
if myIP=='192.168.0.21':  semusarangID='daeseung12';  htxLoginID = "daeseung36"  #i9-12900    사용안함(서울에 있음)   
if myIP=='192.168.0.22':  semusarangID='daeseung3';   htxLoginID = "daeseung37"  #i9-10900th   크롬문제 해결안됨
      
print(myIP)
@login_required(login_url="/login/")
def index(request):
  context = {}


  return render(request, "admin/auto.html",context)

