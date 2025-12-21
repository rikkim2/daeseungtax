import os
import pyautogui
import time
from datetime import timedelta
import pyperclip
import pywinauto
import subprocess
from pywinauto.keyboard import send_keys
from pywinauto import keyboard    # 단축키 기능을 이용하기 위해서
from pywinauto import Desktop, Application, timings
from decimal import Decimal
from django.db import connection
from app.models import MemUser
from app.models import MemDeal
from app.test import utils
from datetime import datetime,timezone
import pandas as pd
import numpy as np
from pandas import DataFrame
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.alert import Alert

from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from app.test import utils

#홈택스 전체메뉴 접근
def Htx_TotalMenu(driver,flagTab,menuName):
	tmpLink = '';tmpLink2 = ''
	if menuName == '표준재무제표증명원':        tmpLink = 'grpMenuLi_43_4301180000'
	elif menuName == '부가가치세과세표준증명원': tmpLink = 'grpMenuLi_43_4301050000'
	elif menuName == '소득금액증명원':          tmpLink = 'grpMenuAtag_43_4301100000'
	elif menuName == '국세완납증명원':          tmpLink = 'grpMenuLi_43_4301030000'
	elif menuName == '고지세액조회':            tmpLink = 'grpMenuAtag_48_4803010000'
	elif menuName == '체납세액조회':            tmpLink = 'grpMenuAtag_48_4803030000'
	elif menuName == '부가가치세 일반과세자': 	tmpLink = 'grpMenuAtag_41_4102010000'
	#지급명세서
	elif menuName == '근로소득': 							tmpLink = 'grpMenuAtag_44_4402010100';tmpLink2 = 'grpMenuLi_44_4402010000'
	elif menuName == '퇴직소득': 							tmpLink = 'grpMenuAtag_44_4402010300';tmpLink2 = 'grpMenuLi_44_4402010000'
	elif menuName == '사업소득': 							tmpLink = 'grpMenuAtag_44_4402020100';tmpLink2 = 'grpMenuLi_44_4402020000'
	elif menuName == '기타소득': 							tmpLink = 'grpMenuAtag_44_4402020300';tmpLink2 = 'grpMenuLi_44_4402020000'
	elif menuName in ('이자소득','배당소득'):		tmpLink = 'grpMenuAtag_44_4402030100';tmpLink2 = 'grpMenuLi_44_4402030000'
	#세무대리
	elif menuName == '기장대리수임납세자등록':		tmpLink = 'grpMenuLi_48_4804010000'   #'grpMenuAtag_48_4804010000'
	elif menuName == '기장대리수임납세자조회':		tmpLink = 'grpMenuLi_48_4804040000'   #'grpMenuAtag_48_4804040000'
	elif menuName == '기장대리수임납세자해지':		tmpLink = 'grpMenuLi_48_4804020000'   #'grpMenuAtag_48_4804020000'
	WebDriverWait(driver, 61).until(EC.element_to_be_clickable((By.ID, "group878"))).click();print('전체메뉴')
	# driver.find_element(By.ID,'group878').click(); time.sleep(3); 
	iframe = driver.find_element(By.CSS_SELECTOR,'#txppIframe');    driver.switch_to.frame(iframe);    time.sleep(1);print('iframe txppIframe')
	WebDriverWait(driver, 61).until(EC.element_to_be_clickable((By.ID,f'tabControl8_tab_{flagTab}'))).click();print(f'전체메뉴  > {menuName}') ;time.sleep(1)
	# driver.find_element(By.ID,f'tabControl8_tab_{flagTab}').click() ;driver.implicitly_wait(1);   time.sleep(0.5) 
	if tmpLink2:		WebDriverWait(driver, 61).until(EC.element_to_be_clickable((By.ID,tmpLink2))).click();print(f'{flagTab} : {tmpLink2}') ;time.sleep(1)
	# if tmpLink2:		driver.find_element(By.ID,tmpLink2).click() ;driver.implicitly_wait(3)  
	if menuName == '소득금액증명원':pyautogui.press('pgdn');time.sleep(1)
	WebDriverWait(driver, 61).until(EC.element_to_be_clickable((By.ID,tmpLink))).click();print(f'{flagTab} : {tmpLink}')   ;time.sleep(2)
	# driver.find_element(By.ID,tmpLink).click() ;driver.implicitly_wait(3)
	iframe = driver.find_element(By.CSS_SELECTOR,'#txppIframe');    driver.switch_to.frame(iframe);    time.sleep(1);print('iframe txppIframe')
	WebDriverWait(driver, 61).until(EC.element_to_be_clickable((By.ID,'textbox3456'))).click();print(f'{flagTab} : 파일변환신고')   ;time.sleep(1)
	
	
	time.sleep(1);print(f'{menuName} : 메뉴 진입') 
	return True	
# 전자신고이력이 있는지 확인하고 신고한 아이디 리턴
def SemusarangID_Check(flag,seq_no,workyear,text_mm,KwaseKikan,KwaseyuHyung,semusarangID):
	# semusarangID="";
	strsql = ""
	memuser = MemUser.objects.get(seq_no=seq_no)  
	memdeal = MemDeal.objects.get(seq_no=seq_no)  
	biz_manager = memdeal.biz_manager
	biz_no = memuser.biz_no
	
	if flag=='vat':				strsql = "select isnull(제출자,'') from 부가가치세전자신고3 where 과세기간='"+KwaseKikan+"'  and 사업자등록번호='"+biz_no+"' and 과세유형='"+KwaseyuHyung+ "'";print(strsql)
	elif flag=='wonchun' or flag=='wonchun-wetax':	strsql = "select isnull(제출자,'') from 원천세전자신고 where 과세연월='"+ workyear+text_mm + "' and  사업자등록번호='" + biz_no + "'";print(strsql)
	elif flag=='corp':	strsql = "select isnull(사용자ID,'') from 법인세전자신고2 where 과세년월='"+ KwaseKikan+ "' and 사업자번호='"+memuser.biz_no+"'";print(strsql)
	elif flag=='income':	strsql = "select isnull(제출자,'') from 종합소득세전자신고2 where 과세년월='"+ KwaseKikan+ "' and 이름='"+memuser.ceo_name+"' and left(주민번호,6)='"+memuser.ssn[:6]+ "'";print(strsql)
	elif flag=='ZZMS-Kunro':	strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='근로소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	elif flag=='ZZMS-Toijik' :strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='퇴직소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	elif flag=='ZZMS-Saup' :	strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='거주자 사업소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	elif flag=='ZZMS-Kita':		strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='거주자 기타소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	elif flag=='ZZMS-50':strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='이자소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	elif flag=='ZZMS-60':strsql = f"select isnull(접수자,'') from 지급조서전자신고 where 신고서종류='배당소득지급명세서' and 과세연도='{workyear}' and 사업자번호='{memuser.biz_no}'";print(strsql)
	if strsql:
		cursor = connection.cursor();print(strsql)
		cursor.execute(strsql)
		results = cursor.fetchall()
		connection.commit()		
		if results and results[0][0]!='':	semusarangID = results[0][0]
	return semusarangID


#홈택스 전자신고
def SS_ElecIssue(flag,SeqNo,workyear,neededIncase,isJungKi) :
	memuser = MemUser.objects.get(seq_no=SeqNo)
	memdeal = MemDeal.objects.get(seq_no=SeqNo) 

	filename = "c:\\ABC\\2208533586"+str(datetime.now())[:10].replace("-","")
	if flag=='vat':
		if isJungKi in {1,2}:    
			if memuser.biz_type ==5:  filename += ".102" 
			else:											filename += ".101" 
		elif isJungKi==4 :        filename += ".103" 
	elif flag=='corp':					filename = "c:\\ABC\\"+str(datetime.now())[:10].replace("-","") + "D100100.01"   
	elif flag=='corp-wetax':		filename = "c:\\ABC\\"+str(datetime.now())[:10].replace("-","") + "D100100.101"  
	elif flag=='income' :				filename = "c:\\ABC\\"+str(datetime.now())[:10].replace("-","") + ".C110700.01"   
	elif flag=='income-wetax':  filename = "c:\\ABC\\enc"+str(datetime.now())[:10].replace("-","") + ".C10"   
	elif flag=='wonchun':           
		filename = "c:\\ABC\\"+str(datetime.now())[:10].replace("-","")+"C103900.01"   
		if isJungKi ==3:filename = "c:\\ABC\\"+str(datetime.now())[:10].replace("-","")+"C103900.03"
	elif flag=='wonchun-wetax':     
		if memdeal.goyoung_banki=="N":#반기신고 아닌경우
			filename = "C:\\ABC\\"+str(datetime.now())[:10].replace("-","")+"A103900.1"
		else:
			filename = "C:\\ABC\\"+str(datetime.now())[:10].replace("-","")+"A103900.2"
	elif flag=='Kani-Saup':         filename = "c:\\ABC\\SF2208533.586"
	elif flag=='Kani-Kunro':        filename = "c:\\ABC\\SC2208533.586"
	elif flag=='Kani-Ilyoung':      filename = "c:\\ABC\\I2208533.586"
	elif flag=='ZZMS-Kunro':        filename = "c:\\ABC\\C2208533.586"
	elif flag=='ZZMS-Saup':         filename = "c:\\ABC\\F2208533.586"
	elif flag=='ZZMS-Kita':         filename = "c:\\ABC\\G2208533.586"
	elif flag=='ZZMS-Toijik':       filename = "c:\\ABC\\EA2208533.586"
	elif flag in ('ZZMS-50','ZZMS-60'):			      filename = "c:\\ABC\\B2208533.586"
	path = "/".join(filename.split("\\")[:-1]) + "/";print(path)
	file_name = filename.split("/")[-1] ;print(file_name)   
	htxLoginID = "";elecfile=""
	if  flag not in ('wonchun-wetax','corp-wetax','income-wetax'):
		try:
			elecfile = open(filename,'r')  
		except:
			print('전자신고파일 없음')
			return False

	if flag=='vat':
		directory = "D:/"+memuser.biz_name+"/"+str(workyear)+"/부가세/"+neededIncase   ;print(directory)
		wcVatTax = 0 #차가감납부세액
		while True:
			line = elecfile.readline(); 
			if not line:   break
			if memuser.biz_type ==5:
				if line[:9] == "12I106000":  htxLoginID = line[37:57].replace(' ','')   #간이과세자 부가세 신고서 
			else:
				if line[:9] == "11I103200":  htxLoginID = line[37:57].replace(' ','')   #일반과세자 부가세 신고서 
					
			if line[:9] == "17I103200":     #일반과세자 부가세 신고서 세부내용
				txtVatTax = line[863:878]
				if txtVatTax[:1]=="-":wcVatTax = int(txtVatTax[1:])*-1
				else:                 wcVatTax = int(txtVatTax)
		elecfile.close() 

		driver = utils.conHometaxLogin(htxLoginID,False);time.sleep(1)
		driver.get('https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=41&tm2lIdx=4102000000&tm3lIdx=4102080000');time.sleep(3);	
		button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_pf_UTERNAAZ0Z11_btnFleTrns')))
		button.click();		    time.sleep(0.5);print('파일변환신고 클릭')	
		
		try:#부가세 신고관련 팝업이 발생하는 경우
			iframe = driver.find_element(By.CSS_SELECTOR,'#UTERNAA892_iframe');   driver.switch_to.frame(iframe);    time.sleep(0.3);print('팝업 닫기')
			driver.find_element(By.ID,'btnClose2').click()  ;    time.sleep(0.3); print('닫기')
		except:
			print('부가세 신고관련 팝업 없음')

		button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger111')))
		button.click();    time.sleep(1);print('찾아보기')

		#이미 검증이 완료된 자료가 존재합니다.
		try:
			WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger111').click();    time.sleep(1);print('찾아보기')#다시한번 찾아보기 클릭 -> 파일선택창
		except :
			print('최초시도 인 경우')
		

		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(0.5);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(0.5);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		pyautogui.press('esc',presses=4,interval=0.25)#잘못된 팝업 털기
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2759').click();    time.sleep(1);print('형식검증하기');time.sleep(5)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2826').click();    time.sleep(1);print('형식검증결과확인');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2763').click();    time.sleep(1);print('내용검증하기');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2828').click();    time.sleep(1);print('내용검증결과확인');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2828').click();    time.sleep(1);print('내용검증결과확인');time.sleep(1)
		try:
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_group2764').click();    time.sleep(1);print('전자파일제출');time.sleep(1)
		except:
			print(f'{memuser.biz_name} : 전자신고시 내용검증오류 있음')
			return 0
		try:
			button = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger104_UTERNAAZ48')))
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger104_UTERNAAZ48').click();      time.sleep(2) #조회하기 후 대기시간 필수			
		except UnexpectedAlertPresentException:
			# alert 팝업이 예상하지 않은 시점에 나타났을 때 처리할 코드 작성
			try:
				WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)  
			except TimeoutException:   
				driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger104_UTERNAAZ48').click();    time.sleep(1);print('전자파일 제출하기')
		#정상변환된 신고서를 제출합니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(0.5)    
		#신고서를 제출합니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(0.5)    
		try:
			#이미 제출완료된 신고서 입니다
			WebDriverWait(driver, 2).until(EC.alert_is_present());al = Alert(driver);al.accept();print('이미 제출완료된 신고서 입니다 팝업 닫기');time.sleep(1)  
		except:
			print("이미 제출완료된 신고서 입니다 alert 없음")
		button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAZ02_wframe_trigger2')))#trigger2
		button.click(); time.sleep(0.5); print('닫기')
		try:
			#부가가치세 전자신고 접수가 완료되었습니다.설문조사에 참여하시겠습니까?
			WebDriverWait(driver, 1).until(EC.alert_is_present());al = Alert(driver);al.dismiss();print('부가가치세 전자신고 접수가 완료되었습니다.설문조사에 참여하시겠습니까? 팝업 닫기');time.sleep(1)  
		except:
			print("부가가치세 전자신고 접수가 완료되었습니다.설문조사에 참여하시겠습니까? alert 없음")

		#신고결과 저장
		tabbtn = driver.find_element(By.ID,'mf_txppWframe_tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11_tabHTML')
		tabbtn.click();print('신고내역조회 탭클릭')
		#신고내역조회로 이동합니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1);print("신고내역조회로 이동합니다")      
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').clear()
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').send_keys(memuser.biz_no);time.sleep(0.25);    
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_trigger70_UTERNAAZ31').click();print('사업자번호로 조회하기')
		#팝업 컨트롤 - 조회결과 있어도 팝업, 업어도 팝업 없는 경우 테이블데이터 없는 것으로 체크
		WebDriverWait(driver, 5).until(EC.alert_is_present()); al = Alert(driver); al.accept(); time.sleep(3)  
		# 테이블 가져오기
		table = driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_body_table')
		tbody = table.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_body_tbody')    
		print(memuser.biz_no+' 조회결과')
		print(len(tbody.find_elements(By.TAG_NAME,'tr')))
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			ElecIssue.action_ElecIssue(driver,flag,filename,cols)
			
			if wcVatTax>0:
				btnVatTax = driver.find_element(By.XPATH,'//*[@id="mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_cell_0_13"]/nobr/button')
				if btnVatTax.is_displayed():      
					btnVatTax.click();time.sleep(3);driver.implicitly_wait(20)
					fullFileName = directory + "/200.pdf"  #부가세납부서
					if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
					pyautogui.press('tab');time.sleep(3);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(1)
					pyautogui.press('tab',presses=6,interval=0.5);pyautogui.press('enter') ;time.sleep(3)  ;driver.implicitly_wait(10)
					utils.FileSave_Downloaded_PDF(directory,'','200.pdf',memuser.seq_no);print(memuser.biz_name + '부가세 납부서 저장완료')
					pyautogui.hotkey('alt','f4')
					main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]); 

	elif flag=='wonchun':     
		directory = "D:/"+memuser.biz_name+"/"+str(workyear)+"/인건비"   ;print(directory)
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:9] == "21C103900":     htxLoginID = line[49:69].replace(' ','')
			if line[:12]== "23C103900A99":  wcZ = int(line[27:42]);  wcZman = int(line[12:27]);  wcZtax = int(line[102:117])
		elecfile.close()      
		driver = utils.conHometaxLogin(htxLoginID,False)
		
		driver.get("https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=41&tm2lIdx=4106000000&tm3lIdx=4106010000")
		# 오버레이가 사라질 때까지 기다림
		WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, 'mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal')))
		# 4. 일정 시간 동안 팝업이 뜨는지 감지하고, 뜨면 정리한 뒤 메인으로 복귀
		try:
				main_handle = driver.current_window_handle
				# 기존 핸들 목록
				old_handles = driver.window_handles
				# 새 창이 열리면 감지 (최대 5초 정도)
				WebDriverWait(driver, 5).until(
						EC.new_window_is_opened(old_handles)
				)				
				# 새 창(팝업) 처리 후 메인으로 돌아가기
				utils.focus_main_window(driver, main_handle)

		except TimeoutException:
				# 새 창이 안 뜬 경우 그냥 무시
				pass
		print('파일변환신고 버튼 클릭 전')
		textbox_btn = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_pf_UTERNAAZ0Z11_btn_cbcMediRtn')))
		# textbox_btn.click()
		driver.execute_script("arguments[0].click();", textbox_btn)
		print('파일변환신고 클릭');time.sleep(0.1)

		pyautogui.press('enter');
		# 오버레이가 사라질 때까지 기다림
		WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, 'mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal')))		
		button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_pf_UTERNAAZ0Z11_btn_selFileB')))
		button.click();		print('파일선택 클릭')		

		#이미 검증이 완료된 자료가 존재합니다.
		if not utils.Htx_Modal_Clear(driver, '이미 검증이 완료된 자료가 존재합니다.',timeout=5):
				# 모달을 닫았으니 다시 파일선택 버튼 클릭
				button = WebDriverWait(driver, 10).until(
						EC.element_to_be_clickable(
								(By.ID, 'mf_txppWframe_pf_UTERNAAZ0Z11_btn_selFileB')
						)
				)
				button.click()
				print('이미 검증된 자료 → 다시 파일선택 클릭')

		if not utils.wait_file_dialog_open():
				print("⚠ 파일 선택창이 열리지 않아 pyautogui 입력은 스킵합니다.")
		else:
				# 4) 파일 경로 입력 (기존 로직 유지)
				pyautogui.hotkey('alt','d')
				print('c:\\ABC 선택')
				time.sleep(0.5)
				pyperclip.copy(path)
				pyautogui.hotkey('ctrl', 'v')
				pyautogui.press('enter');time.sleep(0.5)
		pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		pyautogui.press('esc',presses=3,interval=0.25)#잘못된 팝업 털기
		driver.find_element(By.ID,'mf_txppWframe_pf_UTERNAAZ0Z11_btn_cenSts').click();    time.sleep(1);print('파일검증하기');time.sleep(4)
		try:
			WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(0.5) ;print('경고알람') 
			driver.find_element(By.ID,'trigger104_UTERNAAZ63').click();    time.sleep(1);print('확인');time.sleep(1)
		except:
			print('경고없음')		   

		BLUR_BOX_ID   = "mf_txppWframe_pf_UTERNAAZ0Z11_grp_blur_box"            # '변환파일 검증 중입니다.' 레이어
		NORMAL_CNT_ID = "mf_txppWframe_pf_UTERNAAZ0Z11_tbx_tbcntnVrfNrmlScnt"   # 정상납세자수 span

		def wait_validation_and_go_next(driver, timeout=120):
				wait = WebDriverWait(driver, timeout)

				try:
						# 1) '검증 중' 레이어가 한번이라도 뜨는지 (짧게) 기다렸다가
						try:
								WebDriverWait(driver, 10).until(
										EC.visibility_of_element_located((By.ID, BLUR_BOX_ID))
								)
								print("[검증] '변환파일 검증 중입니다' 레이어 표시 확인")
						except TimeoutException:
								# 너무 빨리 끝나거나 안 보일 수도 있으니, 이 부분은 그냥 통과
								print("[검증] 진행중 레이어는 보이지 않았지만 계속 진행")

						# 2) 검증이 끝나면서 레이어가 사라질 때까지 대기
						wait.until(
								EC.invisibility_of_element_located((By.ID, BLUR_BOX_ID))
						)
						print("[검증] 진행중 레이어 종료 확인")

						# 3) 결과 영역(정상납세자수 span)이 나타날 때까지 대기
						normal_el = wait.until(
								EC.visibility_of_element_located((By.ID, NORMAL_CNT_ID))
						)
						text = normal_el.text.strip().replace(",", "")  # "1", "1,234" 대비
						normal_cnt = int(text or 0)
						print(f"[검증] 정상납세자수 = {normal_cnt}")

						if normal_cnt == 1:
								print("[검증] 정상납세자수 1명 → 다음 단계 진행")
								# ── 여기서 다음 단계(예: '신고서 작성' 버튼 클릭 등)를 호출 ──
								# click_next_step_button(driver)
								return True
						else:
								print("[검증] 정상납세자수 1이 아님 → 다음 단계 진행 안 함")
								return False

				except TimeoutException as e:
						print("[검증] 검증/결과 대기 중 타임아웃:", e)
						raise
		# 2. 검증 완료 + 정상납세자수 체크 후 다음 단계로
		ok = wait_validation_and_go_next(driver)
		if not ok:
				# 오류 납세자수 있으면 로그 찍거나 예외 처리
				print("정상납세자수가 1이 아니라서 중단합니다.")
				return
		utils.click_button_3attempt(driver,'mf_txppWframe_pf_UTERNAAZ0Z11_btn_rigSts');print('제출하러 가기')
		utils.click_button_3attempt(driver,'mf_txppWframe_pf_UTERNAAZ0Z11_btn_confirm');print('전자파일 제출하기')
		utils.Htx_Modal_Clear(driver, '정상 변환된 신고서를 제출합니다.',timeout=2)
		utils.Htx_Modal_Clear(driver, '신고서를 제출하시겠습니까?',timeout=2)
		try:
			WebDriverWait(driver, 10).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('이미 제출완료된 신고서 입니다.')
		except:
			print('경고없음')
		closeBtn = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'mf_txppWframe_pf_UTERNAAZ0Z11_UTERNAAZ02_wframe_trigger2')));    
		time.sleep(0.1);print('인쇄팝업 닫기')
		closeBtn.click()  ;    time.sleep(0.1); print('닫기')
		driver.find_element(By.ID,'mf_txppWframe_btnRtnInqr').click();    time.sleep(1);print('신고내역조회 클릭(모달)')
	 
		driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_input_txprRgtNo_UTERNAAZ31').clear()#사업자번호 인풋박스
		driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_input_txprRgtNo_UTERNAAZ31').send_keys(memuser.biz_no);time.sleep(0.25);    
		driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_trigger70_UTERNAAZ31').click();print('사업자번호로 조회하기 버튼')#한 사업자를 대상으로 한다
		utils.Htx_Modal_Clear(driver, '조회가 완료되었습니다.',timeout=2)
		# 테이블 가져오기                   
		table = driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_ttirnam101DVOListDes_body_table')
		tbody = table.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_ttirnam101DVOListDes_body_tbody')    
		print(memuser.biz_name+' 조회결과')  
		for i,tr in enumerate(tbody.find_elements(By.TAG_NAME,'tr')):
			if i==0:
				cols = tr.find_elements(By.TAG_NAME,'td')
				print(cols)
				wcKwase = cols[2].text  ;print(' 과세연월 : '+wcKwase)
				issueMM = wcKwase[-3:].replace("년", "").replace("월", "");print(' intmm : '+issueMM)        
				ElecIssue.action_ElecIssue(driver,flag,filename,cols)
				if wcZtax>0:
					pyautogui.press('pgdn');time.sleep(0.25)    ;print('페이지다운')
					btnNapbuTax = driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_ttirnam101DVOListDes_cell_0_13')
					if btnNapbuTax.is_displayed():      
						btnNapbuTax.click();time.sleep(0.1)
						table = driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_UTERNAAB40_wframe_ttirnal111DVOListDes_body_table')
						tbody = table.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_UTERNAAB40_wframe_ttirnal111DVOListDes_body_tbody')    
						for i,tr in enumerate(tbody.find_elements(By.TAG_NAME,'tr')):
							cols = tr.find_elements(By.TAG_NAME,'td')
							tdTax = cols[5].text.split("(")[0]  # 소득세 종류  
							td6ID = 'mf_txppWframe_UTERNAAZ0Z31_wframe_UTERNAAB40_wframe_ttirnal111DVOListDes_cell_'+str(i)+'_6'
							intmm = issueMM
							if memdeal.goyoung_banki=='Y': intmm =  str(int(issueMM)+5)
							fileName = intmm + "월 납부서("+tdTax+").pdf"
							fullFileName = directory + "/"+ fileName   
							btnTDID6 = driver.find_element(By.ID,td6ID)
							try:
								btnTDID6.click();driver.implicitly_wait(10);time.sleep(3)
								if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
								main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]); 
								driver.find_element(By.XPATH,'/html/body/div[1]/div/div[1]/table/tbody/tr/td/div/nobr/button[1]').click();time.sleep(3);driver.implicitly_wait(10)
								pyautogui.press('tab',presses=6,interval=0.3);time.sleep(1);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(3)
								utils.FileSave_Downloaded_PDF(directory,'',fileName,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
								pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  
								main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]); 
                        
							except:
								print(tdTax+' 납부서는 없습니다.')
						driver.find_element(By.ID,'mf_txppWframe_UTERNAAZ0Z31_wframe_UTERNAAB40_wframe_trigger7').click();time.sleep(0.2);print('닫기')
		return wcZtax      
	elif flag=='wonchun-wetax':       
		directory = "D:/"+memuser.biz_name+"/"+str(workyear)+"/인건비"  
		max_retries = 10  # 최대 재시도 횟수
		retry_interval = 1  # 재시도 간격 (초)    
		driver = utils.conWetaxLogin(False);time.sleep(1)
		driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(2); print('전체메뉴')
		driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[1]/ul/li[1]/a').click();time.sleep(1); print('특별징수신고 ')
		driver.find_element(By.ID,'btnFileCfmtnDclr').click();time.sleep(1); print('회계파일신고')
		acntBtn = driver.find_element(By.XPATH,r'//*[@id="frmUpload"]/div/div/div/div/label').click();  time.sleep(1.5); print('파일첨부');  
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(1);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(1);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		driver.find_element(By.ID,'filePw').send_keys('11111111')
		WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="btn_next"]'))).click();time.sleep(1)
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('업로드하신 회계파일의 신고정보를 검증합니다') 
		print(f"정상신고건수 :{driver.find_element(By.ID,'spnTotCnt').text}")
		if driver.find_element(By.ID,'spnTotCnt').text!='0':
			# 테이블 가져오기
			table = driver.find_element(By.ID,'tblMain')
			tbody = table.find_element(By.ID,'tbodyMain')    
			wcWetax = 0;
			print(len(tbody.find_elements(By.TAG_NAME,'tr')))
			for tr in tbody.find_elements(By.TAG_NAME,'tr'):
				cols = tr.find_elements(By.TAG_NAME,'td')
				wcWetax = int(cols[6].text.replace(",","").replace("원","")	);print(f"납부세액 : {cols[6].text}")		
				break;
			driver.find_element(By.ID,'btn_next').click();time.sleep(1)
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('제출하시겠습니까') 
			if wcWetax>0:
				#특별징수신고내역으로 이동해서 조회하기 실패
				# driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(1); print('전체메뉴')
				# driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[1]/ul/li[2]/a').click();time.sleep(1); print('특별징수신고내역 ')
				# driver.find_element(By.XPATH,'//*[@id="contents"]/div[1]/button').click();time.sleep(1); print('상세검색 ')
				# pyautogui.press('tab',presses=9,interval=0.3);pyautogui.write(memuser.biz_no)
				# driver.find_element(By.XPATH,'//*[@id="btnSearch"]').click();time.sleep(1); print('검색버튼 ')			
				# if driver.find_element(By.ID,'spnTotCnt').text=='1':##정상 제출됐음에도 제출결과가 0으로 나오고 있다
					# 테이블 가져오기
					# table = driver.find_element(By.ID,'tblMain')
					# tbody = table.find_element(By.XPATH,'//*[@id="tblMain"]/tbody') 		
					# for tr in tbody.find_elements(By.TAG_NAME,'tr'):
					# 	cols = tr.find_elements(By.TAG_NAME,'td')		
					# 	link = cols[5].find_element(By.TAG_NAME, 'a')
					# 	ActionChains(driver).move_to_element(link).click().perform();time.sleep(2)
					# 	break
					driver.find_element(By.ID,'btnPayReport').click();time.sleep(2)
					main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
					pyautogui.press('tab');time.sleep(0.5);					pyautogui.press('enter');time.sleep(0.5);print('지방세 납부서')
					pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5);
					intmm = str(int(neededIncase))
					if memdeal.goyoung_banki=='Y': intmm =  str(int(intmm)+5)
					fileName = intmm + "월 납부서(지방소득세).pdf"
					utils.FileSave_Downloaded_PDF(directory,'',fileName,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
					pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  					
			else:
				print('지방세 신고를 정상적으로 마쳤습니다. 납부할 지방세가 없습니다.')    
		else:#오류인경우
			# 테이블 가져오기
			table = driver.find_element(By.ID,'tbl_errList')
			tbody = table.find_element(By.ID,'tbody_errList')    
			print(memuser.biz_no+' 조회결과')
			print(len(tbody.find_elements(By.TAG_NAME,'tr')))
			for tr in tbody.find_elements(By.TAG_NAME,'tr'):
				cols = tr.find_elements(By.TAG_NAME,'td')
				print(f"항목명(자료구분) : {cols[1].text}")
				print(f"오류내용 : {cols[2].text}") 
	elif flag=='corp' :			
		biz_no="";sanchul="";wcTotLocalTax="";wcTotCorpTax="";wcBunapTax = "";seq_no = "";biz_name = ""
		while True:
			line = elecfile.readline()   
			if not line:   break
			if line[:9] == "81D100100": 
				htxLoginID = utils.retrieve_words_from_end(line, "2208533586") 		
				biz_no = line[17:28];
				biz_noWithDash = biz_no[:3]+"-"+biz_no[3:5]+"-"+biz_no[5:10]
			if line[:9]== "83D100100":
				sanchul       = line[151:166];
				wcTotLocalTax = int(int(sanchul)/100*10)
				wcTotCorpTax  = line[286:301];
				wcBunapTax    = line[301:316]
				memuser = MemUser.objects.get(biz_no=biz_no[:3]+"-"+biz_no[3:5]+"-"+biz_no[5:10])
				seq_no=memuser.seq_no;biz_name = memuser.biz_name
				directory = "D:/"+memuser.biz_name+"/"+str(workyear)+"/세무조정계산서"   ;print(directory)
				if wcTotCorpTax[:1]=="-":wcTotCorpTax = int(wcTotCorpTax[1:])*-1
				else: wcTotCorpTax = int(wcTotCorpTax);wcBunapTax = int(wcBunapTax)				
		elecfile.close() 	
		driver = utils.conHometaxLogin(htxLoginID,False);time.sleep(1)
		# Wait for the modal to disappear
		WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal')))
		WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_wfHeader_hdGroup005'))).click();time.sleep(0.1);print('전체메뉴')   
		driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('법인세 정기신고');pyautogui.press('enter');time.sleep(1)
		pyautogui.press('tab',presses=2,interval=0.3);pyautogui.press('enter');time.sleep(1);	

		driver.find_element(By.XPATH,'//*[@id="mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAA08_wframe_chkYn"]/div/label').click();		    time.sleep(0.5);print('팝업-확인하였습니다')	
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAA08_wframe_btnClose2').click();		    time.sleep(0.5);print('팝업-닫기')	
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(0.5);print('팝업 닫기 알람 - 닫기')
		except TimeoutException as ex:
			print('팝업 닫기 알람 - 닫기 오류')

		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_textbox8651').click();		    time.sleep(1);print('파일변환신고 클릭')	
		
		button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger111')))
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger111').click();    time.sleep(1);print('찾아보기')
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1);print('이미 검증이 완료된 자료가 존재합니다.')
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger111').click();    time.sleep(1);print('찾아보기')#다시한번 찾아보기 클릭 -> 파일선택창
		except TimeoutException as ex:
			print('최초시도 인 경우')
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger111').click();    time.sleep(1);print('찾아보기')#다시한번 찾아보기 클릭 -> 파일선택창
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(0.5);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(0.5);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2);  driver.implicitly_wait(30)
		pyautogui.press('esc',presses=3,interval=0.25)#잘못된 팝업 털기
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger93').click();    time.sleep(1);print('형식검증하기');time.sleep(3.5)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger120').click();    time.sleep(1);print('형식검증결과확인');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger96').click();    time.sleep(1);print('내용검증하기');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger121').click();    time.sleep(1);print('내용검증결과확인');time.sleep(3)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger121').click();    time.sleep(1);print('내용검증결과확인');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger97').click();    time.sleep(1);print('전자파일제출');time.sleep(1)   

		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger104_UTERNAAZ48').click();    time.sleep(1);print('전자파일 제출하기');time.sleep(1)
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('정상변환된 신고서를 제출합니다') 
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('신고서를 제출합니다')
		
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('이미 제출완료된 신고서 입니다')
		except:
			print('pass')
		# iframe = driver.find_element(By.CSS_SELECTOR,'#UTERNAAZ02_iframe');    driver.switch_to.frame(iframe);    time.sleep(1);print('인쇄팝업 닫기')
		# WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'group6'))).click();time.sleep(1); print('제출내역확인 닫기')

		WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAZ02_wframe_trigger2'))).click();time.sleep(1); print('접수증 팝업 닫기')
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.dismiss();time.sleep(1) ;print('설문조사에 참여하시겠습니까 -> 취소')

		driver.find_element(By.ID,'mf_txppWframe_tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11_tabHTML').click();    time.sleep(1);print('신고내역조회 클릭')
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('이용중인 서비스 종료하고 신고내역 조회 (접수증 · 납부서) 화면으로 이동?')

		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').clear()
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').send_keys(biz_no);time.sleep(0.25);    
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_trigger70_UTERNAAZ31').click();print('사업자번호로 조회하기')
		#팝업 컨트롤 - 조회결과 있어도 팝업, 업어도 팝업 없는 경우 테이블데이터 없는 것으로 체크
		WebDriverWait(driver, 5).until(EC.alert_is_present()); al = Alert(driver); al.accept(); time.sleep(1)  
		# 테이블 가져오기
		pyautogui.press('pgdn');time.sleep(0.5)	
		table = driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_scrollX_table')
		tbody = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.ID, "mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_body_tbody"))
		)
		print(biz_no+' 조회결과')
		print(len(tbody.find_elements(By.TAG_NAME,'tr')))
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			ElecIssue.action_ElecIssue(driver,flag,filename,cols)			
			#접수증
			btnSummit = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH,'//*[@id="mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_cell_0_12"]/nobr/button'))
			)
			if btnSummit.is_displayed(): 
				btnSummit.click();time.sleep(3);driver.implicitly_wait(10)
				fullFileName = directory + "/198.pdf"  #법인세신고 접수증
				if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료")
				#접수증 팝업
				main = driver.window_handles;        print(main);        driver.switch_to.window(main[1]) 
				pyautogui.press('tab');time.sleep(3);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(3);driver.implicitly_wait(10)
				utils.FileSave_Downloaded_PDF(directory,'','198.pdf',seq_no);print(biz_name + '법인세신고 접수증 저장완료')
				pyautogui.hotkey('alt','f4')
				main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]); 

			# print(f"wcTotCorpTax:{wcTotCorpTax}")
			# print(f"wcBunapTax:{wcBunapTax}")
			#납부서 - 분납이 아닌 경우만...
			if wcTotCorpTax>0 and wcBunapTax==0:
				btnCorpTax = WebDriverWait(driver, 10).until(
					EC.presence_of_element_located((By.XPATH,'//*[@id="mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_cell_0_13"]/nobr/button'))
				)
				if btnCorpTax.is_displayed():      
					btnCorpTax.click();time.sleep(3);driver.implicitly_wait(20)
					fullFileName = directory + "/200.pdf"  #법인세납부서
					if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
					pyautogui.press('tab');time.sleep(3);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(1)
					pyautogui.press('tab',presses=6,interval=0.5);pyautogui.press('enter') ;time.sleep(3)  ;driver.implicitly_wait(10)
					utils.FileSave_Downloaded_PDF(directory,'','200.pdf',memuser.seq_no);print(memuser.biz_name + '법인세 납부서 저장완료')
					pyautogui.hotkey('alt','f4')
					main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]); 

	elif flag=='corp-wetax':
		directory = "D:/"+memuser.biz_name+"/"+str(workyear)+"/세무조정계산서"  
		driver = utils.conWetaxLogin(False);time.sleep(1)
		driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(2); print('전체메뉴')			
		driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[4]/ul/li[1]/a').click();time.sleep(1); print('법인소득분신고 ')	
		driver.find_element(By.ID,'btnFileCfmtnDclr').click();time.sleep(1); print('회계파일신고')		
		acntBtn = driver.find_element(By.XPATH,r'//*[@id="frmUpload"]/div/div/div/div/label').click();  time.sleep(1.5); print('파일첨부');  
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(1);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(1);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		driver.find_element(By.ID,'clitxFilePwen').send_keys('11111111')
		WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'btn_convert'))).click();time.sleep(1)
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();print('업로드하신 회계파일의 신고정보를 검증합니다') 
		time.sleep(3) 
		max_attempts = 20
		current_attempt = 0
		while current_attempt < max_attempts:		
			WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'btn_srch'))).click();time.sleep(1)
			table = driver.find_element(By.ID, 'dclrFileList')
			tbody = table.find_element(By.XPATH, '//*[@id="dclrFileList"]/tbody')
			wetaxresult = ""
			for tr in tbody.find_elements(By.TAG_NAME, 'tr'):
				cols = tr.find_elements(By.TAG_NAME, 'td')
				if cols[1].text=="11111111":
					wetaxresult = cols[5].text
					print(f"재시도 : {current_attempt}회, 남은 재시도: {max_attempts-current_attempt} 처리완료되지 않았습니다.")
					break #내꺼만 처리한다					
			current_attempt += 1
			time.sleep(10)  # Wait for 3 seconds before the next attempt
			if current_attempt == max_attempts or wetaxresult.strip() == "처리오류":
				print(f"최종처리결과 : {wetaxresult}")
				return 1						
			elif current_attempt==16 or wetaxresult.strip() == "처리완료":
				strsql = f"select 법인등록번호,지방세 from tbl_EquityEval where 사업자번호='{memuser.biz_no}' and 사업연도말='{neededIncase}'"
				corpNo="";wetax = 0
				with connection.cursor() as cursor:
						cursor.execute(strsql)
						result = cursor.fetchone()
						if result:  # 결과가 존재하는 경우에만 처리
								corpNo, wetax = result  # 튜플의 각 요소를 변수에 할당
								if wetax.strip()=="":wetax = 0
								else:wetax = int(wetax)
				connection.commit()
				connection.close()    					
				driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(2); print('전체메뉴')	
				pyautogui.press('pgdn');time.sleep(0.5)		
				linkCorp = driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[4]/ul/li[3]/a'); print('법인소득분신고내역(법인별) ')
				WebDriverWait(driver, 10).until(EC.element_to_be_clickable(linkCorp)).click();time.sleep(4)

				driver.find_element(By.XPATH,'//*[@id="contents"]/div[1]/button').click();time.sleep(0.3);print('상세검색')
				driver.find_element(By.ID,'inqCrno').send_keys(corpNo);time.sleep(0.5)#법인번호 검색
				driver.find_element(By.ID,'btnSearch').click();time.sleep(1.5)
				print(f"검색결과 :{driver.find_element(By.ID,'spnTotCnt').text}")
				if driver.find_element(By.ID,'spnTotCnt').text!='0':
					table = driver.find_element(By.ID, 'tblMain')
					tbody = table.find_element(By.XPATH, '//*[@id="tblMain"]/tbody')
					for tr in tbody.find_elements(By.TAG_NAME,'tr'):
						cols = tr.find_elements(By.TAG_NAME,'td')		

						#접수증
						driver.find_element(By.XPATH,'//*[@id="tblMain"]/tbody/tr/td[7]/a').click();					time.sleep(1);print('성공건수')
						table = driver.find_element(By.ID, 'tblCliDclrPdi')
						tbody = table.find_element(By.XPATH, '//*[@id="tblCliDclrPdi"]/tbody')							
						for tr in tbody.find_elements(By.TAG_NAME,'tr'):
							cols = tr.find_elements(By.TAG_NAME,'td')		
							i_tag = cols[8].find_element(By.TAG_NAME, 'i') 
							i_tag.click();time.sleep(1)
							main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
							pyautogui.press('enter');time.sleep(0.5);print('접수증')
							pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5);
									
							fileName = "199.pdf"
							utils.FileSave_Downloaded_PDF(directory,'',fileName,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
							pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  ;time.sleep(1)
							main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);time.sleep(1)
							driver.find_element(By.XPATH,'//*[@id="btnCliDclrPdiLayerClose"]').click()	;time.sleep(1)	

						#납부서
						if wetax>0:
							driver.find_element(By.XPATH,'//*[@id="tblMain"]/tbody/tr/td[7]/a').click();					time.sleep(1);print('성공건수')
							table = driver.find_element(By.ID, 'tblCliDclrPdi')
							tbody = table.find_element(By.XPATH, '//*[@id="tblCliDclrPdi"]/tbody')							
							for tr in tbody.find_elements(By.TAG_NAME,'tr'):
								cols = tr.find_elements(By.TAG_NAME,'td')		
								i_tag = cols[8].find_element(By.TAG_NAME, 'i') 
								i_tag.click();time.sleep(1)
								main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
								pyautogui.press('tab');time.sleep(0.5);					pyautogui.press('enter');time.sleep(0.5);print('지방세 납부서')
								pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5);
										
								fileName = "201.pdf"
								utils.FileSave_Downloaded_PDF(directory,'',fileName,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
								pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  ;time.sleep(1)
								main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);time.sleep(1)
								driver.find_element(By.XPATH,'//*[@id="btnCliDclrPdiLayerClose"]').click()	;time.sleep(1)	
								# driver.find_element(By.XPATH,'/html/body/div[2]/div[2]/div/div[2]/div/div/button').click()	;time.sleep(1)	
								break#exit for
							

						#접수증
						# driver.find_element(By.XPATH,'//*[@id="tblMain"]/tbody/tr[1]/td[10]/a/i').click();					time.sleep(1)
						# iframe = driver.find_element(By.XPATH,'//*[@id="cmnPopup_reportList"]/div/div/iframe')
						# driver.switch_to.frame(iframe)						
						# table = driver.find_element(By.ID, 'tblReport')
						# tbody = table.find_element(By.XPATH, '//*[@id="tblReport"]/tbody')	
						# for tr in tbody.find_elements(By.TAG_NAME,'tr'):
						# 	cols = tr.find_elements(By.TAG_NAME,'td')		
						# 	if cols[1].text.strip()=="법인지방소득세_접수증":
						# 		link2 = cols[2].find_element(By.TAG_NAME, 'a')#접수증
						# 		ActionChains(driver).move_to_element(link2).click().perform();time.sleep(1)
						# 		main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
						# 		pyautogui.press('tab');time.sleep(0.5);					pyautogui.press('enter');time.sleep(0.5);print('지방세 접수증')
						# 		pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5);
						# 		fileName = "199.pdf"
						# 		utils.FileSave_Downloaded_PDF(directory,'',fileName,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
						# 		pyautogui.hotkey('alt','f4');print('프린트팝업 닫기') 
						# 		break

						break	#exit for
		
				break# exit while - 처리완료시
	elif flag=='income' :
		record_53C110700=[];wcIncomeTax = 0;wcMidTax=0
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:9] == "51C110700":     htxLoginID = line[43:63].replace(' ','')
			if line[:9] == "53C110700":     #종합소득세 세액의계산 레코드
				record_53C110700.append(line)        
				if int(line[261:276])<0 :   wcIncomeTax  = (int(line[203:215])-wcMidTax/10)*-1     
				else:                       wcIncomeTax  =  (int(line[203:215])+wcMidTax/10)          
		elecfile.close() 
		driver = utils.conHometaxLogin(htxLoginID,False);time.sleep(1)
		driver.get('https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=41&tm2lIdx=4103020000&tm3lIdx=4103020500')
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger111')))
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		button.click()
		# driver.execute_script("arguments[0].click();", button)
		print('찾아보기 클릭');time.sleep(0.1)		
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1);print('이미 검증이 완료된 자료가 존재합니다.')
			button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger111')));time.sleep(2);  
			driver.execute_script("arguments[0].click();", button);    time.sleep(1);print('찾아보기')
		except TimeoutException as ex:
			print('최초시도 인 경우')
			# button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_trigger111')));time.sleep(2);  
			# driver.execute_script("arguments[0].click();", button);    time.sleep(1);print('찾아보기')
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(0.5);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(0.5);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2);  driver.implicitly_wait(30)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger93').click();    time.sleep(1);print('형식검증하기');time.sleep(3.5)
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger120').click();    time.sleep(1);print('형식검증결과확인');time.sleep(1)
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger96').click();    time.sleep(1);print('내용검증하기');time.sleep(2)
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger121').click();    time.sleep(1);print('내용검증결과확인');time.sleep(3)
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger121').click();    time.sleep(1);print('내용검증결과확인');time.sleep(2)
		driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger121').click();    time.sleep(1);print('내용검증결과확인');time.sleep(1)
		WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
		trigger97 = driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger97')
		driver.execute_script("arguments[0].click();", trigger97);    time.sleep(1);print('전자파일제출');time.sleep(1)    
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('경고/오류발생') 
			confirmProceed = pyautogui.confirm('전자신고파일에 오류가 있습니다. 프로그램 중단됩니다 [아니오 : 계속진행]') 
			if confirmProceed=="Ok":
				os._exit
			else:
				driver.find_element(By.ID,'trigger104_UTERNAAZ63').click();time.sleep(1)			
		except:
			print('경고/오류 없음')
	
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('신고서를 제출합니다')
			closeBtn = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAZ02_wframe_trigger2')));  time.sleep(0.1);print('인쇄팝업 닫기')
			closeBtn.click()  ;    time.sleep(0.1); print('닫기')		
		except:
			print('알람없음 : 신고서를 제출합니다')
			pyautogui.press('esc',presses=2,interval=0.1)
			agree = driver.find_element(By.CSS_SELECTOR,'#mf_txppWframe_wframe2_UTERNAAZ11_radio1_99_UTERNAAZ48 > div > label');  driver.implicitly_wait(10);  agree.click(); print('동의함2') ;time.sleep(0.5) 		
			driver.find_element(By.ID,'mf_txppWframe_wframe2_UTERNAAZ11_trigger104_UTERNAAZ48').click();    time.sleep(1);print('전자파일 제출하기');time.sleep(1)
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('정상변환된 신고서를 제출합니다2') 	
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('신고서를 제출합니다2')			
			closeBtn = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'mf_txppWframe_wframe2_UTERNAAZ11_UTERNAAZ02_wframe_trigger2')));    time.sleep(0.1);print('인쇄팝업 닫기')
			WebDriverWait(driver, 20).until(EC.invisibility_of_element((By.ID, "mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal")))
			closeBtn.click()  ;    time.sleep(0.1); print('닫기')

		#신고내역조회로 이동합니다	
		driver.find_element(By.ID,'mf_txppWframe_tabControl1_UTERNAAZ11_tab_tabs2_UTERNAAZ11').click();    time.sleep(1);print('신고내역조회 클릭')
		#신고내역조회로 이동합니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1);print('이용중인서비스를 종료하고 신고내역조회로 이동합니다')     
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').clear()
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_input_txprRgtNo_UTERNAAZ31').send_keys(memuser.ssn);time.sleep(0.25);    
		driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_trigger70_UTERNAAZ31').click();print('주민번호로 조회하기')
		#팝업 컨트롤 - 조회결과 있어도 팝업, 업어도 팝업 없는 경우 테이블데이터 없는 것으로 체크
		WebDriverWait(driver, 5).until(EC.alert_is_present()); al = Alert(driver); al.accept(); time.sleep(1)  
		# 테이블 가져오기
		table = driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_body_table')
		tbody = table.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_body_tbody')    
		print(memuser.ceo_name+' 조회결과')  
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			ElecIssue.action_ElecIssue(driver,flag,filename,cols)
			directory = "D:/"
			savefile = directory;fileName="";printBtnName = ""
			if memdeal.biz_manager=='화물' or memdeal.biz_manager[:3]=='종소세': 
				directory += "AAA/종합소득세/" + str(workyear) +"/" + memdeal.biz_manager 
				savefile = directory + "/"+memuser.ceo_name+"("+memuser.ssn[:6]+")-";fileName = memuser.ceo_name+"("+memuser.ssn[:6]+")-"
			else:                                           
				directory += memuser.biz_name+"/" + str(workyear) +"/세무조정계산서"   
				savefile = directory + "/"   

			btnSummitTax = driver.find_element(By.XPATH,'//*[@id="mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_cell_0_12"]/nobr/button')
			if btnSummitTax.is_displayed():#소득세접수증
				savefile_198 =savefile+ "198.pdf";fullFileName = savefile_198;fileName_198= fileName+ "198.pdf";print(fullFileName)
				btnSummitTax.click();time.sleep(3);driver.implicitly_wait(20)
				# 우체국 알람
				# main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]); #time.sleep(30)
				# driver.find_element(By.ID,'trigger4').click() ;driver.switch_to.window(main[0])        

				main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]); 
				if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
				driver.find_element(By.XPATH,'/html/body/div/div/div[1]/table/tbody/tr/td/div/nobr/button[2]').click();time.sleep(4);driver.implicitly_wait(10)
				utils.FileSave_Downloaded_PDF(directory,'',fileName_198,memuser.seq_no);print(memuser.biz_name + '소득세 접수증 저장완료')
				pyautogui.hotkey('alt','f4')
				main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);        
			#소득세납부서
			if wcIncomeTax>0:
				savefile_200 =savefile+ "200.pdf";fullFileName = savefile_200;fileName_200= fileName+ "200.pdf";print(fullFileName)  
				btnVatTax = driver.find_element(By.XPATH,'//*[@id="mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_ttirnam101DVOListDes_cell_0_13"]/nobr/button')
				if btnVatTax.is_displayed():      
					btnVatTax.click();
					WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('지방세도 접수해야합니다')   
					driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_UTERNAAZ68_wframe_ttirnal111DVOListDes_cell_0_3').click();
					driver.implicitly_wait(10);time.sleep(3);print('납부서버튼')
					if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
					main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]); 
					driver.find_element(By.XPATH,'/html/body/div[1]/div/div[1]/table/tbody/tr/td/div/nobr/button[1]').click();time.sleep(3);driver.implicitly_wait(10)
					pyautogui.press('tab',presses=6,interval=0.3);time.sleep(1);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(3)
					utils.FileSave_Downloaded_PDF(directory,'',fileName_200,memuser.seq_no);print(memuser.biz_name + '소득세 납부서 저장완료')
					pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')
					main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]); 
					driver.find_element(By.ID,'mf_txppWframe_genScrn2_UTERNAAZ11_0_wframe2_UTERNAAZ11_1_UTERNAAZ68_wframe_trigger1').click();time.sleep(0.2);print('닫기')
					WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.dismiss();time.sleep(1) ;print('지금 지방세 신고하기 - 취소') 
			#지방세접수증/납부서
			#전자신고파일 작성
			if not utils.is_App_running("Rebirth.exe"):
				print("🔄 Rebirth.exe 실행 중 아님. 실행 시도 중...")
				dig = utils.semusarang_LaunchProgram_App('daeseung6')  
				utils.semusarang_ChangeCompany_ID_App(dig,memuser.duzon_id) 
				app = Application(backend='uia').connect(path="C:\\NewGen\\Rebirth\\Rebirth.exe")
			else:
				app = Application(backend='uia').connect(path="C:\\NewGen\\Rebirth\\Rebirth.exe")
				subprocess.Popen(r'C:/NewGen/Rebirth/Rebirth.exe');  time.sleep(2)
			try:
					dig = app['세무사랑 Pro']
					dig.wait('visible', timeout=10)  # 창 뜰 때까지 대기
			except Exception as e:
					print(f"⚠️ 세무사랑 Pro 창 연결 실패: {e}")
					raise
			utils.semusarang_MenuCode_Popup('3642','개인지방소득세(종합소득)신고서')  
			pyautogui.press('f12');time.sleep(0.5)
			pyautogui.press('y');time.sleep(0.5)
			pyautogui.press('f3');time.sleep(1)
			pyautogui.press('f3');time.sleep(0.5)
			pyautogui.press('esc');time.sleep(0.5)
			utils.semusarang_MenuCode_Popup('3646','지방소득세전자신고')  
			pyautogui.press('enter',presses=3,interval=0.3);
			pyautogui.write(str(memuser.duzon_id));time.sleep(0.5);
			if len(str(memuser.duzon_id))<4: pyautogui.press('enter');time.sleep(0.5)
			pyautogui.write(str(memuser.duzon_id));time.sleep(0.3);pyautogui.press('enter');time.sleep(0.3)
			pyautogui.press('f4');time.sleep(1);pyautogui.press('enter',presses=4,interval=0.3);time.sleep(1)  		
			pyautogui.press('esc',presses=4,interval=0.3);time.sleep(0.5)  
			#위택스 접속
			SS_ElecIssue('income-wetax',memuser.seq_no,workyear,memuser.seq_no,1)	
	elif flag=='income-wetax':
		wcIncomeTax = 0;wcMidTax=0
		record_51C110700=[];
		elecfile = open("c:\\ABC\\"+str(datetime.now())[:10].replace("-","") + ".C110700.01" ,'r') 
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:9] == "51C110700":    
				htxLoginID = line[43:63].replace(' ','')
				if line[9:22].replace(' ','')!=memuser.ssn:pyautogui.prompt('선택된 전자신고파일 : '+line[69:99])  
				record_51C110700.append(line)
			if line[:9] == "52C110713":     #종합소득세 중간예납 레코드
				wcMidTax = int(line[9:22])     #중간예납
			if line[:9] == "53C110700":     #종합소득세 세액의계산 레코드    
				if int(line[261:276])<0 :   wcIncomeTax  = (int(line[203:215])-wcMidTax/10)*-1     
				else:                         wcIncomeTax  =  (int(line[203:215])+wcMidTax/10)     
		elecfile.close() 

		directory = "D:/"
		savefile = directory;fileName="";printBtnName = ""
		if memdeal.biz_manager=='화물' or memdeal.biz_manager[:3]=='종소세': 
			directory += "AAA/종합소득세/" + str(workyear) +"/" + memdeal.biz_manager 
			savefile = directory + "/"+memuser.ceo_name+"("+memuser.ssn[:6]+")-";fileName = memuser.ceo_name+"("+memuser.ssn[:6]+")-"
		else:                                           
			directory += memuser.biz_name+"/" + str(workyear) +"/세무조정계산서"   
			savefile = directory + "/"  

		driver = utils.conWetaxLogin(False);time.sleep(1)
		driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(2); print('전체메뉴')			
		driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[2]/ul/li[1]/a').click();time.sleep(1); print('종합소득분신고 ')	
		driver.find_element(By.ID,'btnFileCfmtnDclr').click();time.sleep(1); print('회계파일신고')	
		acntBtn = driver.find_element(By.XPATH,r'//*[@id="frmUpload"]/div/div/div/div/label').click();  time.sleep(1.5); print('파일첨부');  
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(1);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(1);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		driver.find_element(By.ID,'filePw').send_keys('11111111')
		WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.ID, 'btnNext'))).click();time.sleep(1)
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();print('세무대리인입니다') ;time.sleep(1)
		except:
			print('세무대리인입니다 알람 없음')		
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();print('저장후 다음화면으로 이동') ;time.sleep(2)
		# 테이블 가져오기
		table = driver.find_element(By.ID,'tbl_dclrList')
		tbody = table.find_element(By.XPATH, '//*[@id="tbl_dclrList"]/tbody')   
		print(memuser.ceo_name+' 조회결과')  
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			if cols[2].text[:3]==memuser.ceo_name[:3]:
				wcSangho = cols[2].text  # 이름
				wcDueDate = cols[4].text  # 신고기한
				wcIssueT = cols[5].text  # 납부금액

				driver.find_element(By.ID,"btnSend").click();print("제출버튼");time.sleep(0.5)
				WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();print('신고서를 제출하시겟습니가') ;time.sleep(1)
				# 테이블 가져오기2
				table = driver.find_element(By.ID,'tbl_dclrList')
				tbody = table.find_element(By.XPATH, '//*[@id="tbl_dclrList"]/tbody')   
				print(memuser.ceo_name+' 조회결과')  
				for tr in tbody.find_elements(By.TAG_NAME,'tr'):
					cols = tr.find_elements(By.TAG_NAME,'td')
					if cols[2].text[:3]==memuser.ceo_name[:3]:
						wcSangho = cols[2].text  # 이름
						wcDueDate = cols[4].text  # 신고기한
						wcIssueT = cols[5].text.replace(",","")  # 납부금액
						print('지방세 신고완료');time.sleep(1)

						driver.find_element(By.XPATH,'//*[@id="header"]/div[2]/div/div[3]/a/I').click(); time.sleep(2); print('전체메뉴')	
						linkCorp = driver.find_element(By.XPATH,'//*[@id="contents"]/div[2]/ul[1]/li[7]/ul/li[2]/ul/li[2]/a'); print('종합소득분 신고내역')
						WebDriverWait(driver, 10).until(EC.element_to_be_clickable(linkCorp)).click();time.sleep(4)

						driver.find_element(By.XPATH,'//*[@id="divContents"]/div[1]/button').click();time.sleep(0.3);print('상세검색')
						driver.find_element(By.ID,'inqTxpNm').send_keys(memuser.ceo_name);time.sleep(0.3)
						driver.find_element(By.ID,'btnSearch').click();time.sleep(1)
						print(f"검색결과 :{driver.find_element(By.ID,'spnTotCnt').text}건")
						if driver.find_element(By.ID,'spnTotCnt').text!='0':
							table = driver.find_element(By.ID, 'tblMain')
							tbody = table.find_element(By.XPATH, '//*[@id="tblMain"]/tbody')
							for tr in tbody.find_elements(By.TAG_NAME,'tr'):
								cols = tr.find_elements(By.TAG_NAME,'td')		
								if cols[1].text[:3]==memuser.ceo_name[:3]:
									link1 = cols[1].find_element(By.TAG_NAME, 'a')#납부서
									ActionChains(driver).move_to_element(link1).click().perform();time.sleep(1)

									savefileName199 = fileName + "199.pdf"
									driver.find_element(By.ID,'btnRcptPrint').click();print('지방세접수증 출력');time.sleep(3)#btnRcptPrint 접수증 / btnPrint 신고서
									main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
									pyautogui.press('tab');time.sleep(0.5);		pyautogui.press('enter');time.sleep(0.5);print('지방세접수증')
									pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5)
									utils.FileSave_Downloaded_PDF(directory,'',savefileName199,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
									pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  ;time.sleep(1)
									main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);time.sleep(1)	
									print(f"지방세 납부금액 : {wcIssueT}")
									if int(wcIssueT)>0:
										savefileName201 = fileName + "201.pdf"
										driver.find_element(By.ID,'btnPrint2').click();print('납부서 출력');time.sleep(3)
										main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]);time.sleep(1)
										pyautogui.press('tab');time.sleep(0.5);		pyautogui.press('enter');time.sleep(0.5);print('지방세 납부서')
										pyautogui.press('down');time.sleep(0.5);	pyautogui.press('tab',presses=2,interval=0.5);time.sleep(0.5);	pyautogui.press('enter');time.sleep(0.5)
										utils.FileSave_Downloaded_PDF(directory,'',savefileName201,memuser.seq_no);print(memuser.biz_name +': '+ fileName+' 저장완료')
										pyautogui.hotkey('alt','f4');print('프린트팝업 닫기')  ;time.sleep(1)
										main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);time.sleep(1)	
									break								
						break
				break
	elif flag in ('Kani-Kunro','Kani-Saup','Kani-Ilyoung'):
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:1] == "A":     #A레코드
				htxLoginID = line[21:41].replace(' ','')
		elecfile.close()     
		driver = utils.conHometaxLogin(htxLoginID,False);time.sleep(1)
		driver.get("https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=44&tm2lIdx=4401000000&tm3lIdx=4401110000")
		# 오버레이가 사라질 때까지 기다림
		WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal')));		time.sleep(1);	
	
		if   flag=='Kani-Kunro':   select = Select(driver.find_element(By.ID,'mf_txppWframe_sbmsKnd'));select.select_by_visible_text('간이지급명세서(근로소득)');neededIncase = '간이지급명세서(근로소득)';time.sleep(0.5)
		elif flag=='Kani-Saup': 	 select = Select(driver.find_element(By.ID,'mf_txppWframe_sbmsKnd'));select.select_by_visible_text('간이지급명세서(거주자의 사업소득)');neededIncase = '간이지급명세서(거주자의 사업소득)';time.sleep(0.5)
		elif flag=='Kani-Ilyoung': select = Select(driver.find_element(By.ID,'mf_txppWframe_sbmsKnd'));select.select_by_visible_text('일용근로소득 지급명세서');neededIncase = '일용근로소득 지급명세서';time.sleep(0.5)
		try:
        # 혹시 이전 단계에서 alert가 이미 떠 있는 경우 먼저 처리
			WebDriverWait(driver, 2).until(EC.alert_is_present())
			alert = Alert(driver)
			print(f"사전 Alert 발생: {alert.text}")
			alert.accept()
			time.sleep(1)
		except TimeoutException:
			pass  # Alert 없으면 넘어감

		try:
			# 파일선택 버튼 클릭 시도
			driver.find_element(By.ID, 'mf_txppWframe_btnFleChce').click()
			time.sleep(1)
			print('파일선택 클릭 완료')

			# 클릭 후 Alert가 다시 뜨는 경우 처리
			WebDriverWait(driver, 2).until(EC.alert_is_present())
			alert = Alert(driver)
			print(f"클릭 후 Alert 발생: {alert.text}")
			alert.accept()
			time.sleep(1)
			alert.accept()
			time.sleep(1)
			# 재시도
			driver.find_element(By.ID, 'mf_txppWframe_btnFleChce').click()
			print("파일선택 재시도")
		except UnexpectedAlertPresentException:
			print("예상치 못한 알림창으로 실패했습니다. 다시 시도하세요.")
		except Exception as e:
			print(f"파일 버튼 클릭 중 예외 발생: {e}") 
		main = driver.window_handles;        print(main);        driver.switch_to.window(main[1]) 
		driver.find_element(By.ID,'mf_btnFind').click();    time.sleep(1);print('찾아보기')#다시한번 찾아보기 클릭 -> 파일선택창
		menuName='열기'
		intlen = len(menuName)
		procs = pywinauto.findwindows.find_elements();handle=''
		for proc in procs: 
			print(proc.name)
			if proc.name[:intlen]== menuName:handle = proc.handle;break
		app = Application().connect(handle=handle)
		w_open = app.window(handle=handle)
		w_open.set_focus()        
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(0.5);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(0.5);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)
		pyautogui.press('esc',presses=3,interval=0.25)#잘못된 팝업 털기
		driver.find_element(By.ID,'mf_btnUpload').click();    time.sleep(1);print('업로드하면 바로 닫힌다')

		main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);   
		driver.find_element(By.ID,'mf_txppWframe_btnFleVrf').click();    time.sleep(1);print('파일검증 시작하기')
		try:
			button = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="mf_txppWframe_chkConfirm"]/li/label'))); 
			button.click();time.sleep(1);print('체크박스 : 위 내용을 확인하고 제출합니다.') 
		except:
			print(f'{memuser.biz_name} : 전자파일 오류존재')
			return 0

		try:
			driver.find_element(By.ID,'mf_txppWframe_btnErrExclSbms').click();    time.sleep(1);print('제출하기');time.sleep(1)
		except UnexpectedAlertPresentException:
			# alert 팝업이 예상하지 않은 시점에 나타났을 때 처리할 코드 작성
			try:
				WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)  
			except TimeoutException:     
				driver.find_element(By.ID,'mf_txppWframe_group2806').click();    time.sleep(1);print('전자파일 제출하기');time.sleep(1) 
		#가장 나중것이 제출됩니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)    
		#제출이 완료되었습니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)    
  
		driver.find_element(By.ID,'mf_txppWframe_dsdTfrInqr').click();print('제출내역 조회');time.sleep(0.5)   
		driver.find_element(By.ID,'mf_txppWframe_srchTin_UWEICAAD16').clear();driver.find_element(By.ID,'mf_txppWframe_srchTin_UWEICAAD16').send_keys(memuser.biz_no.replace("-",""));time.sleep(0.25)
		if   flag=='Kani-Kunro':   select = Select(driver.find_element(By.ID,'mf_txppWframe_mateKndCd_UWEICAAD16'));select.select_by_visible_text('간이지급명세서(근로소득)');neededIncase = '간이지급명세서(근로소득)';time.sleep(0.5)
		elif flag=='Kani-Saup': 	 select = Select(driver.find_element(By.ID,'mf_txppWframe_mateKndCd_UWEICAAD16'));select.select_by_visible_text('간이지급명세서(거주자의 사업소득)');neededIncase = '간이지급명세서(거주자의 사업소득)';time.sleep(0.5)
		elif flag=='Kani-Ilyoung': select = Select(driver.find_element(By.ID,'mf_txppWframe_mateKndCd_UWEICAAD16'));select.select_by_visible_text('일용근로소득 지급명세서');neededIncase = '일용근로소득 지급명세서';time.sleep(0.5)
		driver.find_element(By.ID,'mf_txppWframe_btnSearch_UWEICAAD16').click()  ;    time.sleep(0.5); print('조회하기')
		
		table = driver.find_element(By.ID,'mf_txppWframe_gridList01_UWEICAAD16_body_table')
		tbody = table.find_element(By.ID,'mf_txppWframe_gridList01_UWEICAAD16_body_tbody')    
		print(memuser.biz_no+' 조회결과')
		print(len(tbody.find_elements(By.TAG_NAME,'tr')))
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			print('cols[6].text[:12]:'+cols[6].text[:12])
			if cols[6].text[:12]==memuser.biz_no :       
				driver.find_element(By.ID,'mf_txppWframe_textbox4105').click()  ;    time.sleep(1.5); print('목록 내려받기') 
				# elecResult_Save.ElecIssue.action_Kani(htxLoginID,filename,cols)
				isOK = utils.DBSave_Downloaded_xlsx(driver,[cols[8].text[:7],neededIncase,memuser.biz_no],'간이지급명세서') 
				if isOK: driver.quit();print('정상종료')
				break
		if  os.path.isfile(file_name.replace('/',"\\")):os.remove(file_name.replace('/',"\\"));print(file_name+" 삭제완료")
	elif flag in ('ZZMS-Kunro','ZZMS-Toijik','ZZMS-Saup','ZZMS-Kita','ZZMS-50','ZZMS-60'):
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:1] == "A":     #A레코드
				if flag in ('ZZMS-50','ZZMS-60'):		htxLoginID = line[80:100].replace(' ','');print(f"htxLoginID:{htxLoginID}")
				else:																htxLoginID = line[21:41].replace(' ','');print(f"htxLoginID:{htxLoginID}")
		elecfile.close()   		
		driver = utils.conHometaxLogin(htxLoginID,False);time.sleep(1)
		# Wait for the modal to disappear
		WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'mf_wq_uuid_24_mf_wq_uuid_24_wq_proessMsgModal')))
		WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'mf_wfHeader_hdGroup005'))).click();time.sleep(0.1);print('전체메뉴')  
		if flag=='ZZMS-Kunro':	
			driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('근로 사업 퇴직 근로소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)
		elif flag=='ZZMS-Toijik' : 
			driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('근로 사업 퇴직소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)			
		elif flag=='ZZMS-Saup' :	
			driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('사업 기타소득 종교인소득 사업소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)					
		elif flag=='ZZMS-Kita':	
			driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('사업 기타소득 종교인소득 기타소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)					
			pyautogui.press('tab',presses=2,interval=0.3)	
		elif flag=='ZZMS-50':		driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('이자배당소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)					
		elif flag=='ZZMS-60':		driver.find_element(By.ID,'mf_wfHeader_UTXPPBAD22_wframe_input1').send_keys('이자배당소득지급명세서제출/내역 조회');pyautogui.press('enter');time.sleep(1.5)					
		pyautogui.press('tab',presses=2,interval=0.3);pyautogui.press('enter');time.sleep(1);		
		filetransferID = "mf_txppWframe_anchor2"
		if flag=='ZZMS-Kita':filetransferID = "mf_txppWframe_anchor345"
		driver.find_element(By.ID,filetransferID).click();    time.sleep(2);print('파일변환방식')
		driver.find_element(By.ID,'mf_txppWframe_wframe4_trigger116').click();    time.sleep(1);print('찾아보기')
		try:
			print(' 진행중인 파일이 있음')
			WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)
			pyautogui.press('esc');time.sleep(1)
			driver.find_element(By.ID,'mf_txppWframe_wframe4_trigger116').click();    time.sleep(1);print('찾아보기')
			WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)
		except:
			print('정상진행')		
		menuName='열기'
		intlen = len(menuName)
		procs = pywinauto.findwindows.find_elements();handle=''
		for proc in procs: 
			print(proc.name)
			if proc.name[:intlen]== menuName:handle = proc.handle;break
		app = Application().connect(handle=handle)
		w_open = app.window(handle=handle)
		w_open.set_focus()        
		pyautogui.hotkey('alt','d');print('c:\ABC 선택');time.sleep(0.5);pyperclip.copy(path); pyautogui.hotkey('ctrl', 'v');#'c:\ABC'
		pyautogui.press('enter');time.sleep(0.5);pyautogui.press('tab',presses=3,interval=0.25)
		pyautogui.hotkey('alt','n');print('전자신고파일선택');time.sleep(0.5);pyautogui.write(file_name);time.sleep(0.5);pyautogui.hotkey('alt','o'); time.sleep(2)		
		driver.find_element(By.ID,'mf_txppWframe_wframe4_group2759').click();    time.sleep(1);print('형식검증하기');time.sleep(5)
		driver.find_element(By.ID,'mf_txppWframe_wframe4_group2826').click();    time.sleep(1);print('형식검증결과확인');time.sleep(1)
		driver.find_element(By.ID,'mf_txppWframe_wframe4_group2763').click();    time.sleep(1);print('내용검증하기');time.sleep(3)
		try:
			driver.find_element(By.ID,'mf_txppWframe_wframe4_group2828').click();    time.sleep(1);print('내용검증결과확인');time.sleep(1)
		except:
			return ''
		driver.find_element(By.ID,'mf_txppWframe_wframe4_group2828').click();    time.sleep(1);print('내용검증결과확인');time.sleep(2)
		try:
			driver.find_element(By.ID,'mf_txppWframe_wframe4_group2764').click();    time.sleep(1);print('전자파일제출');time.sleep(2)
		except:
			print(f'{memuser.biz_name} : 전자신고시 내용검증오류 있음')
			return 0
		try:
			driver.find_element(By.ID,'mf_txppWframe_wframe4_trigger105').click();    time.sleep(1);print('전자파일 제출하기');time.sleep(1)
		except UnexpectedAlertPresentException:
			# alert 팝업이 예상하지 않은 시점에 나타났을 때 처리할 코드 작성
			try:
				WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)  
			except TimeoutException:  
				try: 	
					driver.find_element(By.ID,'mf_txppWframe_wframe4_trigger105').click();    time.sleep(1);print('전자파일 제출하기');time.sleep(1) 
				except:
					print(f'{memuser.biz_name} : 전자신고시 내용검증오류 있음')
					return '에러발생'
		#정상변환된 신고서를 제출합니다
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)    
		#신고서를 제출합니다
		try:
			WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)
		except:
			print('알람없음')    

		if flag=='ZZMS-Kita':	driver.find_element(By.ID,'mf_txppWframe_wframe4_txtnMateTfrPopup_wframe_trigger2').click(); 	   time.sleep(1); print('닫기')
		elif flag=='ZZMS-Toijik' or  flag=='ZZMS-Saup'  : driver.find_element(By.ID,'mf_txppWframe_wframe4_txtnMateTfrPopup_wframe_trigger14').click();  time.sleep(1); print('닫기')
		elif flag in ('ZZMS-50','ZZMS-60'): driver.find_element(By.ID,'mf_txppWframe_wframe4_group1499').click(); 	   time.sleep(1); print('닫기')
		else								:	driver.find_element(By.ID,'mf_txppWframe_wframe4_txtnMateTfrPopup_wframe_trigger2').click();  time.sleep(1); print('닫기')

		arrBizno = memuser.biz_no.split("-")
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno1').clear();time.sleep(0.5)
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno1').send_keys(arrBizno[0]);time.sleep(0.25);    
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno2').clear();time.sleep(0.5)
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno2').send_keys(arrBizno[1]);time.sleep(0.25);          
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno3').clear();time.sleep(0.5)
		driver.find_element(By.ID,'mf_txppWframe_wframe5_bmanBsno3').send_keys(arrBizno[2]);time.sleep(0.5);          
		driver.find_element(By.ID,'mf_txppWframe_wframe5_group1212_UTESFAAA08').click();print(memuser.biz_no+' 사업자번호로 조회 : 조회하기버튼');time.sleep

		# 테이블 가져오기 방식
		table = driver.find_element(By.ID,'mf_txppWframe_wframe5_grdSbmsBrkd_body_table')
		tbody = table.find_element(By.ID,'mf_txppWframe_wframe5_grdSbmsBrkd_body_tbody')    
		print(memuser.biz_no+' 조회결과')
		print(len(tbody.find_elements(By.TAG_NAME,'tr')))
		for tr in tbody.find_elements(By.TAG_NAME,'tr'):
			cols = tr.find_elements(By.TAG_NAME,'td')
			cols[0] = htxLoginID
			ElecIssue.action_ElecIssue(driver,flag,filename,cols)
			break
		driver.quit();print('정상종료')

		# 엑셀 내려받기 방식
		# driver.find_element(By.ID,'group2613_UTESFAAA08').click();print(memuser.biz_no+' 목록내려받기');time.sleep(1)
		# isOK = utils.DBSave_Downloaded_xlsx(driver,[cols[8].text[:7],neededIncase,memuser.biz_no],'지급조서') 
		# if isOK: driver.quit();print('정상종료')
	return 1

def semusarang_MakeAccount_Insa_AA(flag,biz_no,biz_type,workyy,text_mm):
	whiteBtn = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_CheckAll_white.png'
	blueBtn = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_CheckAll.png'
	deCheck = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_DeCheckAll.png'
	accDateA30 = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_AccDate_A30.png'
	accDateA20 = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_AccDate_A20.png'
	accDateA60 = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_AccDate_A60.png'
	NoData = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_NoData.png'
	NoDataA01 = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_NoDataA01.png'
	if flag=='a01':
		utils.semusarang_Menu_Popup('급여자료회계처리');time.sleep(1)
		pyautogui.press('enter');time.sleep(0.4);pyautogui.press('enter');time.sleep(0.4);pyautogui.write('1');time.sleep(0.4);pyautogui.write('0');time.sleep(0.5)
		noDataXY = pyautogui.locateCenterOnScreen(NoDataA01,confidence=0.7)
		if noDataXY: pyautogui.press('enter');pyautogui.press('esc')
		else:    
			if int(text_mm)>1:
				whiteXY = pyautogui.locateCenterOnScreen(whiteBtn,confidence=0.7)
				if whiteXY: pyautogui.click(whiteXY); print('white btn exist')
			else:
				blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
				if blueXY: pyautogui.click(blueXY);print('blue btn exist')
			pyautogui.press('f6');time.sleep(1);print('전표삭제');pyautogui.press('enter',presses=2,interval=0.3);time.sleep(0.25)
			pyautogui.press('esc',presses=4,interval=0.25)
		utils.semusarang_Menu_Popup('급여자료회계처리');time.sleep(1)
		pyautogui.press('enter');time.sleep(0.4);pyautogui.press('enter');time.sleep(0.4);pyautogui.write('2');time.sleep(0.4);pyautogui.write('0');time.sleep(0.5)
		pyautogui.press('f12');time.sleep(1);print('새로불러오기');pyautogui.press('enter');time.sleep(int(text_mm)*0.5+1) 
		if int(text_mm)>1:
			whiteXY = pyautogui.locateCenterOnScreen(whiteBtn,confidence=0.7);
			if whiteXY: pyautogui.click(whiteXY); print('white btn exist')
		else:
			blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
			if blueXY: pyautogui.click(blueXY);print('blue btn exist')    
		# pyautogui.press('left');time.sleep(0.25);print('체크박스로이동');pyautogui.press('space');time.sleep(0.25);print('체크박스 선택')
		pyautogui.press('f7');time.sleep(1);print('분개설정'); pyautogui.write('1');time.sleep(0.35);print('전표발생일-귀속월의 말일')
		pyautogui.press('tab');time.sleep(0.4);pyautogui.press('enter');time.sleep(2);print('설정반영 - 2초이상 소요') 
		pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(0.25);print('전표추가 - 예')
		pyautogui.press('esc',presses=4,interval=0.25)
	elif flag=='a03':    
		strsql = " select right(과세연월,2), a03 from 원천세전자신고 where 사업자등록번호='"+biz_no+"' and left(과세연월,4)="+workyy+" and a03>0 order by 과세연월"
		cursor = connection.cursor()
		cursor.execute(strsql);print(strsql)
		results = cursor.fetchall()
		connection.commit()
		connection.close()    
		for result in results:       
			utils.semusarang_Menu_Popup('일용직급여자료회계처리');time.sleep(1)
			pyautogui.press('enter');pyautogui.write(result[0]);time.sleep(0.25);pyautogui.write(result[0]);time.sleep(0.25);pyautogui.press('enter');time.sleep(0.5)
			blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
			if blueXY:              
				pyautogui.click(pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7));    time.sleep(1); print('bluebtn 클릭')
				pyautogui.press('f6');time.sleep(1);print('전표삭제');pyautogui.press('enter');time.sleep(int(text_mm)*0.5)
				if blueXY:  pyautogui.click(blueXY);    time.sleep(1); print('bluebtn 클릭')
				pyautogui.press('f8');time.sleep(1);print('기본계정설정'); 
				pyautogui.write('805');pyautogui.press('enter',presses=5,interval=0.3);
				if biz_type>3:pyautogui.write('101');pyautogui.press('enter')
				else          :pyautogui.write('103');pyautogui.press('enter')
				pyautogui.press('tab');time.sleep(0.4)
				pyautogui.press('f12');time.sleep(1);print('새로불러오기');pyautogui.press('enter');time.sleep(int(text_mm)*0.5);pyautogui.write(workyy+result[0]+'25')
				if blueXY:  pyautogui.click(blueXY);    time.sleep(1); print('bluebtn 클릭')
				pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(int(text_mm)*0.5);print('전표추가 - 예')    
			pyautogui.press('esc',presses=4,interval=0.25)    
	elif  flag=='a60' or flag=='a50' or flag=='a40' or flag=='a30' or flag=='a20':   
		txtflag = ''
		if flag=='a20':txtflag = '퇴직소득자료회계처리'
		elif flag=='a30':txtflag = '사업소득자료회계처리'
		elif flag=='a60' or flag=='a50' or flag=='a40':txtflag = '기타이자배당소득자료회계처리'
		if flag=='a60':
			confirm = pyautogui.confirm('배당소득 회계처리 관련 조치하고 확인 누르세요. 취소누르면 다음 프로세스로 이동')
			if confirm=='Cancel':return False   #중단 
		utils.semusarang_Menu_Popup(txtflag);time.sleep(1)
		pyautogui.press('enter',presses=3,interval=0.2)
		if flag=='a40':pyautogui.write('1');time.sleep(0.25);print('기타소득 선택')
		elif flag=='a60' or flag=='a50':pyautogui.write('2');time.sleep(0.25);print('이자배당소득 선택')
		pyautogui.write('1');time.sleep(0.25);print('전표발행 선택')
		noDataXY = pyautogui.locateCenterOnScreen(NoData,confidence=0.6)
		if noDataXY: pyautogui.press('enter');pyautogui.press('esc')
		else:
			blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7) 
			if blueXY: 
				pyautogui.click(blueXY);print('blue btn exist') ;    time.sleep(0.3) 
				pyautogui.press('f6');time.sleep(0.25);print('전표삭제');pyautogui.press('enter');time.sleep(0.25);print('전표삭제 - 예');pyautogui.press('esc');time.sleep(0.25)
			pyautogui.press('esc',presses=4,interval=0.25)
		utils.semusarang_Menu_Popup(txtflag);time.sleep(1)
		pyautogui.press('enter',presses=3,interval=0.2)
		if flag=='a40':pyautogui.write('1');time.sleep(0.25);print('기타소득 선택')
		elif flag=='a60' or flag=='a50':pyautogui.write('2');time.sleep(0.25);print('이자배당소득 선택')
		pyautogui.write('2');time.sleep(0.25);print('전표미발행 선택')
		blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
		if flag=='a60' or flag=='a50':
			pyautogui.click(blueXY);time.sleep(0.3);
			pyautogui.press('f7');time.sleep(0.3);print('전표설정')
			if flag=='a50':
				pyautogui.write('951');pyautogui.press('enter',presses=2,interval=0.2)
				if biz_type>3:pyautogui.write('101')
				else          :pyautogui.write('103')
			elif flag=='a60':pyautogui.write('377');pyautogui.press('enter',presses=2,interval=0.2);pyautogui.write('265')
			pyautogui.press('enter');pyautogui.press('tab')
		accDateXY =  None
		if flag=='a30':accDateXY = pyautogui.locateCenterOnScreen(accDateA30)
		elif  flag=='a20':accDateXY = pyautogui.locateCenterOnScreen(accDateA20)
		elif flag=='a60' or flag=='a50' or flag=='a40':accDateXY = pyautogui.locateCenterOnScreen(accDateA60)
		if accDateXY: pyautogui.click(accDateXY);time.sleep(0.9);print('Accnt Date checked')
		if blueXY: 
			pyautogui.click(blueXY);print('blue btn exist') ;    time.sleep(0.3) 
			pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(0.25);print('전표추가 - 예')
		pyautogui.press('esc',presses=4,interval=0.25)
	return 1


def semusarang_Menu_Corptax(menuName,fileName,workyear,directory):
	isProceed = True
	utils.semusarang_Menu_Popup(menuName)

	if fileName=='101.pdf' or fileName=='102.pdf':
		print('회계 - 재무제표:'+fileName)    
		pyautogui.press('enter');time.sleep(0.25)
	elif fileName=='104.pdf':
		pyautogui.press('enter');time.sleep(0.25);print('3-4와 중복메뉴이니 첫 메뉴 선택')
		semusarang_IsSaved = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_IsSaved.png',confidence=0.6)
		if semusarang_IsSaved:
			pyautogui.click(semusarang_IsSaved)
			pyautogui.press('right');time.sleep(0.25);pyautogui.press('enter');    time.sleep(0.5)
		# pyautogui.press('enter');time.sleep(0.25);
		# pyautogui.press('f12'); time.sleep(0.25);pyautogui.press('right');time.sleep(0.25);pyautogui.press('enter');    time.sleep(0.5); print('아니오 선택')#pyautogui.press('enter');time.sleep(0.25)
		print('주총결의일 설정')
		# pyautogui.press('left');    time.sleep(0.25); print('아니오 선택')
		pyautogui.write(str(workyear+1));    time.sleep(0.5)  
		pyautogui.write('03');    time.sleep(0.5);   
		pyautogui.write('27');    time.sleep(0.5)      
		pyautogui.press('f6');   time.sleep(0.25);  print('전표추가')
		pyautogui.press('enter',presses=2, interval=0.5)
	elif fileName=='105.pdf':
		pyautogui.press('enter',presses=2,interval=0.3)
		time.sleep(2)    #필수
	elif fileName=='3-1.pdf' or fileName=='40-6.pdf':
		pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
		pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('Y');time.sleep(0.5);print('예 버튼')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')
	elif fileName=='3-4.pdf':
		pyautogui.press('down');time.sleep(0.25);print('3-4.pdf인 경우 중복메뉴이니 아래 메뉴 선택')
		pyautogui.press('enter');time.sleep(2) #필수  
		pyautogui.press('f12');time.sleep(1);pyautogui.press('enter');print('불러오기')
		pyautogui.press('f12');time.sleep(1);pyautogui.press('enter');print('불러오기')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')    
	elif fileName=='10-갑.pdf':
		pyautogui.press('f12');time.sleep(0.25);pyautogui.press('tab');pyautogui.press('enter');time.sleep(1) #필수  
		confirm = pyautogui.confirm('조정사항 입력하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;os._exit()#return False   #중단 
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요') 
	elif fileName=='6-11.pdf' or  fileName=='67.pdf' :
		pyautogui.press('f12');time.sleep(0.5);print('불러오기')
		pyautogui.press('enter',presses=5,interval=0.2);time.sleep(0.5);pyautogui.press('tab')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')
	elif fileName=='16.pdf' or  fileName=='52-1.pdf' :
		pyautogui.hotkey('ctrl','f5');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5);
		pyautogui.press('1');time.sleep(0.5);print('매출선택')
		pyautogui.press('f4');time.sleep(0.5);pyautogui.press('tab');print('매출조회')
		pyautogui.press('f11');time.sleep(3);print('저장하기 2초 소요')    
	elif fileName=='17.pdf' or  fileName=='52-2.pdf' :
		pyautogui.press('f12');time.sleep(0.5);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('불러오기');print('예')
		pyautogui.hotkey('ctrl','2');time.sleep(0.5);print('부가세신고차이확인')
		confirm = pyautogui.confirm('부가세 신고서와 차이 있는 경우 조정입력하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;return False   #중단      
		pyautogui.press('f11');time.sleep(3);print('저장하기 2초 소요')    
	elif fileName=='23-갑.pdf' or fileName=='55.pdf':
		pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('접대비 조회')
		confirm = pyautogui.confirm('접대비 한도초과나 즉시부인 금액이 없거나, 부인액이 있는 경우 조정사항 입력하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;return False   #중단  
		pyautogui.press('f11');time.sleep(3);print('저장하기 2초 소요')     
	elif fileName=='34.pdf':
		confirm = pyautogui.confirm('대손충당금조정명세서를 작성하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;return False   #
	elif fileName=='19-갑.pdf':
		confirm = pyautogui.confirm('가지급금조정명세서를 작성하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) ')
		if confirm=='Cancel':isProceed = False;return False   #중단  
		pyautogui.hotkey('ctrl','3');time.sleep(0.25);print('19-을 출력준비')   
		utils.semusarang_Print('19-을',directory);time.sleep(0.5)
		pyautogui.hotkey('ctrl','4');time.sleep(0.25);print('19-갑 출력준비')  
	elif  fileName=='39.pdf':
		confirm = pyautogui.confirm('['+fileName+'] 해당 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;return False   #중단          
	elif fileName=='47-을.pdf':
		pyautogui.hotkey('ctrl','2');time.sleep(0.3);pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')
	elif fileName=='85.pdf':
		pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
		pyautogui.hotkey('ctrl','2');time.sleep(0.5);pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
		pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
		confirm = pyautogui.confirm('23.차이를 조정한 후 해당 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
		if confirm=='Cancel':isProceed = False;return False   #중단  
		pyautogui.press('f6');time.sleep(5);print('저장')   
	elif fileName=='92-지-43-5-갑.pdf':
		# pyautogui.keyDown('ctrl');pyautogui.press('f12')  ;pyautogui.keyUp('ctrl');
		pyautogui.hotkey('ctrl','f12') 
		# semusarang_CTRL_F12 =  pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_CTRL_F12.png')
		# if semusarang_CTRL_F12:  pyautogui.click(semusarang_CTRL_F12);     
		time.sleep(0.5);pyautogui.press('enter');print('조회')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')   
	else:
		# 47-갑  #92-지-43-2  #92-지-43-2
		pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
		pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')
		print('세무:'+menuName)
		isProceed = True
	if isProceed:utils.semusarang_Print(fileName,directory)
	return isProceed


#마감이월후 마감취소
def semusarang_MagamEwall(flag):
  pyautogui.hotkey('ctrl', 'enter');pyperclip.copy('마감후이월')    #메뉴검색
  pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter')
  time.sleep(0.5)
  if flag=='vat':
    pyautogui.press('enter');print('회계인경우 첫번째 마감메뉴 선택');time.sleep(1)
    pyautogui.press('f6');time.sleep(1);pyautogui.press('enter')
    time.sleep(5);pyautogui.press('enter')
    #pyautogui.press('f11');pyautogui.press('enter');print('마감해제')
  elif flag=='insa':
    pyautogui.press('down');time.sleep(0.25)
    pyautogui.press('enter');print('인사인경우 두번째 마감메뉴 선택');time.sleep(1.5)
    pyautogui.press('f4');time.sleep(1.5);pyautogui.press('enter',presses=2,interval=0.5)
  pyautogui.press('esc',presses=2,interval=0.5)
  return 1

#부가가치세 신고서 작성
def SS_VatSingoMagam(directory,mmStart,mmEnd,seq_no,isJungKi,kawasekisu,workPd):
	memuser = MemUser.objects.get(seq_no=seq_no)
	if memuser.biz_type==5:	utils.semusarang_Menu_Popup('부가가치세신고서(간이과세자)')
	else:										utils.semusarang_Menu_Popup('부가가치세신고서')
	print(f'시작월:{mmStart}월');pyautogui.write(mmStart);time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5);
	if len(mmStart)!=2: print('시작일(엔터)');pyautogui.press('enter');time.sleep(0.5);
	print(f'종료월:{mmEnd}월');pyautogui.write(mmEnd);time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
	print('신고구분:정기');pyautogui.press('enter');time.sleep(0.5);
	location = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_SaveDataCall.png', confidence=0.5)
	if location:      pyautogui.press('N');time.sleep(0.5);print('기존에 저장된 데이터를 불러오겠습니까 : 아니오')
	else:             pyautogui.press('enter');time.sleep(0.5)
	if (memuser.uptae[:1]=='음' or memuser.uptae[:1]=='숙'):
		print('음식점인 경우 사업장명세를 만든다')
		pyautogui.press('F8');print('사업장명세');time.sleep(0.3);pyautogui.press('2');time.sleep(0.3);pyautogui.press('tab');time.sleep(0.3)
	if isJungKi==4:#기한후신고인 경우
		pyautogui.press('f4');time.sleep(0.3);pyautogui.write(str(isJungKi));time.sleep(0.3);pyautogui.press('tab');time.sleep(0.5);print('기한후신고')
	strsel = f"select 예정미환급세액일반,예정고지세액일반 from 부가가치세통합조회 where 사업자등록번호='{memuser.biz_no}' and 과세기수='{kawasekisu}' and 신고구분='{workPd}'";print(strsel)   
	cursor = connection.cursor()   
	cursor.execute(strsel)
	rstong = cursor.fetchone()
	connection.commit()
	mewhan = prepay = 0
	if rstong:
		mewhan = rstong[0]
		prepay = rstong[1]
		if mewhan>0:				pyautogui.press('down',presses=16,interval=0.3);pyautogui.write(str(mewhan))
		elif prepay>0:			pyautogui.press('down',presses=17,interval=0.3);pyautogui.write(str(prepay))
	pyautogui.press('f3');time.sleep(0.5);pyautogui.press('esc');time.sleep(0.5);pyautogui.press('f3');time.sleep(0.5);print('  부가세 신고서  마감 ')
	
	locationMagamCare = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamCare.png', confidence=0.8) #마감오류 전체
	if locationMagamCare:pyautogui.press('f3');time.sleep(0.5);

	locationTIGongje = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamError_TIGongje.png', confidence=0.8)   
	# locationBuilding = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamError_Building.png', confidence=0.8) 
	# locationRefundF6 = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamError_RefundF6.png', confidence=0.8) #F6환급구분이누락되었습니다.
	if locationTIGongje:    pyautogui.press('f3');time.sleep(0.5);print('개인사업자 3억미만 전자신고세액공제 유의사항 => 공제받지 않고 강제마감') 
	# if locationBuilding:  # 건물등 감가상각자산 명세서 작성
	# 	pyautogui.press('esc',presses=5,interval=0.3)
	# 	VAT.SS_TI_TangibleAsset(directory,mmStart,mmEnd)
	# 	SS_VatSingoMagam(directory,mmStart,mmEnd,seq_no,isJungKi)  
	# if locationRefundF6:  # 환급명세서
	# 	pyautogui.press('esc',presses=2,interval=0.8)
	# 	pyautogui.press('f6');time.sleep(0.5)
	# 	radioF6 = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamError_RefundF6_Radio.png', confidence=0.6) 
	# 	if radioF6:
	# 		radioF6.click();time.sleep(0.5)
	# 		pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_Btn_Tab.png', confidence=0.6).click();time.sleep(0.5)
	# 	SS_VatSingoMagam(directory,mmStart,mmEnd,seq_no,isJungKi,kawasekisu,workPd)     
	time.sleep(1)   
	menuName='부가가치세신고서'
	intlen = len(menuName)
	procs = pywinauto.findwindows.find_elements();handle=''
	for proc in procs: 
		if proc.name[:intlen]== menuName:handle = proc.handle;break
	app = Application().connect(handle=handle)
	w_open = app.window(handle=handle)
	w_open.set_focus()      

	utils.semusarang_Print('0.pdf',directory) 
	return 1


class VAT:
	def SS_excelupload_Card(fileName,flag):
		utils.semusarang_Menu_Popup('신용카드매입매출전표전송')
		if flag=='매출':    pyautogui.press('f4');print('매출자료올리기')
		elif flag=='매입':  pyautogui.press('f3');print('매입자료올리기')
		pyautogui.hotkey('alt','d');print('alt + d');time.sleep(0.5);pyperclip.copy(fileName); pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter');time.sleep(5);print(fileName+' 업로드 버튼')
		pyautogui.press('tab');time.sleep(1.5);
		whiteBtn = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_CardSale_CheckAll.png'
		if pyautogui.locateCenterOnScreen(whiteBtn,confidence=0.7):  
			pyautogui.click(pyautogui.locateCenterOnScreen(whiteBtn,confidence=0.7));    time.sleep(1); print('whitebtn 클릭')
			time.sleep(1)
			pyautogui.press('f6');time.sleep(0.5);print('전표처리');
			pyautogui.press('enter',presses=2,interval=1);time.sleep(1);
			pyautogui.press('esc',presses=3,interval=1);time.sleep(1);
			return 1    
		else: 
			print('whitebtn 없음');  
			return 0
		# confirm = pyautogui.confirm('전표처리할 데이터를 체크("V")하고 확인을 클릭하세요.[취소] 중단')
		# if confirm=='OK':
			
	def SS_excelupload_Cash(fileName,flag):
		utils.semusarang_Menu_Popup('기타매입매출전표전송')
		if flag=='매출':    pyautogui.press('f4');print('매출자료올리기')
		elif flag=='매입':  pyautogui.press('f3');print('매입자료올리기')
		pyautogui.hotkey('alt','d');print('alt + d');time.sleep(0.5);pyperclip.copy(fileName); pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter');time.sleep(3);print(fileName+' 업로드 버튼')
		pyautogui.press('tab');time.sleep(1.5);pyautogui.press('f6');time.sleep(0.5);print('전표처리');
		pyautogui.press('enter',presses=2,interval=1);time.sleep(1);
		pyautogui.press('esc',presses=3,interval=1);time.sleep(1);
		return 1

	# 세무사랑 전자세금계산서 스크래핑 데이터 업로드
	def SS_excelupload_TI(fileName,seq_no,flag):
		utils.semusarang_Menu_Popup('기타매입매출전표전송')
		if flag=='매출':    pyautogui.press('f4');print('매출자료올리기')
		elif flag=='매입':  pyautogui.press('f3');print('매입자료올리기')
		pyautogui.hotkey('alt','d');print('alt + d');time.sleep(0.5);pyperclip.copy(fileName); pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter');time.sleep(3);print(fileName+' 업로드 버튼');pyautogui.press('tab');time.sleep(1.5);
		if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_hasNoCheckedData.png', confidence=0.6):
			pyautogui.press('enter');time.sleep(0.2)
		else:
			pyautogui.press('f6');time.sleep(0.5);print('전표처리');
			pyautogui.press('enter',presses=2,interval=1);time.sleep(1);
		pyautogui.press('esc',presses=3,interval=1);time.sleep(1);
		return 1
	def SS_TI_TangibleAsset(directory,mmStart,mmEnd):
		utils.semusarang_Menu_Popup('건물등감가상각자산취득명세서')
		pyautogui.write(str(mmStart));
		if len(mmStart)!=2:pyautogui.press('enter');
		time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter',presses=2,interval=0.5);time.sleep(1.5)
		pyautogui.press('f4');time.sleep(0.5);pyautogui.press('tab');pyautogui.press('enter');time.sleep(0.5);time.sleep(1.5);pyautogui.press('f11');time.sleep(1.5);print('저장');pyautogui.press('enter');time.sleep(0.5)
		utils.semusarang_Print('11.pdf',directory) ;pyautogui.press('esc');time.sleep(0.5)
		return 1 
	def SS_TI_Bullgong(directory,mmStart,mmEnd):
		utils.semusarang_Menu_Popup('공제받지못할매입세액명세서')
		pyautogui.write(str(mmStart));pyautogui.press('enter');time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter',presses=2,interval=0.5);time.sleep(1.5)
		pyautogui.press('f11');time.sleep(1.5);print('저장')
		utils.semusarang_Print('10.pdf',directory) 
		return 1
	def SS_TI_Summation(directory,mmStart,mmEnd,trd_1,trd_2):
		if trd_1 or trd_2:
			utils.semusarang_Menu_Popup('세금계산서합계표')
			pyautogui.write(str(mmStart));pyautogui.press('enter');time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter',presses=3,interval=0.5);time.sleep(1.5)
			pyautogui.press('f7');time.sleep(1.5);
		if trd_1==True and trd_2==True:    
			utils.semusarang_Print_TI_Summary('1.pdf',directory)
			utils.semusarang_Print_TI_Summary('2.pdf',directory)  
		elif trd_1==True and trd_2==False:    
			utils.semusarang_Print_TI_Summary('1.pdf',directory) 
		elif trd_1==False and trd_2==True:
			utils.semusarang_Print_TI_Summary('2.pdf',directory) 
		pyautogui.press('esc',presses=4,interval=0.25);print('열린 세무사랑 하부메뉴 닫기');    time.sleep(0.5)  
		return 1
	
	def SS_TI_Summation2(directory,mmStart,mmEnd,trd_3,trd_4):
		if trd_3 or trd_4:
			utils.semusarang_Menu_Popup('계산서합계표')
			pyautogui.write(str(mmStart));pyautogui.press('enter');time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter');time.sleep(1.5)
			pyautogui.press('f7');time.sleep(1.5);  
		if trd_3==True and trd_4==True:    
			utils.semusarang_Print_TI_Summary('3.pdf',directory) 
			utils.semusarang_Print_TI_Summary('4.pdf',directory) 
		elif trd_3==True and trd_4==False:    
			utils.semusarang_Print_TI_Summary('3.pdf',directory) 
		elif trd_3==False and trd_4==True:
			utils.semusarang_Print_TI_Summary('4.pdf',directory) 
		pyautogui.press('esc',presses=4,interval=0.25);print('열린 세무사랑 하부메뉴 닫기');    time.sleep(0.5)  
		return 1

	def SS_YueJaeGongje(directory,mmStart,mmEnd,seq_no,work_yy) :
		return 1
	
	def SS_SaleCard_Summation(directory,mmStart,mmEnd):
		utils.semusarang_Menu_Popup('신용카드매출전표등발행금액집계표')
		pyautogui.write(str(mmStart));
		if len(mmStart)!=2:pyautogui.press('enter');
		time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter',presses=3,interval=0.5);time.sleep(1.5)
		pyautogui.press('f11');time.sleep(1);pyautogui.press('enter');time.sleep(0.5);
		utils.semusarang_Print('5.pdf',directory)   
		return 1
	def SS_Card_Summation(directory,mmStart,mmEnd):
		utils.semusarang_Menu_Popup('신용카드매출전표등수령명세서(갑)(을)')
		pyautogui.write(str(mmStart));pyautogui.press('enter');time.sleep(0.5);pyautogui.write(str(mmEnd));pyautogui.press('enter',presses=3,interval=0.5);time.sleep(1.5)
		pyautogui.press('f7');time.sleep(1);
		if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_VAT_MagamAfterCancel.png', confidence=0.4):
			pyautogui.press('enter');time.sleep(0.2)
		pyautogui.press('enter');time.sleep(0.5);
		utils.semusarang_Print('6.pdf',directory) 
	


# 세액공제감면 고용증대 여부 검토
def func_cntGoyoungIncrease(seq_no,work_YY,reg_date,fiscalMM):
	work_YY = int(work_YY)
	fiscalMM = int(fiscalMM)
	Increase_UsualEmp = 0
	sum_YoungworkMM_Now = 0
	sum_YoungworkMM_Pre = 0
	sangsi_MM_Pre = 0
	sangsi_MM_Now = 0

	if fiscalMM == 12:
			reg_year = int(reg_date[:4])
			if reg_year < work_YY:
					sangsi_MM_Now = 12
					sangsi_MM_Pre = 1
					if reg_year > (work_YY - 1):
							sangsi_MM_Pre = 12
					elif reg_year == (work_YY - 1):
							sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1
					else:
							sangsi_MM_Pre = 12
			elif reg_year == work_YY:
					sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1
					sangsi_MM_Pre = 1
			else:
					sangsi_MM_Now = 1
					sangsi_MM_Pre = 1
	else:
			if int(reg_date[:4]) < work_YY:
					if (work_YY - int(reg_date[:4])) == 1:
							sangsi_MM_Now = 12
							sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1 + fiscalMM
					elif (work_YY - int(reg_date[:4])) == 0:
							if int(reg_date[5:7]) > fiscalMM:
									sangsi_MM_Now = 1
									sangsi_MM_Pre = 1
							else:
									sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1 + fiscalMM
									sangsi_MM_Pre = 12 - int(reg_date[5:7]) + 1 + fiscalMM
					elif (work_YY - int(reg_date[:4])) > 1:
							sangsi_MM_Now = 12
							sangsi_MM_Pre = 12
			elif int(reg_date[:4]) == work_YY:
					if int(reg_date[5:7]) > fiscalMM:
							sangsi_MM_Now = 1
							sangsi_MM_Pre = 1
					else:
							sangsi_MM_Now = 12 - int(reg_date[5:7]) + 1 - fiscalMM
							sangsi_MM_Pre = 1
			else:
					sangsi_MM_Now = 1
					sangsi_MM_Pre = 1

	endDate = "-12-31" if fiscalMM == 12 else f"-0{fiscalMM}-30"
	startDate = "-01-01" if fiscalMM == 12 else f"-0{12-fiscalMM+1}-01"

	sql_query = f"""
			SELECT empRegDate,empExitdate FROM tbl_Employ
			WHERE seq_no = %s AND empReject = ''
			AND YEAR(empRegDate) <= %s
			AND (empExitdate = '' OR YEAR(empExitdate) >= %s)
			ORDER BY empName
	"""
	with connection.cursor() as cursor:
			cursor.execute(sql_query, (seq_no, work_YY, work_YY - 1))
			employees = cursor.fetchall()

	sum_workMM_Pre = 0
	sum_YoungworkMM_Pre = 0
	sum_workMM_Now = 0
	sum_YoungworkMM_Now = 0

	for emp in employees:
			ExitDate = emp[1].strip()
			EnterDate = emp[0].strip()

			if not ExitDate or ExitDate >= f"{work_YY}{endDate}":
					ExitDate = f"{work_YY}{endDate}"
					ExitDate_Pre = f"{work_YY-1}{endDate}"
			else:
					if fiscalMM == 12:
							if ExitDate >= f"{work_YY}{startDate}":
									ExitDate_Pre = f"{work_YY-1}{endDate}"
							else:
									ExitDate = f"{work_YY}{startDate}"
									ExitDate_Pre = (datetime.datetime.strptime(emp[1], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
					else:
							if ExitDate >= f"{work_YY-1}{startDate}":
									ExitDate_Pre = f"{work_YY-1}{endDate}"
							else:
									ExitDate_Pre = (datetime.datetime.strptime(emp[1], "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

			workMM_Pre = max(0, min(12, abs((datetime.datetime.strptime(ExitDate_Pre, "%Y-%m-%d").year - int(EnterDate[:4])) * 12 + (datetime.datetime.strptime(ExitDate_Pre, "%Y-%m-%d").month - int(EnterDate[5:7])))))
			workMM_Now = max(0, min(12, abs((datetime.datetime.strptime(ExitDate, "%Y-%m-%d").year - int(EnterDate[:4])) * 12 + (datetime.datetime.strptime(ExitDate, "%Y-%m-%d").month - int(EnterDate[5:7])))))

			sum_workMM_Pre += workMM_Pre
			sum_workMM_Now += workMM_Now

	Increase_YoungEmp = round(sum_YoungworkMM_Now / sangsi_MM_Now, 2) - round(sum_YoungworkMM_Pre / sangsi_MM_Pre, 2)

	if Increase_YoungEmp > (round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)):
			Increase_YoungEmp = round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)

	if Increase_YoungEmp < 0:
			Increase_YoungEmp = 0

	Increase_UsualEmp = round(sum_workMM_Now / sangsi_MM_Now, 2) - round(sum_workMM_Pre / sangsi_MM_Pre, 2)

	# print(f"Increase_YoungEmp: {Increase_YoungEmp}")
	# print(f"Increase_UsualEmp: {Increase_UsualEmp}")   
	return (Increase_YoungEmp+Increase_UsualEmp)
def func_isKWAMIL(region):
	isKWAMIL = ""
	arrKWAMIL = ["서울", "인천", "의정부", "구리", "하남", "고양", "수원", "성남", "안양",
								"부천", "광명", "과천", "의왕", "군포", "시흥", "호평동", "평내동",
								"금곡동", "일패동", "이패동", "삼패동", "가운동", "수석동", "지금동", "도농동"]
	notKWAMIL = ["강화", "옹진", "대곡", "불로", "마전", "금곡", "오류", "왕길", "당하", "원당", "남동"]
	
	for kw in arrKWAMIL:
			if kw in region:
					isKWAMIL = "Y"
					for nw in notKWAMIL:
							if region.startswith("인천") and nw in region:
									isKWAMIL = ""
	return isKWAMIL
def func_isSpecialDeduct(upJong):
	isSpecialDeduct = "Y"
	arrSpecial = ["작물재배", "작물", "재배", "축산업", "어업", "광업",
								"도매", "소매", "도소매",
								
								"하수", "폐기물","원료재생", "재활용", "환경복원", 
								"제조업", "건설업", "정보통신공사", "전기통신업",

								"물류산업", "신성장", #세부 업종 추가 판단

								"여객운송업", "출판업", "영상", "오디오", "배급업", "방송업",  "프로그래밍",
								"시스템 통합", "소프트웨어", "프로그램", "정보서비스업", "연구개발업", "고업", "전문과학",
								"과학기술서비스업", "포장 및 충전업", "포장", "충전", "전문디자인업", "창작", "예술",
								"수탁생산업", "엔지니어링",  "직업기술", "자동차정비공장", "선박관리업",
								"의료기관 운영사업", "관광사업", "노인복지시설", "전시산업", "인력공급", "직업소개",
								"고용알선", "콜센터", "텔레마케팅", "에너지절약", "재가장기요양기관", "청소업",
								"경비", "경호", "시장조사", "여론조사", "사회복지", "무형재산", "연구개발지원업", "간병",
								"사회교육시설", "직원훈련기관", "도서관", "사적지", "주택임대관리업", 
								"재생에너지", "신재생에너지", "보안시스템", "임업", "통관", "자동차임대업", "여행"]
	for item in arrSpecial:
			if item in upJong:
					isSpecialDeduct = "Y"
					break
	return isSpecialDeduct
def func_isSmallAmt(upjong):
	isSmallAmt = 0
	arr120 = ["전기","가스","수도업"]
	for i in arr120:
		if upjong.find(i)!=-1: isSmall="120";isSmallAmt = 12000000000
	arr80 = ["인쇄","기록매체","농업","임업","어업","광업","건설업","정보통신공사","운수업","운송","운수","창고업","금융","보험"]
	for i in arr80:
		if upjong.find(i)!=-1: isSmall="80";isSmallAmt = 8000000000
	if upjong.find("제조")!=-1:
		arr80Jejo = ["담배","섬유","목재","나무","고무제품","펄프","플라스틱","의료","정밀","광학","시계","운송장비","제조"]
		for i in arr80Jejo:
			if upjong.find(i)!=-1: isSmall="80";isSmallAmt = 8000000000
		arr120Jejo = ["식료품","음료","의복","액세서리","모피","가죽","가방","신발","연탄","석유정제","코크스","화학제품","화학물질","의료용물질","의약품","비금속","금속","전자제품","컴퓨터","영상","음향","통신장비","전기장비","기계","자동차","트레일러","가구","수도","가스","증기"]
		for i in arr120Jejo:
			if upjong.find(i)!=-1: isSmall="120" ;isSmallAmt = 12000000000 
	arr50 = ["도매","소매","도소매","정보통신","정보서비스"]
	for i in arr50:
		if upjong.find(i)!=-1: isSmall="50";isSmallAmt = 5000000000
	arr30 = ["하수","폐기물","원료재생","부동산","전문","과학","기술","사업시설","사업지원","예술","스포츠","여가"]
	for i in arr30:
		if upjong.find(i)!=-1: isSmall="30";isSmallAmt = 3000000000
	arr10 = ["산업용 기계","장비수리","수리","숙박","음식","교육","보건","사회복지","서비스"]
	for i in arr10:
		if upjong.find(i)!=-1: isSmall="10" ;isSmallAmt = 1000000000
	return isSmallAmt

def func_isMiddle(upjong):
	isMiddle = "0"
	arr1000 = ["농업","임업","어업","광업","전기","가스","수도업","도매","소매","도소매","건설업","정보통신공사"]
	for i in arr1000:
		if upjong.find(i)!=-1: isMiddle="1000"
	arr800 = ["인쇄","기록매체","하수","폐기물","원료재생","운수업","운송","운수","창고업","정보통신"]
	for i in arr800:
		if upjong.find(i)!=-1: isMiddle="800"
	if upjong.find("제조")!=-1:
		arr800Jejo = ["음료","의료용물질","의약품","비금속","의료","정밀","광학","시계","기계","제조"]
		for i in arr800Jejo:
			if upjong.find(i)!=-1: isMiddle="800"        
		arr1500Jejo = ["의복","액세서리","모피","가죽","가방","신발","펄프","종이","가구"]
		for i in arr1500Jejo:
			if upjong.find(i)!=-1: isMiddle="1500"
		arr1000Jejo = ["담배","섬유","목재","나무","고무제품","식료품","연탄","석유정제","플라스틱","운송장비","제조","코크스","화학제품","화학물질","금속","전자제품","컴퓨터","영상","음향","통신장비","전기장비","자동차","트레일러"]
		for i in arr1000Jejo:
			if upjong.find(i)!=-1: isMiddle="1000" 
	arr600 = ["산업용 기계","장비수리","수리","정보서비스","전문","과학","기술","사업시설","사업지원","예술","스포츠","여가","보건","사회복지","서비스"]
	for i in arr600:
		if upjong.find(i)!=-1: isMiddle="600"       
	arr400 = ["숙박","음식","교육","금융","보험","부동산","임대"]
	for i in arr400:
		if upjong.find(i)!=-1: isMiddle="400"  			
	return isMiddle
	
def  func_isSmall(upJong,saleAmt):
	isSmall = ""
	if any(x in upJong for x in ["전기", "가스", "수도"]):
			isSmall = "Y" if saleAmt < 12000000000 else ""
	if any(x in upJong for x in ["인쇄", "농업", "광업", "건설업"]):
			isSmall = "Y" if saleAmt < 8000000000 else ""
	if "제조" in upJong:
			arr120Jejo = ["식료품", "음료", "의복", "가죽", "가방", "신발", "연탄", "코크스", "석유",
											"화학물질", "의료용물질", "비금속", "광물", "금속", "전자부품", "컴퓨터",
											"음향", "영상", "통신장비", "전기장비", "기계", "가구", "자동차", "트레일러",
											"수도", "가스", "증기"]
			found = False
			for item in arr120Jejo:
					if item in upJong:
							isSmall = "Y" if saleAmt < 12000000000 else ""
							found = True
							break
			if not found:
					isSmall = "Y" if saleAmt < 8000000000 else ""
	if any(x in upJong for x in ["도매", "소매", "도소매", "출판", "영상", "방송", "방송통신", "정보서비스"]):
			isSmall = "Y" if saleAmt < 5000000000 else ""
	if any(x in upJong for x in ["인력공급", "직업소개", "고용알선", "콜센터", "텔레마케팅", "부동산",
																"하수도", "폐기물 재상", "전문 과학", "전문과학", "사업시설", "사업지원",
																"전문디자인업", "창작", "예술"]):
			isSmall = "Y" if saleAmt < 3000000000 else ""
	if isSmall == "":
			isSmall = "Y" if saleAmt < 1000000000 else ""
	return isSmall
def func_isKnowledge(upJong):
	isKnowledge = ""
	arrKnowledge = ["엔지니어링", "연구개발", "전기통신", "프로그래밍", "소프트웨어", "프로그램",
									"시스템통합", "시스템관리", "영화", "방송", "전문디자인", "오디오", "원판녹음",
									"광고물", "방송", "정보서비스", "출판", "창작", "예술", "인쇄출판", "경영컨설팅"]
	for item in arrKnowledge:
			if item in upJong:
					isKnowledge = "Y"
					break
	return isKnowledge
def func_isChangUp(upJong):
	isChangUp = ""
	arrChangUp = ["광업", "제조", "정보통신", "전문과학", "하수", "폐기물", "원료재생", "재활용",
								"환경복원", "건설업", "정보통신공사", "통신판매", "물류산업", "엔지니어링",
								"사업시설", "조경", "사업지원", "예술", "창작", "전문디자인업", "스포츠", "이용업",
								"미용업", "사회교육", "직원훈련", "직업기술", "과학기술서비스업", "전시산업",
								"노인복지", "간병", "관광사업", "여행", "숙박", "음식", "에너지", "창업보육센터",
								"통신판매", "금융"]
	notChangUp = ["세무사", "변호사", "변리사", "법무사", "회계사", "수의사", "행정사", "건축사",
								"감정평가사", "중개사", "블록체인", "뉴스제공", "감상실", "암호화폐", "암호화자산",
								"예술가", "오락", "유흥", "커피"]
	for item in arrChangUp:
		if item in upJong:
			isChangUp = "Y"
			break
	for item in notChangUp:
		if item in upJong:
			isChangUp = "N"
			break
	return isChangUp
def func_isMyulyu(upJong):
	isMyulyu = ""
	arrMyulyu = ["육상", "수상", "항공", "운송","운수", "화물", "퀵", "택배", "보관업", "창고업",
								"화물운송", "화물포장", "화물검수", "계량", "예선", "도선", "파렛트", "기계임대", "장비임대"]
	for item in arrMyulyu:
			if item in upJong:
					isMyulyu = "Y"
					break
	return isMyulyu
def func_isNewGroth(upJong):
	isNewGroth = ""
	arrNewGroth = ["엔지니어링", "연구개발", "전기통신", "정보서비스", "컴퓨터", "프로그래밍",
									"소프트웨어", "프로그램", "시스템통합", "시스템관리", "영화", "방송",
									"전문디자인", "보안시스템", "오디오", "원판녹음", "광고물", "방송", "정보서비스",
									"출판", "창작", "예술", "인쇄출판", "경영컨설팅", "관광", "국제회의", "유원시설",
									"관광객", "육상", "수상", "항공", "운송", "화물", "퀵", "택배", "보관업", "창고업",
									"화물운송", "화물포장", "화물검수", "계량", "예선", "도선", "파렛트", "기계임대", "장비임대",
									"전시산업", "시장조사", "여론조사", "광고업"]
	for item in arrNewGroth:
			if item in upJong:
					isNewGroth = "Y"
					break
	return isNewGroth

def func_ChangupDeduct(work_YY,kisu,isKWAMIL,isChangUpUpjong,isNewGroth,isVenture,saleAmt,reg_date,age):
  ChangUpDeduct = "N"
  ChangUpDeductRate = 0  
  if kisu is not None:
    if kisu < 6 and isChangUpUpjong == "Y" and isKWAMIL == "":
        ChangUpDeductRate = 50;ChangUpDeduct = "Y"
    if kisu < 6 and isChangUpUpjong == "Y" and (age > 0 and age < 36):
        ChangUpDeductRate = 100 if isKWAMIL == "" else 50
        ChangUpDeduct = "Y"
    if isChangUpUpjong == "Y" and isKWAMIL == "" and isNewGroth == "Y" and kisu is not None and kisu <= 3 and ChangUpDeductRate <= 50:
        ChangUpDeductRate = 75;ChangUpDeduct = "Y"
    if isVenture == "Y":
        ChangUpDeductRate = 50;ChangUpDeduct = "Y"
    # 소규모창업 (조특법 제6항)
    isLittle = ""
    reSale = saleAmt
    try:
        reg_dt = datetime.strptime(reg_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        reg_year = reg_dt.year
        reg_month = reg_dt.month
    except Exception:
        reg_year, reg_month = 0, 0
    if reg_year == int(work_YY) and saleAmt > 0:
        reSale = saleAmt * 12 / (12 - reg_month + 1)
    if kisu < 6 and (isChangUpUpjong == "Y" ):
        if reg_date >= datetime.strptime("2018-05-29", "%Y-%m-%d").replace(tzinfo=timezone.utc) and reSale <= 48000000:
            isLittle = "Y";ChangUpDeduct = "Y"
            ChangUpDeductRate = 50 if isKWAMIL == "Y" else 100
        if reg_year >= 2022 and reSale <= 80000000:
            isLittle = "Y";ChangUpDeduct = "Y"
            ChangUpDeductRate = 50 if isKWAMIL == "Y" else 100
    #최종판단
    if ChangUpDeductRate==0:
      ChangUpDeduct = "N"  
  return ChangUpDeductRate,ChangUpDeduct ,isLittle

def func_SpecialDeduct(upJong,isSpecialUpjong,isRural,isSmall):
  SpecialDeductRate = 0;SpecialDeduct = "N"
  # 도매소매의료 여부
  isDoSoMedi = "Y" if any(x in upJong for x in ["도매", "소매", "도소매", "의료"]) else ""  
  if isSpecialUpjong == "Y":
    # 지방인 경우 - 중기업도 감면적용
    if isRural == "Y":  
        if isSmall == "Y":# 소기업인 경우/중기업 아님
            SpecialDeductRate = 10 if isDoSoMedi == "Y" else 30
            SpecialDeduct = "Y"
        else:
            SpecialDeductRate = 5 if isDoSoMedi == "Y" else 15
            SpecialDeduct = "Y"
    # 수도권인 경우 중기업은 감면 안됨 / 소기업만 적용
    else:  
        if isSmall == "Y":
            SpecialDeductRate = 10 if isDoSoMedi == "Y" else 20
            SpecialDeduct = "Y"
        # 수도권 중기업 지식기반산업 규정은 23년 귀속부터 폐지하였다
        # else:
        #     if isKnowledge == "Y":
        #         SpecialDeductRate = 10;SpecialDeduct = "Y"    
    #최종판단
    if SpecialDeductRate==0:
      SpecialDeduct = "N"  
  return SpecialDeductRate,SpecialDeduct
class CORP:

	#법인세신고서작성
	def semusarang_Make_CorpSheet(flag,member,filelist,workyear,directory,preFilelist,finalKi,htxLoginID):
		memuser = MemUser.objects.get(seq_no=member[3])
		memdeal = MemDeal.objects.get(seq_no=member[3])
		saleAmt = member[4]
		isProceed = True  
		#---------------------------------------------------------------------------------------------------------------------------세액감면공제 파악
		ChangUpDeductRate = 0;ChangUpDeduct = "N"
		SpecialDeductRate=0;	SpecialDeduct = "N"
		upjong = memuser.uptae+memuser.jongmok
		region = memuser.biz_addr1 + memuser.biz_addr2
		age = datetime.now().year- int(memuser.ssn[:2])-1901 
		isYoung=0
		if age<36 : isYoung = age
		kisu = finalKi
		# kisu = int(workyear) - int(memuser.reg_date[:4]) + 1
		isVenture = memuser.isventure
		# 수도권과밀억제권역 판단 Y 또는 ""
		isKWAMIL = func_isKWAMIL(region)
		# 수도권(도시) 여부: 해당 단어가 없으면 지방(Y)
		isRural_count = sum(1 for r in ["서울", "인천", "경기"] if r in region)
		isRural = "Y" if isRural_count <= 0 else ""
		# 특별세액감면 검토 (업종)
		isSpecialUpjong = func_isSpecialDeduct(upjong)
		# 소기업/중기업 판별
		isSmall = func_isSmall(upjong,saleAmt)
		isMiddle = func_isMiddle(upjong)
		isSmallAmt = func_isSmallAmt(upjong)
		# 지식기반사업 여부
		isKnowledge = func_isKnowledge(upjong)

		# 창업 관련 변수
		isChangUpUpjong = func_isChangUp(upjong)
		# 물류산업여부/성정산업
		isMyulyu = func_isMyulyu(upjong)
		isNewGroth = func_isNewGroth(upjong)

		# 물류산업여부/신성장산업 인 경우 특별감면과 창업감면 대상이다
		if isMyulyu=="Y" or isNewGroth=="Y":
				isSpecialUpjong = "Y"
				isChangUpUpjong = "Y"
		# 감면율 판단
		SpecialDeductRate,SpecialDeduct = func_SpecialDeduct(upjong,isSpecialUpjong,isRural,isSmall)
		ChangUpDeductRate,ChangUpDeduct,isLittle = func_ChangupDeduct(workyear,kisu,isKWAMIL,isChangUpUpjong,isNewGroth,isVenture,saleAmt,memuser.reg_date,age)        
		# 재무조건에 따른 감면율 조정
		# if (net_income - float(valDefict)) < 0 or net_income < 0:
		#     ChangUpDeductRate = 0;SpecialDeductRate = 0

		#고용증대 인원
		# cntGoyoungIncrease = func_cntGoyoungIncrease(memuser.seq_no,workyear,memuser.reg_date,memdeal.fiscalmm)
			
		if isProceed and not "19-갑.pdf" in filelist  and member[13]>0  and flag=='1' :#가지급금이 있는경우
			if member[16]>0: isProceed = semusarang_Menu_Corptax('가지급금등의인정이자조정명세서','19-갑.pdf',workyear,directory)  
			elif member[16]==0: 
				print('가지급금:'+str(member[13]))
				print('미수수익:'+str(member[16]))
				confirm = pyautogui.confirm('인정이자를 회계에 반영하지 않았습니다. 미수수익/이자수익을 계상하고 다시 시도하세요.  작성된 재무제표를 삭제합니다. 아니오는 삭제안함')
				if confirm=='OK':
					flag='1'
					utils.delete_CorpSheet_files(flag,directory)
				os._exit()#시스템중단
		if (member[26]-member[15])>7500: #이자수익에서 미수수익 차감하고 순이자가 7500원 이상이고 선납세금이 이자수익보다 작은경우
			if member[5]>0:      #이익인경우
				if member[15]>0:       #선납세금이 있는 경우
					if not "10-갑.pdf" in filelist and flag=='1':
						confirm = pyautogui.confirm('이자분 선납법인세를 미지급법인세와 상계하는 회계처리을 계상하고 다시 시도하세요. 작성된 재무제표를 삭제합니다.\n예:제무제표삭제후 중단 \n아니오: 삭제하지않고 중단 \n무시:계속진행',buttons=['예','아니오','무시'])
						if confirm=='예':   utils.delete_CorpSheet_998_files('1',directory);time.sleep(0.5) ;os._exit()   #중단 
						elif confirm=='아니오':os._exit()   #중단 
			else:                 #손실
				if not "10-갑.pdf" in filelist and member[15]>0  and flag=='1':       #손실/선납세금있고/순이자가 7500원이상
					confirm = pyautogui.confirm(f'선납세액:{member[15]}\n이자수익:{member[26]}\n원천납부세액명세서를 작성하시겠습니까? [아니오 : 다음 서식으로 이동]')
					if confirm=='OK': semusarang_Menu_Corptax('원천납부세액명세서','10-갑.pdf',workyear,directory)
		if not "104.pdf" in filelist and flag=='1' : semusarang_Menu_Corptax('이익잉여금처분계산서','104.pdf',workyear,directory)
		if not "103.pdf" in filelist and member[34]>0 : 
			utils.semusarang_Menu_Popup('제조원가명세서')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			utils.semusarang_Print('103.pdf',directory)
		if not "102.pdf" in filelist : semusarang_Menu_Corptax('손익계산서','102.pdf',workyear,directory)
		if not "101.pdf" in filelist : semusarang_Menu_Corptax('재무상태표','101.pdf',workyear,directory)
		if not "105.pdf" in filelist  : semusarang_Menu_Corptax('합계잔액시산표','105.pdf',workyear,directory)   
		if not "3-1.pdf" in filelist  and flag=='1': semusarang_Menu_Corptax('표준재무상태표','3-1.pdf',workyear,directory)  
		if not "40-6.pdf" in filelist  and flag=='2': semusarang_Menu_Corptax('표준재무상태표','40-6.pdf',workyear,directory)  
		if not "40-9.pdf" in filelist  and flag=='2': semusarang_Menu_Corptax('표준합계잔액시산표','40-9.pdf',workyear,directory)    
		if not "3-2.pdf" in filelist  and flag=='1': 
			utils.semusarang_MenuCode_Popup('3010','표준손익계산서')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('Y');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')  
			if member[30]>0:       #법인세비용이 있는 경우  
				pyautogui.press('f3');time.sleep(1);pyautogui.press('pgdn');time.sleep(1)
				pyperclip.copy('법인세비용');time.sleep(0.25);pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
				pyautogui.write(str(member[30]));pyautogui.press('enter',presses=3,interval=0.5);time.sleep(0.5);pyautogui.press('esc')      
				# confirm = pyautogui.confirm('법인세비용은 '+str(member[30])+'원 입니다. 소득금액조정명세서를 작성하고 조정창만 닫아주세요.(출력진행) [아니오 : 다음 서식으로 이동]')
				# if confirm=='OK': semusarang_Print('3-2.pdf',directory)
			utils.semusarang_Print('3-2.pdf',directory)
		if not "40-7.pdf" in filelist  and flag=='2': 
			utils.semusarang_MenuCode_Popup('3010','표준손익계산서')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')  
			if member[30]>0:       #소득세비용이 있는 경우  
				pyautogui.press('f3');time.sleep(1);pyautogui.press('pgdn');time.sleep(1)
				pyperclip.copy('소득세비용');time.sleep(0.25);pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
				pyautogui.write(str(member[30]));pyautogui.press('enter',presses=3,interval=0.5);time.sleep(0.5);pyautogui.press('esc')      
			utils.semusarang_Print('40-7.pdf',directory)    
		if not "3-3.pdf" in filelist and member[34]>0:
			utils.semusarang_Menu_Popup('표준원가명세서');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')   
			utils.semusarang_Print('3-3.pdf',directory)    
		if not "40-8.pdf" in filelist and member[34]>0 and flag=='2':
			utils.semusarang_Menu_Popup('표준원가명세서');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f12');time.sleep(1);print('불러오기');pyautogui.press('enter');time.sleep(0.5);print('예 버튼')
			pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')   
			utils.semusarang_Print('40-8.pdf',directory)        
		if not "3-4.pdf" in filelist and flag=='1': semusarang_Menu_Corptax('이익잉여금처분계산서','3-4.pdf',workyear,directory)  
		if not "90.pdf" in filelist and flag=='1': semusarang_Menu_Corptax('전산조직운용명세서','90.pdf',workyear,directory)  
		if not "98.pdf" in filelist and flag=='2': semusarang_Menu_Corptax('전산조직운용명세서','98.pdf',workyear,directory)  
		saleRecord=0
		if saleAmt>0 and ((not "16.pdf" in filelist and memuser.biz_type<4) or (not "52-1.pdf" in filelist and memuser.biz_type>=4)): 
			sql = "select acnt_cd, sum(tranamt_Dr) as 금액 from ds_slipledgr2  WITH (NOLOCK) where  work_yy='"+str(workyear)+"' and seq_no='"+str(member[3])+"' "
			if flag=='1':sql += "and acnt_cd>=401 and acnt_cd<=430 "
			elif flag=='2':sql += "and ((acnt_cd>=401 and acnt_cd<=430) or acnt_cd=930) "
			sql += " GROUP BY acnt_cd "
			cursor = connection.cursor()
			cursor.execute(sql)
			saleRecord = cursor.fetchall()
			connection.commit()
			connection.close()          
			if len(saleRecord)==1 and flag=='1':
				if not "16.pdf" in filelist  and flag=='1': semusarang_Menu_Corptax('수입금액조정명세서','16.pdf',workyear,directory)  
				if not "17.pdf" in filelist  and flag=='1':semusarang_Menu_Corptax('조정후수입금액명세서','17.pdf',workyear,directory) 
				#if not "52-1.pdf" in filelist  and flag=='2': semusarang_Menu_Corptax('총수입금액조정명세서','52-1.pdf',workyear,directory) 
				#if not "52-2.pdf" in filelist  and flag=='2':semusarang_Menu_Corptax('조정후총수입금액명세서','52-2.pdf',workyear,directory)
			else:
				if not "16.pdf" in filelist and flag=='1':utils.semusarang_Menu_Popup('수입금액조정명세서')
				elif not "52-1.pdf" in filelist  and flag=='2':utils.semusarang_Menu_Popup('총수입금액조정명세서')
				pyautogui.hotkey('ctrl','f5');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5);
				for i in range(len(saleRecord)):
					if i==0: 
						if flag=='1':pyautogui.press('1');time.sleep(0.3);
						pyautogui.press('f4');time.sleep(0.3);pyautogui.press('tab');time.sleep(0.3);pyautogui.press('down');time.sleep(0.3);pyautogui.press('down')
					elif i>=1:
						if flag=='1':pyautogui.press('1');time.sleep(0.3);
						pyautogui.press('f4');time.sleep(0.3);pyautogui.press('down');pyautogui.press('tab');time.sleep(0.3);pyautogui.press('down');time.sleep(0.3)
						for j in range(i-1):
							pyautogui.press('down');time.sleep(0.3)
					
				pyautogui.press('f11');time.sleep(3);print('저장하기 2초 소요') 
				if not "17.pdf" in filelist  and  flag=='1':utils.semusarang_Print('16.pdf',directory) ;utils.semusarang_Menu_Popup('조정후수입금액명세서');
				elif not "52-2.pdf" in filelist and flag=='2':utils.semusarang_Print('52-1.pdf',directory)  ;utils.semusarang_Menu_Popup('조정후총수입금액명세서');
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
				pyautogui.hotkey('ctrl','2');pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
				confirm = pyautogui.confirm('조정후수입금액명세서를 작성하고 OK 를 누르세요(출력진행함)')
				if confirm=='Cancel':isProceed = False
				else:
					pyautogui.press('f11');time.sleep(3);print('저장하기 2초 소요') 
					if  not "17.pdf" in filelist and flag=='1':semusarang_Menu_Corptax('조정후수입금액명세서','17.pdf',workyear,directory) 
					elif  not "52-2.pdf" in filelist and flag=='2':utils.semusarang_Print('52-2.pdf',directory)  
		if isProceed and (not "51.pdf" in filelist and flag=='1') or (not "90.pdf" in filelist and flag=='2')  : 
			utils.semusarang_Menu_Popup('중소기업기준검토표')
			pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
			pyautogui.press('down',presses=6,interval=0.25)
			pyautogui.write(isMiddle)
			pyautogui.hotkey('ctrl','3') 
			if saleAmt>isSmallAmt :
				pyautogui.press('down');time.sleep(0.25);pyautogui.write('2');time.sleep(0.5)
				pyautogui.press('down');time.sleep(0.5)
				pyautogui.write(isSmall);time.sleep(0.25);pyautogui.press('enter')
				confirm = pyautogui.confirm('매출액이 소기업기준매출액을 초과하였습니다. [[특별세액감면 판단시 주의!!]]. 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오:세무조정중단]')
				if confirm=='Cancel':
					pyautogui.press('esc',presses=3,interval=0.2)
					isProceed = False;return False   #중단 
			else:
				pyautogui.press('down',presses=3,interval=0.25)
				pyautogui.write(isSmall);time.sleep(0.25);pyautogui.press('enter')
			if isSmall=="" or isMiddle=="":
				confirm = pyautogui.confirm('중소기업확인서가 제대로 작성되지 않았습니다. 기준금액을 입력하세요. 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오:세무조정중단]')
				if confirm=='Cancel':isProceed = False;return False   #중단      
			pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요')  
			if flag=='1':utils.semusarang_Print('51.pdf',directory) 
			elif flag=='2':utils.semusarang_Print('90.pdf',directory) 
			pyautogui.press('esc')#중소기업기준검토표는 3번눌러야 나간다

		if isProceed and not "16-2.pdf" in filelist  and member[27]>0 and flag=='1': 
			utils.semusarang_Menu_Popup('수입배당금액명세서')
			confirm = pyautogui.confirm('수입배당금조정:'+str(member[27])+'  있으니 소득금액 조정반영후 확인누르면 출력진행')
			if confirm=='Cancel':isProceed = False;return False   #중단  
			else:
				pyautogui.press('f11');time.sleep(0.5);print('저장')
				utils.semusarang_Print('16-2',directory);time.sleep(0.5)   
		if isProceed and not "40-을.pdf" in filelist  and (member[28]>0 or member[29]>0) : 
			utils.semusarang_Menu_Popup('외화자산등평가차손익조정명세서')
			confirm = pyautogui.confirm('외화환산이익:'+str(member[28])+'/외화환산손실:'+str(member[29])+' 등 있으니 을표와 갑표를 작성하고 세무조정 반영후 확인 누르면 출력진행')
			if confirm=='Cancel':isProceed = False;return False   #중단  
			pyautogui.press('f11');time.sleep(0.5);print('저장')
			pyautogui.hotkey('ctrl','3');time.sleep(0.25);print('40-갑 출력준비')   
			utils.semusarang_Print('40-갑',directory);time.sleep(0.5)   
			isProceed = semusarang_Menu_Corptax('외화자산등평가차손익조정명세서','40-을.pdf',workyear,directory)
		if isProceed  and member[6]>0  and ((not "6-11.pdf" in filelist and flag=='1') or (not "67.pdf" in filelist and flag=='2')) :
				if flag=='1':utils.semusarang_Menu_Popup('세금과공과금명세서')
				elif flag=='2':utils.semusarang_Menu_Popup('제세공과금조정명세서')
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter',presses=4,interval=0.3);pyautogui.press('tab');time.sleep(0.5)
				confirm = pyautogui.confirm('세금과공과금명세서를 작성하고 세무조정금액 '+str(member[7])+'원을 조정입력하고(세무조정창은 닫기) OK 를 누르세요(출력진행함).[아니오:세무조정중단]')
				if confirm=='Cancel':isProceed = False  
				if flag=='1':utils.semusarang_Print('6-11',directory);time.sleep(0.5) 
				elif flag=='2':  utils.semusarang_Print('67',directory);time.sleep(0.5)   
		if isProceed and member[8]>0 and ((not "23-갑.pdf" in filelist and flag=='1') or  (not "55.pdf" in filelist and flag=='2')): 
			if  flag=='1':isProceed = semusarang_Menu_Corptax('접대비(기업업무추진비)조정명세','23-갑.pdf',workyear,directory) 
			elif flag=='2':  isProceed = semusarang_Menu_Corptax('접대비(기업업무추진비)조정명세','55.pdf',workyear,directory) 
		if isProceed and member[9]>0 and ((not "22.pdf" in filelist and flag=='1' ) or (not "56.pdf" in filelist and flag=='2' )) : 
			if flag=='1':
				utils.semusarang_Menu_Popup('법인세과세표준및세액조정계산서');pyautogui.press('f12');time.sleep(1.5);pyautogui.press('enter');time.sleep(1.5);pyautogui.press('f11');time.sleep(1.5);pyautogui.press('esc',presses=3,interval=0.5)     
				utils.semusarang_Menu_Popup('기부금조정명세서');pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)   
			elif flag=='2':
				utils.semusarang_Menu_Popup('기부금명세서및조정명세서');pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)   
			confirm = pyautogui.confirm('기부금조정명세서를 기부금조정까지 작성하고  OK 를 누르세요(출력진행함).[아니오:세무조정중단]')
			if confirm=='OK':  
				pyautogui.press('f11');time.sleep(3)  ;pyautogui.press('enter');time.sleep(0.5)
				if flag=='1':
					pyautogui.hotkey('ctrl','2');time.sleep(0.25);print('21.기부금조정명세서 출력준비')   
					utils.semusarang_Print_NotExit('21',directory);time.sleep(0.5)  
					pyautogui.hotkey('ctrl','1');time.sleep(0.5);print('22. 기부금명세서 출력준비')      
					utils.semusarang_Print('22',directory);time.sleep(0.5) 
				elif flag=='2':utils.semusarang_Print('56',directory);time.sleep(0.5) 
			else:
				pyautogui.press('esc',presses=3,interval=0.2)
		if isProceed and member[10]>0 and not "34.pdf" in filelist   and flag=='1': 
			isProceed = semusarang_Menu_Corptax('대손충당금및대손금조정명세서','34.pdf',workyear,directory)   
			confirm = pyautogui.confirm(f'대손충당금({member[10]}) 평가조정명세서를 작성하고와  OK 를 누르세요(출력진행함). [아니오 : 나가기]')
			if confirm=='Cancel': 
				pyautogui.press('esc',presses=5,interval=0.2) 
			else:
				pyautogui.press('f11');time.sleep(1)
				utils.semusarang_Print('34',directory);time.sleep(0.5)  
		if isProceed and not "26-갑.pdf" in filelist  and member[13]>0 and member[11]>0 and flag=='1': 
			utils.semusarang_MenuCode_Popup('3027','업무무관부동산등에관련한차입금이자조정명세서');time.sleep(0.25);pyautogui.press('enter')
			confirm = pyautogui.confirm('업무무관부동산등에관련한차입금이자조정명세서를 작성하고 [갑지]에서  OK 를 누르세요( 갑지먼저 출력진행함). [아니오:다음서식]')
			if confirm=='OK':
				utils.semusarang_Print('26-갑',directory);time.sleep(0.5)
				utils.semusarang_MenuCode_Popup('3027','업무무관부동산등에관련한차입금이자조정명세서');time.sleep(0.25);pyautogui.press('enter');time.sleep(1)
				utils.semusarang_Print_NotExit('26-을',directory);time.sleep(1)  
			else:
				pyautogui.press('esc',presses=3,interval=0.2)  
		if isProceed and (  member[20]>0 and not "39.pdf" in filelist and flag=='1') or  ( member[20]>0 and not "62.pdf" in filelist and flag=='2') : 
			if  flag=='1':utils.semusarang_Menu_Popup('재고자산(유가증권)평가조정');pyautogui.press('enter');time.sleep(0.5)
			elif flag=='2':utils.semusarang_Menu_Popup('재고자산평가조정명세서');pyautogui.press('enter');time.sleep(0.5)
			confirm = pyautogui.confirm(f'재고자산({member[20]}) 평가조정명세서를 작성하고와  OK 를 누르세요(출력진행함). [아니오 : 나가기]')
			if confirm=='Cancel': 
				pyautogui.press('esc',presses=5,interval=0.2) 
			else:
				pyautogui.press('f11');time.sleep(1)
				if  flag=='1':utils.semusarang_Print('39',directory);time.sleep(0.5)  
				elif flag=='2':utils.semusarang_Print('62',directory);time.sleep(0.5)  ;pyautogui.press('esc');time.sleep(0.5)  
		if isProceed and ( (member[17]-member[21])>0 and not "20-4.pdf" in filelist and flag=='1') or ((member[17]-member[21])>0 and not "53-3.pdf" in filelist and flag=='2'):#고정자산에서 토지를 뺀 유형자산 
			if flag=='1':
				utils.semusarang_MenuCode_Popup('1053','미상각분감가상각비'); pyautogui.press('enter',presses=3,interval=0.3)
				utils.semusarang_Menu_Popup('미상각자산감가상각조정명세서');time.sleep(0.25);pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter')
			elif flag=='2':
				utils.semusarang_MenuCode_Popup('1053','미상각분감가상각비'); pyautogui.press('enter',presses=3,interval=0.3)
				utils.semusarang_Menu_Popup('미상각분감가상각조정명세서');time.sleep(0.25);pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter')      
			pyautogui.hotkey('ctrl','1');time.sleep(0.25);pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter')
			confirm = pyautogui.confirm('열린 서식 중 해당하는 서식을 출력/저장하고 메뉴닫고 상태에서 OK 를 누르세요. [아니오 : 세무조정 중단]')
			if confirm=='Cancel':
				pyautogui.press('esc',presses=3,interval=0.2)
				isProceed = False;return False   #중단 
			else:
				if flag=='1':isProceed = semusarang_Menu_Corptax('감가상각비조정명세서합계표','20-4.pdf',workyear,directory)  
				elif flag=='2':isProceed = semusarang_Menu_Corptax('감가상각비조정명세서합계표','53-3.pdf',workyear,directory)  
		if isProceed and not "15.pdf" in filelist and flag=='1':
			time.sleep(1);utils.semusarang_Menu_Popup('소득금액조정합계표및명세서');time.sleep(1)
			confirm = pyautogui.confirm('세무조정이 있으면 조정사항 반영하고 확인을 누르세요(출력진행).[취소] 서식 저장안함')
			if confirm=='OK':utils.semusarang_Print('15.pdf',directory)  
			else : pyautogui.press('esc',presses=2,interval=0.2)
		if isProceed and not "47.pdf" in filelist and flag=='2':
			time.sleep(1);utils.semusarang_Menu_Popup('소득금액조정합계표및명세서');time.sleep(1)
			confirm = pyautogui.confirm('소득금액조정합계표및명세서에 이상없으면 확인을 누르세요(출력진행).[취소] 세무조정 중단')
			if confirm=='OK':utils.semusarang_Print('47.pdf',directory)  
			else: isProceed = False;return False   #중단
		if isProceed and not "46.pdf" in filelist and flag=='2':
			utils.semusarang_Menu_Popup('조정계산서');time.sleep(0.5)
			pyautogui.write('40');time.sleep(0.3);pyautogui.write('1');time.sleep(0.3);pyautogui.press('f12');time.sleep(0.5)
			pyautogui.press('enter');time.sleep(0.3);pyautogui.press('f11');time.sleep(2)
			utils.semusarang_Print('46.pdf',directory) 
			# confirm = pyautogui.confirm('조정계산서를 작성하고 확인을 누르세요(출력진행).[취소] 세무조정 중단')
			# if confirm=='OK':semusarang_Print('46.pdf',directory)  
			# else: isProceed = False;return False   #중단    
		if isProceed and not "47-갑.pdf" in filelist  and (member[10]>0 or member[9]>0 or member[8]>0)  and flag=='1': isProceed = semusarang_Menu_Corptax('주요계정명세서','47-갑.pdf',workyear,directory) 
		if isProceed and not "47-을.pdf" in filelist  and (member[13]>0 or member[20]>0 )  and flag=='1': isProceed = semusarang_Menu_Corptax('주요계정명세서','47-을.pdf',workyear,directory) 
		valDefit = member[31]
		if valDefit=='':valDefit = 0
		else: valDefit = int(member[31])
		if isProceed and not "50-갑.pdf" in filelist   and flag=='1': 
			utils.semusarang_Menu_Popup('자본금과적립금조정명세서')
			if member[5]<0 or valDefit>0:#당기결손금 있거나 이월결손금 있는 경우
				pyautogui.hotkey('ctrl','4');time.sleep(0.25);pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter');time.sleep(0.25);pyautogui.press('down');time.sleep(0.25)
				# pyautogui.write(str(workyear)+"1231");time.sleep(0.25)
				confirm = pyautogui.confirm(f'당기결손금:{member[5]}\n 이월결손금:{valDefit}\n세무상 결손금을 입력하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행)')
				if confirm=='Cancel':isProceed = False;return False   #중단 
			pyautogui.hotkey('ctrl','3') 
			pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter')
			pyautogui.press('f11');time.sleep(3);print('[50-갑]저장하기 3초 소요')  
			utils.semusarang_Print('50-갑.pdf',directory) ;time.sleep(0.5)
			utils.semusarang_Menu_Popup('법인세과세표준및세액조정계산서');pyautogui.press('f12');time.sleep(1.5);pyautogui.press('enter');time.sleep(1.5);pyautogui.press('f11');time.sleep(1.5);pyautogui.press('esc',presses=3,interval=0.5)     
		if "50-을" in preFilelist and flag=='1':
			utils.semusarang_Menu_Popup('자본금과적립금조정명세서');time.sleep(0.25)
			pyautogui.press('f12');time.sleep(0.25);pyautogui.press('enter')
			confirm = pyautogui.confirm('전기이월 유보가 있으니 자적(을) 입력하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행). [아니오:세무조정중단]')
			if confirm=='Cancel':isProceed = False;return False   #중단 
			else:
				pyautogui.press('f11');time.sleep(3);print('[50-갑]저장하기 3초 소요')  
				utils.semusarang_Print('50-을.pdf',directory) 
		if isProceed and not "85.pdf" in filelist   and flag=='1': isProceed = semusarang_Menu_Corptax('지출증명서류수취검토서식','85.pdf',workyear,directory)  
		isGong = False;isGam = False

		print('세액감면판단: 당기순이익이 이월결손금 초과? '+str((member[5]-valDefit)))
		print('소기업? '+ isSmall)
		print('중기업? '+ str(isMiddle))
		print(f'창업감면: {ChangUpDeduct}, 창업감면율 : {ChangUpDeductRate}')
		print(f'특별감면: {SpecialDeduct}, 특별감면율 : {SpecialDeductRate}')
		increaseSangsi = member[32]
		if increaseSangsi=='':increaseSangsi=0
		else:increaseSangsi = int(float(member[32]))  
		print('고용인원증가 : ' + str(increaseSangsi))
		if flag=='1' and ( (member[5]-valDefit)>0  or increaseSangsi>0):
			tmpTxt = f'소기업기준 : {isSmall}\n중기업 : {isMiddle}\n창업감면: {ChangUpDeduct}\n 창업감면율 : {ChangUpDeductRate}\n특별감면: {SpecialDeduct}\n 특별감면율 : {SpecialDeductRate}\n'
			tmpTxt += f"고용증가 : {increaseSangsi}\n\n 확인을 누르면 계속진행됩니다 [아니오:프로그램 중단]"
			confirm = pyautogui.confirm(tmpTxt)  
			if confirm=='Cancel': return False
		if flag=='2':
			tmpTxt = '마감신고 대상(메인소득)입니까? [아니오:프로그램 중단(서브소득)]'
			confirm = pyautogui.confirm(tmpTxt)  
			if confirm=='Cancel': return False
		
		if flag=='1':
			if isProceed and (member[5]-valDefit)>0  and (not (isSmall=="" or isMiddle=="") or SpecialDeductRate>0 or ChangUpDeductRate>0): 
				utils.semusarang_Menu_Popup('법인세과세표준및세액조정계산서');pyautogui.press('f12');time.sleep(1.5);pyautogui.press('enter');time.sleep(1.5);pyautogui.press('f11');time.sleep(1.5);pyautogui.press('esc',presses=3,interval=0.5) 
				if not '48.pdf' in filelist and (SpecialDeductRate>0 or ChangUpDeductRate>0):  
					utils.semusarang_Menu_Popup('소득구분계산서') 
					confirm = pyautogui.confirm('매출종류는 ['+str(saleRecord)+']개이니 주의바랍니다. \n\n소득구분계산서 작성완료 후 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
					if confirm=='OK':  
						pyautogui.press('f11');time.sleep(3);print('[48]저장하기 3초 소요')        
						utils.semusarang_Print('48.pdf',directory) 
				if not '91-조-2-2.pdf' in filelist and ChangUpDeduct=="Y":  
					utils.semusarang_MenuCode_Popup('3065','창업중소기업등에대한감면') ;time.sleep(0.5);pyautogui.press('enter') ;time.sleep(0.5)
					confirm = pyautogui.confirm('창업감면율이 '+str(ChangUpDeductRate)+'%로 예상됩니다. 작성완료 후 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
					if confirm=='OK':  
						pyautogui.press('f11');time.sleep(3);print('[91-조-2-2]저장하기 3초 소요')        
						utils.semusarang_Print('91-조-2-2.pdf',directory)        
					else:pyautogui.press('esc',presses=3,interval=0.25)       
				if not '8-2.pdf' in filelist and (SpecialDeductRate>0 or ChangUpDeductRate>0):  
					utils.semusarang_Menu_Popup('공제감면세액계산서(2)') 
					confirm = pyautogui.confirm(f'감면율이 {SpecialDeduct}/{ChangUpDeductRate}%로 예상됩니다. 작성완료 후 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
					if confirm=='OK':  
						pyautogui.press('f11');time.sleep(3);print('[8-2]저장하기 3초 소요')        
						utils.semusarang_Print('8-2.pdf',directory) 
				isGam=True
			
			print('세액공제판단 - 고용증가인원 : '+str(increaseSangsi))
			if isProceed and ( "91-조-1.pdf" in preFilelist or increaseSangsi>0):
				confirm = pyautogui.confirm('고용관련 세액공제를 진행하시겠습니까? (아니오:다음서식)')
				if confirm=="OK":
					if "91-조-10-8.pdf" in preFilelist and increaseSangsi>0 and member[30]==0: #전년도에 고용증대서식 있거나 올해 고용이 증가한 경우 , 당기 법인세비용=0
						utils.semusarang_MenuCode_Popup('3290','근로자고용현황');pyautogui.press('enter') ;time.sleep(1);pyautogui.press('f12');time.sleep(0.5);  
						confirm = pyautogui.confirm('상시근로자 증감 : '+str(member[32])+'명,근로자고용현황을 작성하고 13x-근로자고용현황.pdf로 저장 후 메뉴 닫고 OK 를 누르세요.(출력진행 안함) [아니오 : 다음 서식으로 이동]')
						if confirm=='OK': pyautogui.press('f11');time.sleep(3);print('[근로자고용현황]저장하기 3초 소요') ;isGong=True
						else:pyautogui.press('esc',presses=4,interval=0.5)
					if "91-조-10-8.pdf" in preFilelist and increaseSangsi<=0  and member[30]==0: #전년도에 고용증대서식 있거나 올해 고용이 감소한 경우
						utils.semusarang_MenuCode_Popup('3290','근로자고용현황');time.sleep(0.5);pyautogui.press('enter');time.sleep(1);pyautogui.press('f12');time.sleep(0.5);  
						confirm = pyautogui.confirm('상시근로자 증감 : '+str(member[32])+'명,전년도 증가인원이 있으니 근로자고용현황을 작성하고 13x-근로자고용현황.pdf로 저장 후 메뉴 닫고 OK 를 누르세요.(출력진행 안함) [아니오 : 다음 서식으로 이동]')
						if confirm=='OK': pyautogui.press('f11');time.sleep(3);print('[근로자고용현황]저장하기 3초 소요')  ;isGong=True
						else:pyautogui.press('esc',presses=4,interval=0.5)      
					if not "91-조-10-8.pdf" in filelist:
						utils.semusarang_MenuCode_Popup('3634','고용증대기업에대한공제세액') 
						# pyautogui.hotkey('ctrl', 'enter');time.sleep(0.5) #메뉴검색
						# pyperclip.copy('고용증대기업에대한공제세액');  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.press('down');time.sleep(0.5) ;pyautogui.press('enter');time.sleep(0.5) 
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('고용증대기업에대한공제세액 조회')     
						confirm = pyautogui.confirm('[91-조-10-8]상시근로자 증감 : '+str(member[32])+'명, 고용증대기업에대한공제세액명세서를 작성하고  OK 를 누르세요.(출력진행) [아니오 : 다음 서식으로 이동]')
						if confirm=='OK': 
							pyautogui.press('f11');time.sleep(3);print('[91-조-10-8]저장하기 3초 소요') 
							utils.semusarang_Print('91-조-10-8.pdf',directory);isGong=True
						else:pyautogui.press('esc',presses=2,interval=0.5)
					if not "91-조-11-5.pdf" in filelist:
						utils.semusarang_MenuCode_Popup('3532','중소기업고용증가인원에대한사회보험료') ;time.sleep(0.5);pyautogui.press('enter') ;time.sleep(0.5)
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('중소기업고용증가인원에대한사회보험료세액공제공제세액계산서 조회')
						confirm = pyautogui.confirm('[91-조-11-5]상시근로자 증감 : '+str(member[32])+'명, 중소기업고용증가인원에대한사회보험료세액공제공제세액계산서를 작성하고  OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
						if confirm=='OK': 
							pyautogui.press('f11');time.sleep(3);print('[91-조-11-5]저장하기 3초 소요') ;isGong=True
							utils.semusarang_Print('91-조-11-5.pdf',directory) 
						else:pyautogui.press('esc',presses=2,interval=0.5)  
			if not "4.pdf" in filelist and (isGong or isGam):
				utils.semusarang_Menu_Popup('법인세과세표준및세액조정계산서');pyautogui.press('f12');time.sleep(1.5);pyautogui.press('enter');time.sleep(1.5);pyautogui.press('f11');time.sleep(1.5);pyautogui.press('esc',presses=3,interval=0.5)     
				utils.semusarang_Menu_Popup('최저한세조정계산서') 
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');time.sleep(3);print('최저한세조정계산서 조회')
				confirm = pyautogui.confirm('[4]최저한세조정계산서를 확인하고  OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK': 
					pyautogui.press('f11');time.sleep(2);print('[4]저장하기 3초 소요') 
					utils.semusarang_Print('4.pdf',directory)  
				else:pyautogui.press('esc',presses=2,interval=0.5)  
			if not '91-조-2.pdf' in filelist and (SpecialDeductRate>0 or ChangUpDeductRate>0) and isGam:
				utils.semusarang_Menu_Popup('세액감면(면제)신청서') ;time.sleep(0.5);pyautogui.press('enter') ;time.sleep(0.5)
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
				confirm = pyautogui.confirm('[91-조-2]세액감면(면제)신청서 [한도충족 감면세액]을 작성완료 후 확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK': 
					pyautogui.press('f11');time.sleep(3);print('[91-조-2]저장하기 3초 소요')        
					utils.semusarang_Print('91-조-2.pdf',directory) 
				isGam = True  
			if not "91-조-3-1.pdf" in filelist and "91-조-3-1.pdf" in preFilelist:
				utils.semusarang_Menu_Popup('일반연구및인력개발비명세서') 
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('일반연구및인력개발비명세서 조회')
				confirm = pyautogui.confirm('[91-조-3-1]일반연구및인력개발비명세서를 작성하고  OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK': 
					pyautogui.press('f11');time.sleep(3);print('[91-조-3-1]저장하기 3초 소요')
					utils.semusarang_Print('91-조-3-1.pdf',directory)
				else:pyautogui.press('esc',presses=2,interval=0.5)       
			if not "8-3.pdf" in filelist and isGong:
				utils.semusarang_Menu_Popup('세액공제조정명세서(3)') 
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('세액공제조정명세서(3) 조회')
				pyautogui.press('pgdn');time.sleep(2);print('세액공제 금액등 확인')
				pyautogui.hotkey('ctrl','3');time.sleep(0.5)
				confirm = pyautogui.confirm('[8-3]세액공제조정명세서(3)를 작성하고  OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK':     
					pyautogui.press('f11');time.sleep(5);print('[8-3]저장하기 3초 소요')
					utils.semusarang_Print('8-3.pdf',directory)  
				else:pyautogui.press('esc',presses=2,interval=0.5)   							
			if not "91-조-1.pdf" in filelist and isGong:
				utils.semusarang_Menu_Popup('세액공제신청서') 
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('세액공제신청서 조회')
				pyautogui.press('pgdn');time.sleep(2);print('세액공제 금액등 확인')
				pyautogui.press('f11');time.sleep(3);print('[91-조-1]저장하기 3초 소요')
				utils.semusarang_Print('91-조-1.pdf',directory) 
			if isProceed and (isGong or isGam):  
				if not "8-갑.pdf" in filelist:
					utils.semusarang_Menu_Popup('공제감면세액및추가납부세액합계표') ;pyautogui.press('enter');time.sleep(0.5);
					pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('공제감면세액및추가납부세액합계표 조회')
					pyautogui.hotkey('ctrl','3');time.sleep(2);pyautogui.hotkey('ctrl','4');time.sleep(2)
					pyautogui.press('f11');time.sleep(3);print('[8-갑]저장하기 3초 소요') 
					utils.semusarang_Print('8-갑.pdf',directory)   
			if isGong: #농특세 계산
				confirm = pyautogui.confirm('농특세 계산을 진행하시겠습니까? (아니오:다음서식)')
				if confirm=="OK":
					if isProceed and not "13.pdf" in filelist  : 
						utils.semusarang_Menu_Popup('농특세과세대상감면세액합계표') 
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세대상감면세액합계표 조회')
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세대상감면세액합계표 조회')
						pyautogui.press('f11');time.sleep(3);print('[농특세과세대상감면세액합계표]저장하기 3초 소요') 
						utils.semusarang_Print('13.pdf',directory) 
					if isProceed and not "2.pdf" in filelist  : 
						utils.semusarang_Menu_Popup('농특세과세표준및세액신고서');time.sleep(0.5);pyautogui.press('down',presses=7,interval=0.5)
						pyautogui.write(str(workyear)+'0331');time.sleep(0.5)
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세표준및세액신고서 조회')
						pyautogui.press('f11');time.sleep(3);print('[농특세과세표준및세액신고서]저장하기 3초 소요') 
						utils.semusarang_Print('2.pdf',directory)        
					if isProceed and not "12.pdf" in filelist  : 
						utils.semusarang_Menu_Popup('농특세과세표준및세액조정계산서') 
						confirm = pyautogui.confirm('확인버튼을 클릭하고  OK 를 누르세요.(출력진행함) [아니오 : 다음 서식으로 이동]')
						if confirm=='OK':         
							pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세표준및세액조정계산서 조회')
							pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세표준및세액조정계산서 조회')
							pyautogui.press('f11');time.sleep(3);print('[농특세과세표준및세액조정계산서]저장하기 3초 소요') 
							utils.semusarang_Print('12.pdf',directory) 
					if isProceed and not "2.pdf" in filelist  : 
						utils.semusarang_Menu_Popup('농특세과세표준및세액신고서');time.sleep(0.5);pyautogui.press('down',presses=7,interval=0.5)
						pyautogui.write(str(workyear)+'0331');time.sleep(0.5)
						pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('농특세과세표준및세액신고서 조회')
						pyautogui.press('f11');time.sleep(3);print('[농특세과세표준및세액신고서]저장하기 3초 소요') 
						utils.semusarang_Print('2.pdf',directory)           
			if isProceed and not "3.pdf" in filelist  : isProceed = semusarang_Menu_Corptax('법인세과세표준및세액조정계산서','3.pdf',workyear,directory)  
			if isProceed and not "1.pdf" in filelist  : 
				if member[5]>0:   
					confirm = pyautogui.confirm('미지급법인세를 계상하고 다시 시도하세요. 작성된 재무제표를 삭제하고 시스템 중단합니다. [아니오]는 신고서 계속작성')
					if confirm=='OK':
						utils.delete_CorpSheet_998_files('1',directory)
						os._exit()#시스템중단

				utils.semusarang_Menu_Popup('법인세과세표준및세액신고서')
				pyautogui.press('f12');time.sleep(3);pyautogui.press('enter');
				pyautogui.press('f3');
				if  member[5]<0:time.sleep(4)
				else:           time.sleep(6)
				pyautogui.press('f3');time.sleep(7)
				utils.semusarang_Print('1.pdf',directory)      
			#지방세
			if isProceed and not "92-지-43-5-갑.pdf" in filelist and member[26]>member[16] and member[5]<=0 and member[15]>0: 
				confirm = pyautogui.confirm('지방소득세특별징수세액명세서를 작성하시겠습니까? [아니오 : 다음 서식으로 이동]')
				if confirm=='OK':     
					isProceed = semusarang_Menu_Corptax('지방소득세특별징수세액명세서','92-지-43-5-갑.pdf',workyear,directory)
			if isProceed and not "92-지-43-2.pdf" in filelist : #isProceed = semusarang_Menu_Corptax('지방소득세과세표준및세액조정계','92-지-43-2.pdf',workyear,directory)
				utils.semusarang_Menu_Popup('지방소득세과세표준및세액조정계')
				pyautogui.press('enter');time.sleep(1)
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')
				pyautogui.press('f11');time.sleep(3);print('[92-지-43-2]저장하기 3초 소요')
				utils.semusarang_Print('92-지-43-2.pdf',directory) 
			if isProceed and not "92-지-43.pdf" in filelist :
				utils.semusarang_Menu_Popup('지방소득세과세표준및세액신고서')
				pyautogui.press('f12');time.sleep(0.5);pyautogui.press('enter');print('조회')   
				pyautogui.press('f6');time.sleep(0.5);pyautogui.press('enter');pyautogui.write('1')
				pyautogui.press('enter',presses=2,interval=0.5);pyautogui.write('0');pyautogui.press('enter');time.sleep(0.25);print('종업원수 세팅')  
				semusarang_LocalTax_confirm =  pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_LocalTax_confirm.png')
				if semusarang_LocalTax_confirm:  pyautogui.click(semusarang_LocalTax_confirm);time.sleep(0.25);pyautogui.press('enter');time.sleep(0.25)
				pyautogui.press('f3',presses=2,interval=3);time.sleep(1)
				pyautogui.press('f9');time.sleep(1)
				semusarang_LocalTax_confirm2 =  pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_LocalTax_confirm2.png')
				if semusarang_LocalTax_confirm2:  
					pyautogui.click(semusarang_LocalTax_confirm2);time.sleep(0.25)
					utils.semusarang_Print('92-지-43.pdf',directory)
				else:
					confirm = pyautogui.confirm('확인버튼을 클릭하고 메뉴를 닫지 않은 상태에서 OK 를 누르세요.(출력진행함)')
					if confirm=='Cancel':isProceed = False;return False   #중단    
					else:utils.semusarang_Print('93-지-43.pdf',directory)  
		elif flag=='2': 
			if isProceed and (member[5]-valDefit)>0  and (not (isSmall=="" or isMiddle=="") or (SpecialDeductRate>0 or ChangUpDeductRate>0)): 
				confirm = pyautogui.confirm(f'세액감면율 {SpecialDeductRate}/{ChangUpDeductRate}%로 예상됩니다. 세액감면서식을 작성하고 예를 누르세요. [아니오]프로그램 중단')
				if confirm=='OK': isProceed=True
				else            : isProceed=False      
			if increaseSangsi>0:
				confirm = pyautogui.confirm('고용인원이 '+str(increaseSangsi)+'명 증가하였습니다. 고용증대서식을 작성하고 예를 누르세요. [아니오]프로그램 중단')
				if confirm=='OK': isProceed=True
				else            : isProceed=False
			if isProceed and not "2.pdf" in filelist :
				pyautogui.hotkey('ctrl', 'enter');time.sleep(0.5) #메뉴검색
				pyperclip.copy('소득 · 세액공제신고서');  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5); pyautogui.press('down');time.sleep(0.5) ;
				pyautogui.hotkey('ctrl', 'f4');time.sleep(0.5);pyautogui.press('enter');print('직전년도 소득 · 세액공제신고서 조회')     
				confirm = pyautogui.confirm('소득 · 세액공제신고서를 작성하고  OK 를 누르세요.(출력진행) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK': 
					pyautogui.press('f11');time.sleep(3);print('저장하기 3초 소요') 
					utils.semusarang_Print('2.pdf',directory)
				else:pyautogui.press('esc',presses=2,interval=0.5)    
			if isProceed and not "1.pdf" in filelist :
				utils.semusarang_Menu_Popup('종합소득세신고서')
				pyautogui.write('2');time.sleep(0.3);pyautogui.press('tab');time.sleep(0.3);pyautogui.write('40');time.sleep(0.3);pyautogui.press('down');time.sleep(0.3)
				pyautogui.write(memuser.duzon_id);time.sleep(0.3);pyautogui.press('enter');time.sleep(0.3)
				pyautogui.hotkey('ctrl','4');time.sleep(0.3);pyautogui.press('f12');time.sleep(1);pyautogui.press('enter');time.sleep(0.3)
				pyautogui.hotkey('ctrl','8')
				confirm = pyautogui.confirm('종합소득세신고서를 작성하고  OK 를 누르세요.(출력진행) [아니오 : 다음 서식으로 이동]')
				if confirm=='OK': 
					pyautogui.press('f3');time.sleep(3);pyautogui.press('f3');print('저장하기 3초 소요') ;time.sleep(3)
					utils.semusarang_Print('1.pdf',directory)
				else:pyautogui.press('esc',presses=2,interval=0.5)    
			if isProceed:  
				ElecIssue.SS_MakeElecFile('income',memuser,'mmStart','mmEnd',str(workyear),'kwaseyuhyung',1)
				confirm = pyautogui.confirm('전자신고를 진행하시겠습니까 [아니오 : 중단]')
				if confirm=='OK':  SS_ElecIssue('income',memuser.seq_no.replace("-",""),workyear,memuser.seq_no,1)       

			sql = "merge tbl_corporate2  as A Using (select '"+memuser.seq_no+"' as seq_no , '"+workyear+"' as work_yy) as B "
			sql += "On A.seq_no = B.seq_no and A.work_yy = B.work_yy   "
			sql += "WHEN Matched Then  	Update set YN_6='1'"
			sql += "	When Not Matched Then  "
			sql += "	INSERT 	values('"+memuser.seq_no+"','"+workyear+"',0,0,0,0,0,1,0,0,0, '',0, '', 0, 0, 0);"
			print(sql)
			cursor = connection.cursor()
			cursor.execute(sql)
			cursor.commit()
			print(f'{memuser.biz_name} 신고서 저장완료 마감표시 디비저장성공')	
		return 1
class ElecIssue:

	def SS_MakeElecFile(flag,member,mmStart,mmEnd,KwaseKikan,KwaseyuHyung,isJungKi,semusarangID):
		seq_no = member[0]
		DuzonID = member[4]
		if flag[:7]=='wonchun' :seq_no = member[2];DuzonID = member[0]
		if flag!='income-wetax': utils.delete_all_files("c:\\abc") #f4 누른 후 암호화 방지를 위해 모든 파일을 지운다
		semusarang_elec_ID = SemusarangID_Check(flag,seq_no,mmStart,mmEnd,KwaseKikan,KwaseyuHyung,semusarangID)
		if flag=='vat':    
			utils.semusarang_MenuCode_Popup('1099','전자신고(부가세)')
			#전자신고 아이디 세팅
			pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('up',presses=2,interval=0.1);time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)			
			pyautogui.press('right');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.hotkey('ctrl','2');time.sleep(0.5)
			#전자신고파일 제작
			pyautogui.write(str(mmStart));
			if len(mmStart)!=2: pyautogui.press('enter');
			time.sleep(0.5);pyautogui.write(str(mmEnd))
			if len(mmEnd)!=2: pyautogui.press('enter');
			# pyautogui.press('enter');time.sleep(0.5);#엔터하지 않아도 넘어감
			if isJungKi in {1,2}:       pyautogui.write('1');time.sleep(0.5);#정기신고
			elif isJungKi==4:           pyautogui.write('3');time.sleep(0.5);#기한후신고
			pyautogui.write('1');time.sleep(0.5);#신고인구분
			pyautogui.write('1');time.sleep(0.5);#담당자
			pyautogui.press('enter',presses=4,interval=0.5);time.sleep(0.5);#회사구분
			# pyautogui.write(str(DuzonID));  time.sleep(1)  
			# if len(str(DuzonID))<4:pyautogui.press('enter');  
			# time.sleep(0.5)#필수  
			# # pyautogui.press('f2');time.sleep(0.5);#회사코드
			# pyautogui.write(str(DuzonID));  time.sleep(1)  
			# if len(str(DuzonID))<4:pyautogui.press('enter');  
			time.sleep(1.5)#필수      
			# isMagam = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_Magam_NoCompany.png', confidence=0.5) 
			# if isMagam:
			# 	print(f'{seq_no} : 마감된 회시가 없습니다.')
			# 	return 0
			pyautogui.press('f4');time.sleep(0.5);#제작
			pyautogui.press('esc',presses=4,interval=0.5);time.sleep(0.5);#메뉴종료
		elif flag=='corp' or flag=='income':
			if flag=='corp':			utils.semusarang_MenuCode_Popup('3208','전자신고(정기분)')  
			else: 								utils.semusarang_MenuCode_Popup('3410','전자신고(정기분)')  
			#전자신고 아이디 세팅
			print(f"semusarang_elec_ID 값: {semusarang_elec_ID} / 타입: {type(semusarang_elec_ID)}")
			pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('up',presses=2,interval=0.5);time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)			
			pyautogui.press('right');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.hotkey('ctrl','2');time.sleep(0.5)
			#전자신고파일 제작      
			if flag=='income':pyautogui.press('enter',presses=4,interval=0.3);
			elif flag=='corp':pyautogui.press('enter',presses=3,interval=0.3);
			pyautogui.write(str(DuzonID));time.sleep(0.3);
			if len(str(DuzonID))<4: pyautogui.press('enter');time.sleep(0.3)
			pyautogui.write(str(DuzonID));time.sleep(0.3);pyautogui.press('enter');time.sleep(0.3)
			pyautogui.press('f4');time.sleep(1);pyautogui.press('esc',presses=4,interval=0.3);time.sleep(1)  
		elif flag=='corp-wetax' or flag=='income-wetax':
			
			#전자신고파일 제작      
			if flag=='income-wetax':
				utils.semusarang_MenuCode_Popup('3642','개인지방소득세(종합소득)신고서')  
				pyautogui.press('f12');time.sleep(0.5)
				pyautogui.press('y');time.sleep(0.5)
				pyautogui.press('f3');time.sleep(1)
				pyautogui.press('f3');time.sleep(0.5)
				pyautogui.press('esc');time.sleep(0.5)
				utils.semusarang_MenuCode_Popup('3646','지방소득세전자신고')  
				pyautogui.press('enter',presses=3,interval=0.3);
			elif flag=='corp-wetax':
				utils.semusarang_MenuCode_Popup('3557','지방소득세전자신고')  
				pyautogui.press('enter',presses=3,interval=0.3);
			pyautogui.write(str(DuzonID));time.sleep(0.5);
			if len(str(DuzonID))<4: pyautogui.press('enter');time.sleep(0.5)
			pyautogui.write(str(DuzonID));time.sleep(0.3);pyautogui.press('enter');time.sleep(0.3)
			pyautogui.press('f4');time.sleep(1);pyautogui.press('enter',presses=4,interval=0.3);time.sleep(1)  		
			pyautogui.press('esc',presses=4,interval=0.3);time.sleep(0.5)  	
		elif flag=='wonchun':
			if "귀속지급차이" in member[6]:
				pay_mm = int(mmEnd)+1
				if pay_mm==13:pay_mm = 1
				if pay_mm<10 : 	mmEnd = "0" + str(pay_mm)
				else:						mmEnd = str(pay_mm)				
			pyautogui.hotkey('ctrl', 'enter');time.sleep(0.5) #메뉴검색
			pyperclip.copy('원천세전자신고');  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5) ;pyautogui.press('enter')  ;time.sleep(1);pyautogui.press('enter')  ;time.sleep(0.5)
			pyautogui.press('enter',presses=2,interval=0.3);time.sleep(0.3)
			#전자신고 아이디 세팅
			pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('up',presses=2,interval=0.1);time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)
			pyautogui.press('right');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.hotkey('ctrl','2');time.sleep(0.5)
			#전자신고파일 제작
			if KwaseyuHyung=="N":#반기신고 아닌 경우
				pyautogui.write(mmEnd);time.sleep(0.3);pyautogui.press('enter');pyautogui.write(mmEnd);time.sleep(0.3)
			else:
				pyautogui.write(f'0{str(int(mmEnd)-5)}');time.sleep(0.3);pyautogui.press('enter');pyautogui.write(mmEnd);time.sleep(0.3)
			pyautogui.write('1');pyautogui.press('enter',presses=6,interval=0.3);time.sleep(1.5)
			
			pyautogui.press('f4');time.sleep(2.5);#제작
			pyautogui.press('esc',presses=4,interval=0.5);time.sleep(0.5);#메뉴종료 
			SS_ElecIssue('wonchun',seq_no,mmStart,mmEnd,isJungKi)          
		elif flag=='wonchun-wetax':
			if "귀속지급차이" in member[6]:
				pay_mm = int(mmEnd)+1
				if pay_mm==13:pay_mm = 1
				if pay_mm<10 : 	mmEnd = "0" + str(pay_mm)
				else:						mmEnd = str(pay_mm)	

			folder_path = "C:\\ABC\\"  # 삭제하려는 파일이 있는 폴더 경로 => 바구지 말것
			file_list = os.listdir(folder_path)
			for filename1 in file_list:
					if filename1.endswith(".1"):
							file_path = os.path.join(folder_path, filename1)
							try:
									os.remove(file_path)
									print(f"Deleted: {file_path}")
							except Exception as e:
									print(f"Error deleting {file_path}: {e}")    
			pyautogui.hotkey('ctrl', 'enter');time.sleep(0.5) #메뉴검색
			pyperclip.copy('지방소득세전자신고');  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.press('enter')  ;time.sleep(1);pyautogui.press('enter')  ;time.sleep(0.5)
			pyautogui.press('enter',presses=2,interval=0.3);time.sleep(0.3)
			if KwaseyuHyung=="N":#반기신고 아닌 경우
				pyautogui.write(mmEnd);time.sleep(0.3);pyautogui.press('enter');pyautogui.write(mmEnd);time.sleep(0.3)
			else:
				pyautogui.write(f'0{str(int(mmEnd)-5)}');time.sleep(0.3);pyautogui.press('enter');pyautogui.write(mmEnd);time.sleep(0.3)				
			pyautogui.write('1');print('회사구분')
			if KwaseyuHyung=="N":#반기신고 아닌 경우
				pyautogui.press('enter',presses=4,interval=0.3);time.sleep(0.5)
			else:
				pyautogui.press('enter',presses=3,interval=0.1);time.sleep(0.1);pyautogui.write('1');print('매월0/반기1')
			pyautogui.press('f2');time.sleep(2);#폴더선택
			pyautogui.hotkey('alt','d');    time.sleep(0.25)
			pyautogui.write('C:\\ABC');time.sleep(0.3);pyautogui.press('enter');time.sleep(0.5);
			pyautogui.press('tab',presses=7,interval=0.3); pyautogui.press('enter');time.sleep(0.5);pyautogui.press('enter');time.sleep(1.5)
			pyautogui.press('f4');time.sleep(1.5);print('지방세 전자신고파일 제작')
			pyautogui.press('enter',presses=2,interval=0.5);time.sleep(0.5)
			pyautogui.press('esc',presses=3,interval=0.3);time.sleep(0.5);#메뉴종료 
			SS_ElecIssue('wonchun-wetax',seq_no,KwaseKikan,mmStart,isJungKi)  


	#간이지급명세서
	def action_Kani(htxLoginID,filename,cols):
		#  신고결과 엑셀파일로 전자신고결과를 추출하는 방식


		# 전자신고파일에서 건수/금액을 추출하는 방식
		wc2 = cols[4].text  # 자료명
		wc3 = cols[5].text[:12]  # 사업자번호 (처음 12자리)
		wc4 = cols[6].text.replace("'", "")  # 상호 (작은따옴표 제거)
		wc5 = cols[7].text[:7]  # 과세기간
		wc7 = '홈택스(전자파일)'#cols[8].text  # 신고구분 - 홈택스(전자파일)
		wc8 = htxLoginID  # 접수자
		wc9 = cols[10].text  # 제출건수
		wc10 = cols[11].text.replace(",", "")  # 총금액 (쉼표 제거)
		wc11 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 접수일시
		wc12 = cols[1].text  # 접수번호

		elecfile = open(filename,'r')  
		while True:
			line = elecfile.readline()
			if not line:   break
			if line[:1] == "B":     #A레코드
				wc9 = str(int(utils.unicode_slice(line,172,177)))
				wc10 = str(int(utils.unicode_slice(line,178,192)))
		elecfile.close()  		

		work_mm=wc5[-2:];work_yy=wc5[2:4];KSYD=""
		if work_mm == '01':          KSYD = "Jan-"+work_yy
		elif work_mm == '02':          KSYD = "Feb-"+work_yy
		elif work_mm == '03':          KSYD = "Mar-"+work_yy
		elif work_mm == '04':          KSYD = "Apr-"+work_yy
		elif work_mm == '05':          KSYD = "May-"+work_yy
		elif work_mm == '06':          KSYD = "Jun-"+work_yy
		elif work_mm == '07':          KSYD = "Jul-"+work_yy
		elif work_mm == '08':          KSYD = "Aug-"+work_yy
		elif work_mm == '09':          KSYD = "Sep-"+work_yy
		elif work_mm == '10':          KSYD = "Oct-"+work_yy
		elif work_mm == '11':          KSYD = "Nov-"+work_yy
		elif work_mm == '12':          KSYD = "Dec-"+work_yy
		if KSYD!="":
			cursor = connection.cursor()
			strsel = "SELECT * FROM 지급조서간이소득 WHERE 과세년도='"+KSYD+"' AND 신고서종류='"+wc2+"' AND 사업자번호='"+wc3+"'";print(strsel)
			cursor.execute(strsel)
			result = cursor.fetchone()
			if result is not None:
					sqldel = "DELETE FROM 지급조서간이소득 WHERE 과세년도='"+KSYD+"' AND 신고서종류='"+wc2+"' AND 사업자번호='"+wc3+"'";print(sqldel)
					cursor.execute(sqldel)
			sqlins = "INSERT INTO 지급조서간이소득 VALUES ('"+wc2+"','"+wc3+"','"+wc4+"','"+KSYD+"','"+wc7+"','"+wc8+"','"+wc9+"','"+wc10+"','"+wc11+"','"+wc12+"',  getdate())";print(sqlins)
			cursor.execute(sqlins)    
			print(wc2 +" "+ wc8 +" "+ " 전자신고결과 저장완료")
		return 1

	#전자신고
	def action_ElecIssue(driver,flag,filename,cols):
		cursor = connection.cursor()
		elecfile = open(filename,'r')  
		if flag=='vat':
			wcKwase = cols[2].text.replace("월","기")  # 과세기간
			wc1 = wcKwase[:5]
			wc2 = wcKwase[-2:-1]
			if wc2 == "7" : wc2 = "2"
			wcKwase = wc1 + " " + wc2 + "기"      
			wcCorpGB = cols[3].text  # 신고서종류
			wcSingoGB = cols[4].text  # 신고구분
			wcChojung = cols[5].text  # 신고유형
			wcSangho = cols[6].text.replace("\'","")  # 상호
			wcBizNo = cols[7].text  # 사번
			wcJupsuGB = cols[8].text  # 접수서류
			wcIssueT = cols[9].text  # 신고시각
			wcJubsuNum = cols[10].text  # 접수번호
			issueID = cols[30].text  # 접수번호

			wcCorpGB_txt=""
			if wcCorpGB == "부가가치세 확정(간이)신고서":                     wcCorpGB_txt = "C03"
			elif wcCorpGB == "부가가치세 확정(일반) 4,10월조기 신고서":        wcCorpGB_txt = "C05"
			elif wcCorpGB == "부가가치세 확정(일반) 5,11월조기 신고서":        wcCorpGB_txt = "C06"
			elif wcCorpGB == "부가가치세 확정(일반) 신고서":                  wcCorpGB_txt = "C07"
			elif wcCorpGB == "부가가치세 예정(간이) 신고서":                  wcCorpGB_txt = "C13"
			elif wcCorpGB == "부가가치세 예정(일반) 1,7월조기 신고서":         wcCorpGB_txt = "C15"
			elif wcCorpGB == "부가가치세 예정(일반) 2,8월조기 신고서":         wcCorpGB_txt = "C16"
			elif wcCorpGB == "부가가치세 예정(일반) 신고서":                  wcCorpGB_txt = "C17"	


			GB_KA = "01,02,05,10,12,13,14,50,51,52"
			GB_NA = "15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,40,41,45,55,60,61,62,63,64,65,66,67"
			GB_DA = "70,71,72,73,74,80,85,90,92,93,94,95"
			record_11 = record_17 = CardSaleSheet = CardCost1 = CardCost2 = CardCost3 = CardCost4 = PretendPurchase = PretendPurchase2 = PaperSalesTaxInvoiceSum = ""
			PaperSalesTaxInvoice = PaperExpTaxInvoiceSum = BullGongSheet =PaperExpTaxInvoice= ""
			inspect_elec = 0
			inspect_labor = 0
			inspect_issue = "1#" # 전자신고 파일 업로드시 일단 스마일			
			
			while True:
				sr = elecfile.readline(); 
				if not sr:   break
				if sr.startswith("11I") or sr.startswith("12I"):				record_11=sr
				elif sr.startswith("17I103200"):												record_17 = sr
				elif sr.startswith("17I103400"):												CardSaleSheet = sr
				elif sr.startswith("DL"):
						if sr[18] == '1':								CardCost1 = sr[0:140]
						elif sr[18] == '2':							CardCost2 = sr[0:140]
						elif sr[18] == '3':							CardCost3 = sr[0:140]
						elif sr[18] == '4':							CardCost4 = sr[0:140]
				elif sr.startswith("14I103200230"):					PretendPurchase = sr
				elif sr.startswith("14I103200270"):					PretendPurchase2 = sr
				elif sr.startswith("18I103300"):						BullGongSheet = BullGongSheet + sr[9:48]
				elif sr.startswith("1" + record_11[9:19]):					PaperSalesTaxInvoice = PaperSalesTaxInvoice + sr
				elif sr.startswith("2" + record_11[9:19]):					PaperExpTaxInvoice = PaperExpTaxInvoice + sr
				elif sr.startswith("3" + record_11[9:19]):					PaperSalesTaxInvoiceSum = PaperSalesTaxInvoiceSum + sr					
				elif sr.startswith("4" + record_11[9:19]):					PaperExpTaxInvoiceSum = PaperExpTaxInvoiceSum + sr				

			work_yy = record_11[28:32]; print(work_yy)
			txt_Ki = record_11[32:34].replace("0", ""); print(txt_Ki)
			biz_no = f"{record_11[9:12]}-{record_11[12:14]}-{record_11[14:19]}"; print(biz_no)

			strsql = f"select biz_type from mem_user where biz_no='{biz_no}'"
			rs1 = cursor.execute(strsql)
			record = rs1.fetchone()
			biz_type = record[0] if record else None
		
			kwasekikan = f"{work_yy}년 {txt_Ki}기"; print(kwasekikan)
			UpjongCode = utils.unicode_slice(record_11,422,429)

			print(f"UpjongCode: {UpjongCode}")

			DBname = utils.unicode_slice(record_11,22,24); print(DBname)
			if DBname == "41":					DBname = "부가가치세전자신고"

			wcCorpGB = utils.unicode_slice(record_11,35,37); print(wcCorpGB)
			work_qt = 0
			if wcCorpGB == "C03":
					work_qt = 4 if txt_Ki == '2' else None
			elif wcCorpGB == "C05":
					work_qt = 4 if txt_Ki == '2' else 2
			elif wcCorpGB == "C06":
					work_qt = 4 if txt_Ki == '2' else 2
			elif wcCorpGB == "C07":
					work_qt = 4 if txt_Ki == '2' else 2
			elif wcCorpGB == "C13":
					work_qt = 3 if txt_Ki == '2' else 1
			elif wcCorpGB == "C15":
					work_qt = 3 if txt_Ki == '2' else 1
			elif wcCorpGB == "C16":
					work_qt = 3 if txt_Ki == '2' else 1
			elif wcCorpGB == "C17":
					work_qt = 3 if txt_Ki == '2' else 1
			print('work_qt:'+str(work_qt))
			length_17 = 0
			mainIssue_17 = [None] * 86  # 인덱스 1부터 사용하기 위해 크기 86의 리스트 생성

			for m in range(1, 86):
					if m == 1 or m == 74:
							mainIssue_17[m] = record_17[length_17:length_17 + 2]
							length_17 += 2
					elif m in [3, 7, 8, 12, 24, 25, 26, 44, 56, 59, 60, 67, 69, 71, 72, 73, 82, 85]:
							mainIssue_17[m] = record_17[length_17:length_17 + 15]
							length_17 += 15
					elif m in [75, 80]:
							mainIssue_17[m] = record_17[length_17:length_17 + 3]
							length_17 += 3
					elif m == 76:
							mainIssue_17[m] = record_17[length_17:length_17 + 20]
							length_17 += 20
					elif m == 77:
							mainIssue_17[m] = record_17[length_17:length_17 + 9]
							length_17 += 9
					elif m == 78:
							mainIssue_17[m] = record_17[length_17:length_17 + 30]		#MidUnion(record_17, length_17, 30)
							length_17 += 30
					elif m == 79:
							mainIssue_17[m] = record_17[length_17:length_17 + 8]
							length_17 += 8
					elif m in [81, 83, 84]:
							mainIssue_17[m] = record_17[length_17:length_17 + 1]
							length_17 += 1
					elif m == 2:
							mainIssue_17[m] = record_17[length_17:length_17 + 7]
							length_17 += 7
					else:
							mainIssue_17[m] = record_17[length_17:length_17 + 13]
							length_17 += 13
			# KSPJ = KKKJ = SJNB = MCSK = MISK = KTMC = KTMI = MSMC = MSMI = YSMC = 0
			# if mainIssue_17 is not None:
			# 	KSPJ = int(mainIssue_17[24])
			# 	KKKJ = int(mainIssue_17[61]) + int(mainIssue_17[62]) + int(mainIssue_17[63]) - int(mainIssue_17[66])
			# 	SJNB = int(mainIssue_17[67])
			# 	MCSK = int(mainIssue_17[3]) + int(mainIssue_17[15])
			# 	MISK = int(mainIssue_17[26]) + int(mainIssue_17[28]) + int(mainIssue_17[32])
			# 	KTMC = int(mainIssue_17[7]) + int(mainIssue_17[9]) + int(mainIssue_17[17])
			# 	KTMI = int(mainIssue_17[40]) + int(mainIssue_17[38]) + int(mainIssue_17[34])
			# 	MSMC = int(mainIssue_17[72])
			# 	MSMI = int(mainIssue_17[73])
			# 	YSMC = int(mainIssue_17[11]) + int(mainIssue_17[12]) + int(mainIssue_17[19]) + int(mainIssue_17[20])


			strsql = "Merge 부가가치세전자신고3 as A Using (select '"+wcBizNo+"' as biz_no,'"+wcKwase+"' as wcKwase,'"+wcCorpGB_txt+"' as wcCorpGB_txt) as B "
			strsql += "On A.과세기간=B.wcKwase  and A.사업자등록번호=B.biz_no and A.과세유형=B.wcCorpGB_txt "
			strsql += " when matched then update set "
			strsql += "  신고구분 = '" + wcSingoGB + "'"
			strsql += " ,환급구분 = '" + wcChojung + "'"
			strsql += " ,상호 = '" + wcSangho + "'"
			strsql += " ,접수여부 = '" + wcJupsuGB + "'"
			strsql += " ,신고번호 = '" + wcJubsuNum + "'"
			strsql += " ,신고시각 = '" + wcIssueT + "'"    
			strsql += " ,  매출과세세금계산서발급금액 = '" + mainIssue_17[3] + "'"  
			strsql += " ,  매출과세세금계산서발급세액 = '" + mainIssue_17[4] + "'"  
			strsql += " ,  매출과세매입자발행세금계산서금액 = '" + mainIssue_17[5] + "'"  
			strsql += " ,  매출과세매입자발행세금계산서세액 = '" + mainIssue_17[6] + "'"  
			strsql += " ,  매출과세카드현금발행금액 = '" + mainIssue_17[7] + "'"  
			strsql += " ,  매출과세카드현금발행세액 = '" + mainIssue_17[8] + "'"  
			strsql += " ,  매출과세기타금액 = '" + mainIssue_17[9] + "'"  
			strsql += " ,  매출과세기타세액 = '" + mainIssue_17[10] + "'"  
			strsql += " ,  매출영세율세금계산서발급금액 = '" + mainIssue_17[11] + "'"  
			strsql += " ,  매출영세율기타금액 = '" + mainIssue_17[12] + "'"  
			strsql += " ,  매출예정누락합계금액 = '" + mainIssue_17[13] + "'"  
			strsql += " ,  매출예정누락합계세액 = '" + mainIssue_17[14] + "'"  
			strsql += " ,  예정누락매출세금계산서금액 = '" + mainIssue_17[15] + "'"  
			strsql += " ,  예정누락매출세금계산서세액 = '" + mainIssue_17[16] + "'"  
			strsql += " ,  예정누락매출과세기타금액 = '" + mainIssue_17[17] + "'"  
			strsql += " ,  예정누락매출과세기타세액 = '" + mainIssue_17[18] + "'"  
			strsql += " ,  예정누락매출영세율세금계산서금액 = '" + mainIssue_17[19] + "'"  
			strsql += " ,  예정누락매출영세율기타금액 = '" + mainIssue_17[20] + "'"  
			strsql += " ,  예정누락매출명세합계금액 = '" + mainIssue_17[21] + "'"  
			strsql += " ,  예정누락매출명세합계세액 = '" + mainIssue_17[22] + "'"  
			strsql += " ,  매출대손세액가감세액 = '" + mainIssue_17[23] + "'"  
			strsql += " ,  과세표준금액 = '" + mainIssue_17[24] + "'"  
			strsql += " ,  산출세액 = '" + mainIssue_17[25] + "'"  
			strsql += " ,  매입세금계산서수취일반금액 = '" + mainIssue_17[26] + "'"  
			strsql += " ,  매입세금계산서수취일반세액 = '" + mainIssue_17[27] + "'"  
			strsql += " ,  매입세금계산서수취고정자산금액 = '" + mainIssue_17[28] + "'"  
			strsql += " ,  매입세금계산서수취고정자산세액 = '" + mainIssue_17[29] + "'"  
			strsql += " ,  매입예정누락합계금액 = '" + mainIssue_17[30] + "'"  
			strsql += " ,  매입예정누락합계세액 = '" + mainIssue_17[31] + "'"  
			strsql += " ,  예정누락매입신고세금계산서금액 = '" + mainIssue_17[32] + "'"  
			strsql += " ,  예정누락매입신고세금계산서세액 = '" + mainIssue_17[33] + "'"  
			strsql += " ,  예정누락매입기타공제금액 = '" + mainIssue_17[34] + "'"  
			strsql += " ,  예정누락매입기타공제세액 = '" + mainIssue_17[35] + "'"  
			strsql += " ,  예정누락매입명세합계금액 = '" + mainIssue_17[36] + "'"  
			strsql += " ,  예정누락매입명세합계세액 = '" + mainIssue_17[37] + "'"  
			strsql += " ,  매입자발행세금계산서매입금액 = '" + mainIssue_17[38] + "'"  
			strsql += " ,  매입자발행세금계산서매입세액 = '" + mainIssue_17[39] + "'"  
			strsql += " ,  매입기타공제매입금액 = '" + mainIssue_17[40] + "'"  
			strsql += " ,  매입기타공제매입세액 = '" + mainIssue_17[41] + "'"  
			strsql += " ,  그밖의공제매입명세합계금액 = '" + mainIssue_17[42] + "'"  
			strsql += " ,  그밖의공제매입명세합계세액 = '" + mainIssue_17[43] + "'"  
			strsql += " ,  매입세액합계금액 = '" + mainIssue_17[44] + "'"  
			strsql += " ,  매입세액합계세액 = '" + mainIssue_17[45] + "'"  
			strsql += " ,  공제받지못할매입합계금액 = '" + mainIssue_17[46] + "'"  
			strsql += " ,  공제받지못할매입합계세액 = '" + mainIssue_17[47] + "'"  
			strsql += " ,  공제받지못할매입금액 = '" + mainIssue_17[48] + "'"  
			strsql += " ,  공제받지못할매입세액 = '" + mainIssue_17[49] + "'"  
			strsql += " ,  공제받지못할공통매입면세사업금액 = '" + mainIssue_17[50] + "'"  
			strsql += " ,  공제받지못할공통매입면세사업세액 = '" + mainIssue_17[51] + "'"  
			strsql += " ,  공제받지못할대손처분금액 = '" + mainIssue_17[52] + "'"  
			strsql += " ,  공제받지못할대손처분세액 = '" + mainIssue_17[53] + "'"  
			strsql += " ,  공제받지못할매입명세합계금액 = '" + mainIssue_17[54] + "'"  
			strsql += " ,  공제받지못할매입명세합계세액 = '" + mainIssue_17[55] + "'"  
			strsql += " ,  차감합계금액 = '" + mainIssue_17[56] + "'"  
			strsql += " ,  차감합계세액 = '" + mainIssue_17[57] + "'"  
			strsql += " ,  납부환급세액 = '" + mainIssue_17[58] + "'"  
			strsql += " ,  그밖의경감공제세액 = '" + mainIssue_17[59] + "'"  
			strsql += " ,  그밖의경감공제명세합계세액 = '" + mainIssue_17[60] + "'"  
			strsql += " ,  경감공제합계세액 = '" + mainIssue_17[61] + "'"  
			strsql += " ,  예정신고미환급세액 = '" + mainIssue_17[62] + "'"  
			strsql += " ,  예정고지세액 = '" + mainIssue_17[63] + "'"  
			strsql += " ,  사업양수자의대리납부기납부세액 = '" + mainIssue_17[64] + "'"  
			strsql += " ,  매입자납부특례기납부세액 = '" + mainIssue_17[65] + "'"  
			strsql += " ,  가산세액계 = '" + mainIssue_17[66] + "'"  
			strsql += " ,  차감납부할세액 = '" + mainIssue_17[67] + "'"  
			strsql += " ,  과세표준명세수입금액제외금액 = '" + mainIssue_17[68] + "'"  
			strsql += " ,  과세표준명세합계수입금액 = '" + mainIssue_17[69] + "'"  
			strsql += " ,  면세사업수입금액제외금액 = '" + mainIssue_17[70] + "'"  
			strsql += " ,  면세사업합계수입금액 = '" + mainIssue_17[71] + "'"  
			strsql += " ,  계산서교부금액 = '" + mainIssue_17[72] + "'"  
			strsql += " ,  계산서수취금액 = '" + mainIssue_17[73] + "'"  


			strsql += " ,  환급구분코드 = '" + mainIssue_17[74] + "'"  
			strsql += " ,  은행코드 = '" + mainIssue_17[75] + "'"  
			strsql += " ,  계좌번호 = '" + mainIssue_17[76] + "'"  
			strsql += " ,  총괄납부승인번호 = '" + mainIssue_17[77] + "'"  
			strsql += " ,  은행지점명 = '" + mainIssue_17[78] + "'"  
			strsql += " ,  폐업일자 = '" + mainIssue_17[79] + "'"  
			strsql += " ,  폐업사유 = '" + mainIssue_17[80] + "'"  
			strsql += " ,  기한후여부 = '" + mainIssue_17[81] + "'"  
			strsql += " ,  실차감납부할세액 = '" + mainIssue_17[82] + "'"  
			strsql += " ,  일반과세자구분 = '" + mainIssue_17[83] + "'"  
			strsql += " ,  조기환급취소구분 = '" + mainIssue_17[84] + "'"  
			strsql += " ,  수출기업수입납부유예 = '" + mainIssue_17[85] + "'"  
			strsql += " ,  업종코드 = '" + UpjongCode + "'"  
			strsql += " ,  전자외매출세금계산서 = '" + PaperSalesTaxInvoice + "'"  
			strsql += " ,  전자외매출세금계산서합계 = '" + PaperSalesTaxInvoiceSum + "'"  
			strsql += " ,  전자외매입세금계산서 = '" + str(PaperExpTaxInvoice) + "'"  
			strsql += " ,  전자외매입세금계산서합계 = '" + PaperExpTaxInvoiceSum + "'"  
			strsql += " ,  inspect_issue = '" + inspect_issue + "'"  
			strsql += " ,  inspect_elec = '" + str(inspect_elec) + "'"  
			strsql += " ,  inspect_labor = '" + str(inspect_labor) + "'"  
			strsql += " ,  신용카드발행집계표 = '" + CardSaleSheet + "'"  
			strsql += " ,  신용카드수취기타카드 = '" + CardCost1 + "'"  
			strsql += " ,  신용카드수취현금영수증 = '" + CardCost2 + "'"  
			strsql += " ,  신용카드수취화물복지 = '" + CardCost3 + "'"  
			strsql += " ,  신용카드수취사업용카드 = '" + CardCost4 + "'"  
			strsql += " ,  공제받지못할매입세액명세 = '" + str(BullGongSheet) + "'"  
			strsql += " ,  의제매입세액공제 = '" + PretendPurchase + "'"  
			strsql += " ,  재활용폐자원등매입세액 = '" + PretendPurchase2 + "' "		
			strsql += " ,  제출자 = '" + issueID + "' "		
			strsql += " When Not Matched Then insert values('" 
			strsql +=  wcKwase + "', '"			#'1과세기간
			strsql +=  wcSingoGB + "', '"		#	'2신고구분
			strsql +=  wcCorpGB_txt + "', '"#		'3과세유형
			strsql +=  wcChojung + "', '"		#	'4환급구분
			strsql +=  wcSangho.replace("\'","") + "', '"		#	'5상호
			strsql +=  wcBizNo + "', '"			#'6사업자번호
			strsql +=  wcJupsuGB + "', '"		#	'7접수여부
			strsql +=  wcJubsuNum + "','"		#	'8신고번호
			strsql +=  wcIssueT + "','"			#'9신고시각	9
			strsql += f"{mainIssue_17[3]}', '{mainIssue_17[4]}', '{mainIssue_17[5]}', '{mainIssue_17[6]}', '{mainIssue_17[7]}', '{mainIssue_17[8]}', '{mainIssue_17[9]}', "
			strsql += f"'{mainIssue_17[10]}', '{mainIssue_17[11]}', '{mainIssue_17[12]}', '{mainIssue_17[13]}', '{mainIssue_17[14]}', '{mainIssue_17[15]}', '{mainIssue_17[16]}', "
			strsql += f"'{mainIssue_17[17]}', '{mainIssue_17[18]}', '{mainIssue_17[19]}', '{mainIssue_17[20]}', '{mainIssue_17[21]}', '{mainIssue_17[22]}', '{mainIssue_17[23]}', "
			strsql += f"'{mainIssue_17[24]}', '{mainIssue_17[25]}', '{mainIssue_17[26]}', '{mainIssue_17[27]}', '{mainIssue_17[28]}', '{mainIssue_17[29]}', '{mainIssue_17[30]}', "
			strsql += f"'{mainIssue_17[31]}', '{mainIssue_17[32]}', '{mainIssue_17[33]}', '{mainIssue_17[34]}', '{mainIssue_17[35]}', '{mainIssue_17[36]}', '{mainIssue_17[37]}', "
			strsql += f"'{mainIssue_17[38]}', '{mainIssue_17[39]}', '{mainIssue_17[40]}', '{mainIssue_17[41]}', '{mainIssue_17[42]}', '{mainIssue_17[43]}', '{mainIssue_17[44]}', "
			strsql += f"'{mainIssue_17[45]}', '{mainIssue_17[46]}', '{mainIssue_17[47]}', '{mainIssue_17[48]}', '{mainIssue_17[49]}', '{mainIssue_17[50]}', '{mainIssue_17[51]}', "
			strsql += f"'{mainIssue_17[52]}', '{mainIssue_17[53]}', '{mainIssue_17[54]}', '{mainIssue_17[55]}', '{mainIssue_17[56]}', '{mainIssue_17[57]}', '{mainIssue_17[58]}', "
			strsql += f"'{mainIssue_17[59]}', '{mainIssue_17[60]}', '{mainIssue_17[61]}', '{mainIssue_17[62]}', '{mainIssue_17[63]}', '{mainIssue_17[64]}', '{mainIssue_17[65]}', "
			strsql += f"'{mainIssue_17[66]}', '{mainIssue_17[67]}', '{mainIssue_17[68]}', '{mainIssue_17[69]}', '{mainIssue_17[70]}', '{mainIssue_17[71]}', '{mainIssue_17[72]}', "
			strsql += f"'{mainIssue_17[73]}', '{mainIssue_17[74]}', '{mainIssue_17[75]}', '{mainIssue_17[76]}', '{mainIssue_17[77]}', '{mainIssue_17[78]}', '{mainIssue_17[79]}', "
			strsql += f"'{mainIssue_17[80]}', '{mainIssue_17[81]}', '{mainIssue_17[82]}', '{mainIssue_17[83]}', '{mainIssue_17[84]}', '{mainIssue_17[85]}', '"
			strsql += UpjongCode + "', '"
			strsql += PaperSalesTaxInvoice + "', '"
			strsql += PaperSalesTaxInvoiceSum + "', '"
			strsql += str(PaperExpTaxInvoice) + "', '"
			strsql += PaperExpTaxInvoiceSum + "', '"
			strsql += "#1', '" #inspect_issue
			strsql += "0', '"  #str(inspect_elec)
			strsql += "0', '"  #str(inspect_labor)
			strsql += CardSaleSheet + "', '"
			strsql += CardCost1 + "', '"
			strsql += CardCost2 + "', '"
			strsql += CardCost3 + "', '"
			strsql += CardCost4 + "', '"
			strsql += str(BullGongSheet) + "', '"
			strsql += PretendPurchase + "', '"
			strsql += PretendPurchase2 + "', '" 
			strsql += issueID + "');" 
			print(strsql) 
			cursor.execute(strsql)



			strInspect = "select *, "
			if work_qt==4:
				if biz_type == 4:
					# 예정고지세액은 계산하지 않고 국세청 조회분 엑셀 업로드로 변경 21.04.15
					strInspect += " isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='" + work_yy + "년 2기' and 신고구분='확정' and 사업자등록번호='" + biz_no + "'),0) as 예정금액 "
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간전자외매입세금계산서합계 "
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간의제매입세액공제 "
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간재활용폐자원등매입세액 "
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간공제받지못할매입세액명세 "
				elif biz_type == 1:
					# 예정고지세액은 계산하지 않고 국세청 조회분 엑셀 업로드로 변경 21.04.15
					strInspect += " isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='" + work_yy + "년 2기' and 신고구분='확정' and 사업자등록번호='" + biz_no + "'),0) as 예정금액 "
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='" + biz_no + "' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간전자외매입세금계산서합계 "
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간의제매입세액공제 "
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간재활용폐자원등매입세액 "
					strInspect +=  " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간공제받지못할매입세액명세 "
			elif work_qt==2:
				if biz_type == 4:	
					#예정고지세액은 계산하지 않고 국세청 조회분 엑셀 업로드로 변경 21.04.15
					strInspect += " isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='" + work_yy + "년 1기' and 신고구분='확정' and 사업자등록번호='"+biz_no+"'),0) as 예정금액 "
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간전자외매입세금계산서합계 "
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간의제매입세액공제 "	
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간재활용폐자원등매입세액 "	
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간공제받지못할매입세액명세 "
				elif biz_type == 1:
					#예정고지세액은 계산하지 않고 국세청 조회분 엑셀 업로드로 변경 21.04.15
					strInspect += " isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='" + work_yy + "년 1기' and 신고구분='확정' and 사업자등록번호='"+biz_no+"'),0) as 예정금액 "
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17') as 직전신고기간전자외매입세금계산서합계 "
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17') as 직전신고기간의제매입세액공제 "
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17') as 직전신고기간재활용폐자원등매입세액 "
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C17') as 직전신고기간공제받지못할매입세액명세 "
				else:
					#예정고지세액은 계산하지 않고 국세청 조회분 엑셀 업로드로 변경 21.04.15
					strInspect += " isnull((select isnull(예정고지세액일반+예정미환급세액일반,0) from 부가가치세통합조회 where 과세기수='" + work_yy + "년 1기' and 신고구분='확정' and 사업자등록번호='"+biz_no+"'),0) as 예정금액 "
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간전자외매입세금계산서합계 "	
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간의제매입세액공제 "	
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간재활용폐자원등매입세액 "	
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and not 신고구분 like '%수정%' and  과세기간='" + work_yy + "년 2기' and 과세유형='C17') as 직전신고기간공제받지못할매입세액명세 "	
			elif work_qt==1:
					strInspect += " 0 as 예정금액"
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='"+str(int(work_yy)-1)+"년 "+ "2기' and 과세유형='C07') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='"+str(int(work_yy)-1)+"년 "+ "2기' and 과세유형='C07' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='"+(str(int(work_yy)-1))+"년 "+ "2기' and 과세유형='C07') as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간전자외매입세금계산서합계 "	
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간의제매입세액공제 "	
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간재활용폐자원등매입세액 "	
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + str(int(work_yy)-1) + "년 2기' and 과세유형='C07') as 직전신고기간공제받지못할매입세액명세 "	
			elif work_qt==3:
					strInspect += " 0 as 예정금액"
					strInspect += " ,(select isnull((매출과세기타금액 + 예정누락매출과세기타금액+면세사업합계수입금액-계산서교부금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간현금매출 "
					strInspect += " ,(select isnull(전자외매입세금계산서,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and 과세기간='" + work_yy + "년 1기' and 과세유형='C07' ) as 직전신고기간전자외매입세금계산서 "
					strInspect += " ,(select isnull(전자외매입세금계산서합계,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간전자외매입세금계산서합계 "	
					strInspect += " ,(select isnull(의제매입세액공제,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간의제매입세액공제 "	
					strInspect += " ,(select isnull(재활용폐자원등매입세액,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간재활용폐자원등매입세액 "	
					strInspect += " ,(select isnull(공제받지못할매입세액명세,'')  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + work_yy + "년 1기' and 과세유형='C07') as 직전신고기간공제받지못할매입세액명세 "				

			strInspect += " ,(select isnull(sum(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액 + 매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액 + 매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액 + 면세사업합계수입금액),0) from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and left(과세기간,4)='" + work_yy + "') as 당해년도매출  "
			strInspect += " ,(select isnull(sum(매출과세세금계산서발급금액 + 매출과세매입자발행세금계산서금액 + 예정누락매출세금계산서금액 + 매출과세카드현금발행금액 + 매출과세기타금액 + 예정누락매출과세기타금액 + 매출영세율세금계산서발급금액 + 매출영세율기타금액 + 예정누락매출영세율세금계산서금액 + 예정누락매출영세율기타금액 + 면세사업합계수입금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"'  and left(과세기간,4)='" + str(int(work_yy)-1) + "' and not 신고구분 like '%수정%') 직전년도매출 "
			strInspect += " ,(select isnull(sum(면세사업합계수입금액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and  과세기간='" + kwasekikan + "' ) as 동일기간면세매출 "
			strInspect += " ,(select isnull(SUM(경감공제합계세액),0)  from 부가가치세전자신고3 where 사업자등록번호='"+biz_no+"' and left(과세기간,4)='" + work_yy + "') as 경감공제합계세액 " 
			strInspect += " from 부가가치세전자신고3 	"
			strInspect += " where 사업자등록번호='"+ biz_no +"' "
			strInspect += " and 과세기간='" + kwasekikan + "' "
			strInspect += " and   과세유형='" + wcCorpGB + "' "
			print(strInspect)
			
			cursor.execute(strInspect)
			result = cursor.fetchone()#결과가 1줄인 경우fetchone, 여러줄인 경우 fetchall
			columns = [col[0] for col in cursor.description]#컬럼명으로 조회할 수 있도록 세팅1
		


			if result:
				rs2 = dict(zip(columns, result)) #컬럼명으로 조회할 수 있도록 세팅2

				amt_Issue_CARDSALE = float(mainIssue_17[7]) + float(mainIssue_17[8])  # rs2("매출과세카드현금발행금액")+rs2("매출과세카드현금발행세액")

				strsql = f"SELECT YN_14, yn_15, YN_16, yn_17 FROM mem_user a, tbl_vat b WHERE a.Seq_No=b.seq_no AND biz_no='{biz_no}' AND work_yy='{work_yy}' AND work_qt='{work_qt}'"
				rs4 = cursor.execute(strsql).fetchone()
				yn_14=yn_15=yn_16=yn_17=0
				if rs4:					yn_14=rs4[0]; yn_15=rs4[1]; yn_16=rs4[2]; yn_17 = rs4[3]
				amt_HTX_CARDSALE = float(yn_16) + float(yn_17); print(f'amt_HTX_CARDSALE:{amt_HTX_CARDSALE}')
				# =================================================================================1. 신용카드 및 현금영수증 매출 반영여부
				if amt_Issue_CARDSALE < amt_HTX_CARDSALE:
					if abs(amt_Issue_CARDSALE - amt_HTX_CARDSALE) > 20:
						inspect_issue += "2#"
				# =================================================================================2. 현금건별 온라인매출 반영여부
				if rs2["직전신고기간현금매출"] is not None:
					if float(rs2["직전신고기간현금매출"]) > 0 and ( float(rs2["매출과세기타금액"]) + float(rs2["매출과세기타세액"]) ) == 0:
						inspect_issue += "8#";print(f'당기 매출과세기타금액 : {rs2["매출과세기타금액"]}')
				# =================================================================================2. 예정고지 및 예정미환급 세액 미반영
				preAmt = Decimal(rs2["예정금액"])
				if preAmt - (Decimal(mainIssue_17[63]) + Decimal(mainIssue_17[62])) > Decimal('10'):    inspect_issue += "3#"
				elif preAmt == 0 and (float(mainIssue_17[63]) + float(mainIssue_17[62])) > 0:	inspect_issue += "3#"
				print(f'preAmt:{preAmt}');print(f'mainIssue_17[63]:{mainIssue_17[63]}');print(f'mainIssue_17[62]:{mainIssue_17[62]}')
				# =================================================================================3. 종이 매입세금계산서 반영여부
				pre_paperExpTaxInvoice = 0
				now_paperExpTaxInvoice = ""
				if rs2["전자외매입세금계산서합계"]  != "":   # is not None:
						now_paperExpTaxInvoice = rs2["전자외매입세금계산서합계"][25:40]
				txt_paperExpTaxInvoice = rs2["직전신고기간전자외매입세금계산서"] if rs2["직전신고기간전자외매입세금계산서"] is not None else ""
				if rs2["직전신고기간전자외매입세금계산서합계"]  != "":
						if txt_paperExpTaxInvoice != "":
								pre_paperExpTaxInvoice = float(rs2["직전신고기간전자외매입세금계산서합계"][25:39])
								if pre_paperExpTaxInvoice > 0 and (now_paperExpTaxInvoice == "" or now_paperExpTaxInvoice == "0"):
										inspect_issue += "4#"
				# =================================================================================4. 면세매출 있을 시 공통매입세액 반영여부
				if float(rs2["동일기간면세매출"]) > 0 and float(mainIssue_17[50]) == 0:
						inspect_issue += "5#"
						if float(mainIssue_17[57]) == 0:
								inspect_issue = inspect_issue.replace("5#", "")
				# =================================================================================6. 연간 신용카드발행세액공제 한도체크
				if float(rs2["경감공제합계세액"]) > 10000000:
						inspect_issue += "6#"
				# =================================================================================9. 환급액 500만원 초과시 환급조사 대비
				if float(mainIssue_17[58]) <= -5000000:
						inspect_issue += "9#"
				# =================================================================================7. 전자세금계산서 의무발급 대상자
				if biz_type > 3:
						if PaperSalesTaxInvoiceSum == "" and float(rs2["직전년도매출"]) >= 300000000:
								inspect_elec = 1
						elif PaperSalesTaxInvoiceSum != "" and float(rs2["직전년도매출"]) >= 300000000:
								inspect_elec = 2
				elif biz_type <= 3:
						if PaperSalesTaxInvoiceSum != "":
								inspect_elec = 2
								inspect_issue += "7#"
				# =================================================================================8. 성실신고 대상자
				if 1 <= len(UpjongCode) <= 2:
						if "2021" <= work_yy:
								Amt_Labor_standard = 1500000000
						else:
								Amt_Labor_standard = 750000000
				else:
						if "2021" <= work_yy:
								Amt_Labor_standard = 500000000
						else:
								Amt_Labor_standard = 500000000

				if biz_type > 3 and (float(rs2["당해년도매출"]) * 4 / work_qt >= Amt_Labor_standard):
						inspect_labor = 2
				# =================================================================================10. 의제매입세액공제
				if rs2["직전신고기간의제매입세액공제"] is not None and rs2["직전신고기간의제매입세액공제"].strip() != "" and PretendPurchase.strip() == "":    			inspect_issue += "10#"
				print(f'rs2["직전신고기간의제매입세액공제"]:{rs2["직전신고기간의제매입세액공제"]}');print(f'PretendPurchase:{PretendPurchase}')
				# =================================================================================11. 의제매입세액공제
				if rs2["직전신고기간재활용폐자원등매입세액"] is not None and rs2["직전신고기간재활용폐자원등매입세액"].strip() != "" and PretendPurchase.strip() == "": 	inspect_issue += "11#"
				print(f'rs2["직전신고기간재활용폐자원등매입세액"]:{rs2["직전신고기간재활용폐자원등매입세액"]}');print(f'PretendPurchase2:{PretendPurchase2}')
				# =================================================================================12. 공제받지못할매입세액
				arrBfBull = ["" for _ in range(9)]
				arrNowBull = ["" for _ in range(9)]
				if rs2["직전신고기간공제받지못할매입세액명세"] is not None and rs2["직전신고기간공제받지못할매입세액명세"].strip() != "":
						tmpBfStr = rs2["직전신고기간공제받지못할매입세액명세"].strip()
						c = 0
						for b in range(1, len(tmpBfStr) // 39 + 1):
								tmpBfStr2 = tmpBfStr[c: b * 39]
								arrBfBull[int(tmpBfStr2[1])] = tmpBfStr2
								c += b * 39
				if BullGongSheet != "":
						tmpNowStr = BullGongSheet
						d = 0
						for b in range(1, len(tmpNowStr) // 39 + 1):
								tmpNowStr2 = tmpNowStr[d: b * 39];print('tmpNowStr2:'+tmpNowStr2)
								arrNowBull[int(tmpNowStr2[1])] = tmpNowStr2
								d += b * 39
				if rs2["직전신고기간공제받지못할매입세액명세"] is not None and rs2["직전신고기간공제받지못할매입세액명세"].strip() != "" or BullGongSheet!= "":
					for i in range(len(arrBfBull)):
						if arrBfBull[i] != "" and arrNowBull[i] == "":
							inspect_issue += "12#"
							break
				strsql = f"update  부가가치세전자신고3 set inspect_issue = '{inspect_issue}',inspect_elec = '{inspect_elec}',inspect_labor = '{inspect_labor}' "
				strsql += f"where 사업자등록번호= '{wcBizNo}' and 과세기간= '{wcKwase}' and 과세유형='{wcCorpGB_txt}'"
				print(strsql) 
				cursor.execute(strsql)
				######################################################## 부가세 통합조회와 대조 검증
				saleSinca=elec_saleSC=sum_EtcSinca=sum_EtcSinca_1=sum_kkkePmdh_1=sum_EtcSinca_2=sum_kkkePmdh_2=sum_EtcSinca_3=sum_kkkePmdh_3=sum_EtcSinca_4=sum_kkkePmdh_4=0
				sum_TotalSinca_1=sum_TotalSinca_2=sum_TotalSinca_3=sum_TotalSinca_4=sum_TotalPmdh_1=sum_TotalPmdh_2=sum_TotalPmdh_3=sum_TotalPmdh_4=0				
				img_saleTI = img_saleNTI = img_saleSC = img_saleCash = img_costTI = img_costNTI = img_costSC = invNum = img_pretax = sum_warn = 0
				img_costCard1 = img_costCard2 = img_costCard3 = img_costCard4 = 0
				elec_saleTI = elec_saleNTI = elec_costTI = elec_costNTI = elec_costSC = elec_pretax = elec_pretaxNot = elec_purchaseSpecial = elec_saleSCvat = elec_costCard4_Buho = elec_costCard4Vat =elec_costCard2_Buho = 0				
				elec_costCard3_Buho = elec_costCard3Vat= elec_costCard1_Buho=elec_costCard1Vat=elec_costCard2Vat=0
				sum_Etccash_1	=  sum_Etccash_2 = sum_Etccash_3	=sum_Etccash_4 = 0
				saleTI = saleTIvat = saleNTI = saleSinca = saleCash = saleCashvat = saleExport = saleExport2 = 0
				costTI = costTIvat = costNTI = costSinca = costSincavat = costCash = costCashvat = costBockji = costBockjivat = pretax = pretaxNot = pretaxKani = pretaxKaniSingo = purchaseSpecial = 0
				salecashSheet = addTxt = realestateSheet = ""

				kawasekisu =  kwasekikan
				bizno = wcBizNo
				if wcCorpGB == "C07" : singokubun = "확정" 
				else : singokubun = "예정" 
				if wcCorpGB == "C07" : singokubun_B="C07" 
				else : singokubun_B="C17" 
				if singokubun.strip()=="확정" : singokubun_B="C07" 
				else: singokubun_B="C17" 
				str_vat = f"select * from 부가가치세전자신고3 where 과세기간='{kawasekisu}' and 사업자등록번호='{bizno}'  order by  과세유형" ;print(f"부가세통합조회 검증1 : {str_vat}")
				rs_vat = cursor.execute(str_vat).fetchone()
				columns = [col[0] for col in cursor.description]
				if rs_vat:
					rs_vat = dict(zip(columns, rs_vat))
					strsql = f"select (select top 1 a.biz_type from mem_user a, mem_deal b where  a.biz_no='{bizno}' and a.seq_no=b.seq_no and b.keeping_YN='Y') as biz_type, RIGHT(tran_mm,2) as work_MM, SaleGubun,MM_Scnt,Tot_StlAmt,Etc_StlAmt,PurcEuCardAmt from Tbl_HomeTax_SaleCard where Tran_YY='{kawasekisu[:4]}' and Seq_No=(select top 1 a.seq_no from mem_user a, mem_deal b where  a.biz_no='{bizno}' and a.seq_no=b.seq_no and b.keeping_YN='Y')  order by tran_mm,SaleGubun "
					print(f"부가세통합조회 검증2 : {strsql}")
					rs3s = cursor.execute(strsql).fetchall()
					if rs3s:
						for rs3 in rs3s:
							biz_type = rs3[0]; work_MM = rs3[1]; SaleGubun = rs3[2];MM_Scnt = rs3[3];Tot_StlAmt = rs3[4];Etc_StlAmt = rs3[5];PurcEuCardAmt = rs3[6];
							if SaleGubun.strip()=="신용카드" :
								if int(work_MM)<=3 : 
									sum_TotalSinca_1 = sum_TotalSinca_1 + int(Tot_StlAmt)
									sum_EtcSinca_1	= sum_TotalSinca_1/1.1 
								elif int(work_MM)<=6 : 
									sum_TotalSinca_2 = sum_TotalSinca_2 + int(Tot_StlAmt)
									sum_EtcSinca_2	= sum_TotalSinca_2/1.1 
								elif int(work_MM)<=9 : 
									sum_TotalSinca_3 = sum_TotalSinca_3 + int(Tot_StlAmt)
									sum_EtcSinca_3	= sum_TotalSinca_3/1.1 
								elif int(work_MM)<=12 : 
									sum_TotalSinca_4 = sum_TotalSinca_4 + int(Tot_StlAmt)
									sum_EtcSinca_4	= sum_TotalSinca_4/1.1 
							elif SaleGubun.strip()=="현금영수증" :
								if int(work_MM)<=3 : 
									sum_Etccash_1	= sum_Etccash_1 + int(Etc_StlAmt)
								elif int(work_MM)<=6 : 
									sum_Etccash_2	= sum_Etccash_2 + int(Etc_StlAmt)
								elif int(work_MM)<=9 : 
									sum_Etccash_3	= sum_Etccash_3 + int(Etc_StlAmt)
								elif int(work_MM)<=12 : 
									sum_Etccash_4	= sum_Etccash_4 + int(Etc_StlAmt)
							else:
								if int(work_MM)<=3 :
									sum_TotalPmdh_1 = sum_TotalPmdh_1 + int(Tot_StlAmt)
									sum_kkkePmdh_1 = sum_TotalPmdh_1/1.1
								elif int(work_MM)<=6 : 
									sum_TotalPmdh_2 = sum_TotalPmdh_2 + int(Tot_StlAmt)
									sum_kkkePmdh_2 = sum_TotalPmdh_2/1.1
								elif int(work_MM)<=9 : 
									sum_TotalPmdh_3 = sum_TotalPmdh_3 + int(Tot_StlAmt)
									sum_kkkePmdh_3 = sum_TotalPmdh_3/1.1
								elif int(work_MM)<=12 : 
									sum_TotalPmdh_4 = sum_TotalPmdh_4 + int(Tot_StlAmt)
									sum_kkkePmdh_4 = sum_TotalPmdh_4/1.1
				#==============================================================신용카드 + 판매대행 매출
				if kawasekisu[-2:]+singokubun_B =="1기C17" :
					sum_EtcSinca = sum_EtcSinca_1+sum_kkkePmdh_1 
				elif kawasekisu[-2:]+singokubun_B =="1기C07" :
					if int(biz_type)<4  :
						sum_EtcSinca = sum_EtcSinca_2+ sum_kkkePmdh_2 
					else:
						sum_EtcSinca = sum_EtcSinca_1+sum_kkkePmdh_1 + sum_EtcSinca_2+sum_kkkePmdh_2
				elif kawasekisu[-2:]+singokubun_B =="2기C17" :
						sum_EtcSinca = sum_EtcSinca_3 + sum_kkkePmdh_3
				elif kawasekisu[-2:]+singokubun_B =="2기C07" :
					if int(biz_type)<4  :
						sum_EtcSinca = sum_EtcSinca_4 + sum_kkkePmdh_4
					else:
						sum_EtcSinca = sum_EtcSinca_3+sum_kkkePmdh_3 + sum_EtcSinca_4+sum_kkkePmdh_4 

				now_saleNonTaxInvoice=""
				if rs_vat["전자외매출세금계산서합계"].strip()!="" :
					now_saleNonTaxInvoice = rs_vat["전자외매출세금계산서합계"][25:40]
					if now_saleNonTaxInvoice[-1:]=="}" : now_saleNonTaxInvoice= "-"+now_saleNonTaxInvoice[:14]+"0"
				if now_saleNonTaxInvoice=="" :
					amt_saleNonTaxInvoice = 0 
				else :
					if now_saleNonTaxInvoice[-1:]=="P" :
						now_saleNonTaxInvoice = now_saleNonTaxInvoice[:len(now_saleNonTaxInvoice)-1]
						amt_saleNonTaxInvoice = int(now_saleNonTaxInvoice) * -1
					else:
						amt_saleNonTaxInvoice = int(now_saleNonTaxInvoice) 
				elec_saleTI = int(rs_vat["매출과세세금계산서발급금액"]) + int(rs_vat["매출영세율세금계산서발급금액"]) - amt_saleNonTaxInvoice	
				elec_saleNTI = int(rs_vat["계산서교부금액"])

				CardSaleTotal = rs_vat["신용카드발행집계표"].strip()
				#신용카드 공급가액
				if len(CardSaleTotal)>0 :	elec_saleSC = int(CardSaleTotal.strip()[24:37]) 
				else: elec_saleSC=0 
				if elec_saleSC!=0 : elec_saleSC = round(elec_saleSC/1.1,0)
				#현금영수증 공급가액
				if len(CardSaleTotal)>0 :	elec_saleSCvat = int(CardSaleTotal.strip()[37:50]) ; elec_saleSCvat=0 
				if elec_saleSCvat!=0 : elec_saleSCvat = round(elec_saleSCvat/1.1,0)
				#기타매출
				elecSaleKita = int(rs_vat["매출과세기타금액"])

				now_paperExpTaxInvoice = rs_vat["전자외매입세금계산서합계"][25:40]
				if now_paperExpTaxInvoice=="" :
					amt_paperExpTaxInvoice = 0 
				else :
					if now_paperExpTaxInvoice[-1:]=="}" :
						amt_paperExpTaxInvoice = int(now_paperExpTaxInvoice.replace("}",""))* -1
					else:
						amt_paperExpTaxInvoice = int(now_paperExpTaxInvoice) 

				elec_costTI = int(rs_vat["매입세금계산서수취일반금액"]) + int(rs_vat["매입세금계산서수취고정자산금액"])  + int(rs_vat["예정누락매입신고세금계산서금액"]) - amt_paperExpTaxInvoice
				elec_costNTI = int(rs_vat["계산서수취금액"])
				elec_costCard1 = rs_vat["신용카드수취기타카드"][59:72]
				if elec_costCard1!="" :
					elec_costCard1 = int(elec_costCard1)
					if rs_vat["신용카드수취기타카드"][72:73] == "-" : 
						elec_costCard1_Buho = -1;elec_costCard1 = elec_costCard1*elec_costCard1_Buho
					if elec_costCard1!="" : 
						elec_costCard1Vat = rs_vat["신용카드수취기타카드"][83:96]
						elec_costCard1Vat = elec_costCard1Vat*elec_costCard1_Buho
				else:
					elec_costCard1 = 0
				

				elec_costCard2 = rs_vat["신용카드수취현금영수증"][59:72]
				if elec_costCard2!="" :
					elec_costCard2 = int(elec_costCard2)
					if rs_vat["신용카드수취현금영수증"][72:73] =="-" : 
						elec_costCard2_Buho = -1;elec_costCard2 = elec_costCard2*elec_costCard2_Buho
					if elec_costCard2!="" : 
						elec_costCard2Vat = int(rs_vat["신용카드수취현금영수증"][83:96])
						elec_costCard2Vat = elec_costCard2Vat*elec_costCard2_Buho
				else:
					elec_costCard2 = 0
				

				elec_costCard3 = rs_vat["신용카드수취화물복지"][59:72]
				if elec_costCard3!="" :
					elec_costCard3 = int(elec_costCard3)
					if rs_vat["신용카드수취화물복지"][72:73] =="-" : 
						elec_costCard3_Buho = -1;elec_costCard3 = elec_costCard3*elec_costCard3_Buho
					if elec_costCard3!="" : elec_costCard3Vat = int(rs_vat["신용카드수취화물복지"][83:96]);elec_costCard3Vat = elec_costCard3Vat*elec_costCard3_Buho
				else:
					elec_costCard3 = 0
				elec_costCard4 = rs_vat["신용카드수취사업용카드"][59:72]
				if elec_costCard4!="" :
					elec_costCard4 = int(elec_costCard4)
					if rs_vat["신용카드수취사업용카드"][72:73] =="-" : elec_costCard4_Buho = -1;elec_costCard4 = elec_costCard4*elec_costCard4_Buho
					if elec_costCard4!="" : elec_costCard4Vat = int(rs_vat["신용카드수취사업용카드"][83:96]);elec_costCard4Vat = elec_costCard4Vat*elec_costCard4_Buho
				else:
					elec_costCard4 = 0
				elec_pretax = int(rs_vat["예정고지세액"])
				elec_pretaxNot = int(rs_vat["예정신고미환급세액"])
				elec_purchaseSpecial = int(rs_vat["매입자납부특례기납부세액"])
				if rs_vat:
					str_nm = "select max(과세기수) 과세기수, max(과세기간) 과세기간,max(신고구분) 신고구분,max(상호) 상호,max(신고유형) 신고유형,max(관할서) 관할서,max(법인예정고지대상) 법인예정고지대상,max(간이부가율) 간이부가율,max(주업종코드) 주업종코드,"
					str_nm +=  " isnull(sum(매출전자세금계산서공급가액),0) 매출전자세금계산서공급가액, "
					str_nm +=  " isnull(sum(매출전자세금계산서세액),0) 매출전자세금계산서세액, "
					str_nm +=  " isnull(sum(매출전자계산서공급가액),0) 매출전자계산서공급가액, "
					str_nm +=  " isnull(sum(매출현금영수증공급가액),0) 매출현금영수증공급가액,"
					str_nm +=  " isnull(sum(매출현금영수증세액),0) 매출현금영수증세액,"
					str_nm +=  " isnull(sum(수출신고필증),0) 수출신고필증,"
					str_nm +=  " isnull(sum(구매확인서등),0) 구매확인서등, "
					str_nm +=  " isnull(sum(매입전자세금계산서공급가액),0) 매입전자세금계산서공급가액,"
					str_nm +=  " isnull(sum(매입전자세금계산서세액),0) 매입전자세금계산서세액,"
					str_nm +=  " isnull(sum(매입전자계산서공급가액),0) 매입전자계산서공급가액,"
					str_nm +=  " isnull(sum(매입신용카드세액),0) 매입신용카드세액,"
					str_nm +=  " isnull(sum(매입신용카드공급가액),0) 매입신용카드공급가액,"
					str_nm +=  " isnull(sum(매입현금영수증공급가액),0) 매입현금영수증공급가액,"
					str_nm +=  " isnull(sum(매입현금영수증세액),0) 매입현금영수증세액,"
					str_nm +=  " isnull(sum(매입복지카드공급가액),0) 매입복지카드공급가액,"
					str_nm +=  " isnull(sum(매입복지카드세액),0) 매입복지카드세액,"
					str_nm +=  " isnull(max(예정고지세액일반),0) 예정고지세액일반,"
					str_nm +=  " isnull(max(예정미환급세액일반),0) 예정미환급세액일반,"
					str_nm +=  " isnull(max(예정부과세액간이),0) 예정부과세액간이,"
					str_nm +=  " isnull(max(예정신고세액간이),0) 예정신고세액간이,"
					str_nm +=  " isnull(max(매입자납부특례기납부세액),0) 매입자납부특례기납부세액,"
					str_nm +=  " isnull(max(현금매출명세서),0) 현금매출명세서,"
					str_nm +=  " isnull(max(부동산임대공급가액명세서),0) 부동산임대공급가액명세서 " 
					str_nm +=  f" from 부가가치세통합조회 where 과세기수='{kawasekisu}' and 신고구분='{singokubun}' and 사업자등록번호='{bizno}'" 
					print(f"부가세통합조회 검증3 : {str_nm}")
					rs = cursor.execute(str_nm).fetchone()
					columns = [col[0] for col in cursor.description]
					if rs and rs[0] is not None:
						rs = dict(zip(columns, rs))
						txtTitle = "부가가치세 통합조회내역"
						kawasekisu = rs["과세기수"]
						kwasekikan = rs["과세기간"]
						singokubun = rs["신고구분"].strip()

						sangho = rs["상호"]
						singoyouhyng = rs["신고유형"]
						bubinyejung = rs["법인예정고지대상"]
						if singoyouhyng=="법인" and bubinyejung=="Y" : txtBubinyejung = "(법인예정고지대상)"
						kwanhanseo = rs["관할서"]
						juupjongcode = rs["주업종코드"]
						kanibukayul = rs["간이부가율"]
						saleTI = int(rs["매출전자세금계산서공급가액"] )
						saleTIvat = int(rs["매출전자세금계산서세액"]  )
						saleNTI = int(rs["매출전자계산서공급가액"] )
						saleSinca = sum_EtcSinca
						saleCash = int(rs["매출현금영수증공급가액"] )
						saleCashvat = int(rs["매출현금영수증세액"] )
						saleExport = int(rs["수출신고필증"] )
						saleExport2 = int(rs["구매확인서등"] )

						costTI = int(rs["매입전자세금계산서공급가액"] )
						costTIvat = int(rs["매입전자세금계산서세액"] )
						costNTI = int(rs["매입전자계산서공급가액"] )
						costSinca = int(rs["매입신용카드공급가액"] )
						costSincavat = int(rs["매입신용카드세액"] )
						costCash = int(rs["매입현금영수증공급가액"] )
						costCashvat = int(rs["매입현금영수증세액"] )
						costBockji = int(rs["매입복지카드공급가액"] )
						costBockjivat = int(rs["매입복지카드세액"] )
						pretax = int(rs["예정고지세액일반"] )
						pretaxNot = int(rs["예정미환급세액일반"] )
						pretaxKani = int(rs["예정부과세액간이"] )
						pretaxKaniSingo = int(rs["예정신고세액간이"] )
						purchaseSpecial = int(rs["매입자납부특례기납부세액"] )
						salecashSheet = rs["현금매출명세서"]
						if salecashSheet=="Y" : addTxt = "  [현금매출명세서 제출대상]"
						realestateSheet = rs["부동산임대공급가액명세서"]
						if realestateSheet=="Y" : addTxt = addTxt + "  [부동산임대공급가액명세서 제출대상]"
				else:
					saleSinca = sum_EtcSinca														
				#===============검증시작

				if (saleTI-elec_saleTI)==0 : img_saleTI = 0 
				else: img_saleTI = 1 
				if (saleNTI-elec_saleNTI)==0 : img_saleNTI = 0 
				else: img_saleNTI = 1 

				if (saleSinca>elec_saleSC and abs(saleSinca-elec_saleSC)>1000) or (elec_saleSC-saleSinca)>saleSinca*.3	: img_saleSC = 1  
				else: img_saleSC = 0 
				if abs(saleCash-elec_saleSCvat)<=1000 	: img_saleCash = 0   
				else: img_saleCash = 1  
		
				if (costTI-elec_costTI)==0 : img_costTI = 0 
				else: img_costTI = 1 
				if (costNTI-elec_costNTI)==0 : img_costNTI = 0 
				else: img_costNTI = 1
				if int(costCash)<=int(elec_costCard2)		: img_costCard2 = 0 
				else: img_costCard2 = 1 
				if int(costBockji)<=int(elec_costCard3)	: img_costCard3 = 0 
				else: img_costCard3 = 1 
				if int(costSinca)<=int(elec_costCard4)	: img_costCard4 = 0 	
				else: img_costCard4 = 1 	
				
				#예정고지 검증
				if (pretax-elec_pretax)==0 : invNum = 0 
				else: invNum = 1 
				#예정미환급 검증 누적
				if (pretaxNot - elec_pretaxNot)==0 : invNum = invNum + 0 
				else: invNum = invNum + 1 
				#매입자특례납부 검증 누적
				if (purchaseSpecial-elec_purchaseSpecial)==0 : invNum = invNum + 0 
				else: invNum = invNum + 1 
				if invNum>1 : invNum = 1

				sum_warn = img_saleTI + img_saleNTI + img_saleSC + img_saleCash + img_costTI + img_costNTI + img_costSC + invNum
				sum_warn = sum_warn + img_costCard1 + img_costCard2 + img_costCard3 + img_costCard4
				tran_yy=kawasekisu[:4]
				if kawasekisu.strip()[-2:]=="1기" and singokubun.strip()=="예정" : stnd_Gb=1
				if kawasekisu.strip()[-2:]=="1기" and singokubun.strip()=="확정" : stnd_Gb=2
				if kawasekisu.strip()[-2:]=="2기" and singokubun.strip()=="예정" : stnd_Gb=3
				if kawasekisu.strip()[-2:]=="2기" and singokubun.strip()=="확정" : stnd_Gb=4
				str_mg = f"Merge Tbl_vat as A Using (select (select seq_no from mem_user where biz_no='{biz_no}') as seq_no, '{tran_yy}' as work_yy, '{stnd_Gb}' as work_qt ) as B "
				str_mg += "On A.seq_no = B.seq_no and A.work_yy = B.work_yy and A.work_qt = B.work_qt  "
				str_mg += "WHEN Matched Then   "
				str_mg += f"	Update set YN_14={sum_warn}" 
				str_mg += "	When Not Matched Then  "
				str_mg += "	INSERT (seq_no,work_YY,work_QT,YN_1,YN_2,YN_3,YN_4,YN_5,YN_6,YN_7,YN_8,YN_9,YN_10,YN_11,YN_12,YN_13,YN_14,YN_15,YN_16,YN_17) "
				str_mg += f"	values((select seq_no from mem_user where biz_no='{biz_no}'),'{tran_yy}','{stnd_Gb}',0,0,0,0,0,0,0,0,0,0,0,0,0,{sum_warn},0,0,0);"
				cursor.execute(str_mg)							
		elif flag[:4]=='ZZMS':
			wcSingo = driver.execute_script("return arguments[0].innerText;", cols[3])
			wcYear = driver.execute_script("return arguments[0].innerText;", cols[6])[:4]
			wcBizno = driver.execute_script("return arguments[0].innerText;", cols[4])
			wcSangho =  driver.execute_script("return arguments[0].innerText;", cols[5])
			wcSingoGB =  driver.execute_script("return arguments[0].innerText;", cols[25])
			wcJechulGS =  driver.execute_script("return arguments[0].innerText;", cols[9]).replace(',','')
			wcJechulAMT =  driver.execute_script("return arguments[0].innerText;", cols[10]).replace(',','')
			wcJechulDate =  driver.execute_script("return arguments[0].innerText;", cols[11])
			wcJupsuNo =  driver.execute_script("return arguments[0].innerText;", cols[12])
			if flag[-2:]=='50': wcSingo = "이자소득지급명세서"
			elif flag[-2:]=='60': wcSingo = "배당소득지급명세서"
			strdel = f"delete from 지급조서전자신고 where 신고서종류='{wcSingo}'  and 과세년도='{wcYear}' and 사업자번호='{wcBizno}' ";print(strdel)		
			cursor.execute(strdel) 					#                         사업자번호     상호          과세연도            신고구분            접수자
			strIns = f"INSERT into 지급조서전자신고 VALUES ('{wcSingo}','{wcBizno}','{wcSangho}','{wcYear}','{wcSingoGB}','{cols[0]}',"
			             #제출건수       제출금액          접수일시         접수번호                       
			strIns += f"'{wcJechulGS}','{wcJechulAMT}','{wcJechulDate}','{wcJupsuNo}',getdate())"
			print(strIns)
			cursor.execute(strIns) 				
		elif flag=='wonchun':
			#지급연월  제출연월     #A01      #A20   #A30	   #A40		#A50		#A99                    # 전체합계
			wcJ = ""	;	wcK = ""; issueID = "";wcL=0; wcM = 0;wcN = 0;wcO = 0;wcP = 0;wcQ = 0;wcR = "0";wcZ = 0						
			wcLman = 0;wcMman = 0;wcNman = 0;wcOman = 0;wcPman = 0;wcQman = 0;wcRman = 0
			wcZman = 0;wcLtax = 0;wcMtax = 0;wcNtax = 0;wcOtax = 0 ;wcPtax = 0 ;wcQtax = 0 ;wcRtax = 0;wcZtax = 0
			wcS = wcSman = wcStax = 0#a80 법인원천 이자소득
			# '전체인원 합계# 'a01 세금# 'a60 세금# 'a20 세금# 'a30 세금# 'a40 세금# 'a50 세금# 'a03 세금# '전체인원 세금
			wcManDate = str(datetime.now())[:10].replace("-","")  # '작성일자
			while True:
				line = elecfile.readline()
				if not line:   break
				if line[:9] == "21C103900":      
					htxLoginID = line[49:69].replace(' ','')
					wcJ = line[37:43]  # '지급연월
					wcK = line[43:49]  # '제출연월
					issueID = line[49:69].replace(' ','')  # '제출자
				if line[:12]== "23C103900A01":  wcL = int(line[27:42]);  wcLman = int(line[12:27])
				if line[:12]== "23C103900A03":  wcR = int(line[27:42]); wcRman = int(line[12:27])
				if line[:12]== "23C103900A10":  wcLtax = int(line[102:117])
				if line[:12]== "23C103900A20":  wcM = int(line[27:42]);   wcMman = int(line[12:27]);   wcMtax = int(line[102:117])
				if line[:12]== "23C103900A30":  wcN = int(line[27:42]);   wcNman = int(line[12:27]);    wcNtax = int(line[102:117])
				if line[:12]== "23C103900A40":  wcO = int(line[27:42]);  wcOman = int(line[12:27]);  wcOtax = int(line[102:117])
				if line[:12]== "23C103900A50":  wcP = int(line[27:42]);  wcPman = int(line[12:27]);  wcPtax = int(line[102:117])
				if line[:12]== "23C103900A60":  wcQ = int(line[27:42]);  wcQman = int(line[12:27]);  wcQtax = int(line[102:117])
				if line[:12]== "23C103900A80":  wcS = int(line[27:42]);  wcSman = int(line[12:27]);  wcStax = int(line[102:117])
				if line[:12]== "23C103900A99":  wcZ = int(line[27:42]);  wcZman = int(line[12:27]);  wcZtax = int(line[102:117])
			elecfile.close()  
			wcKwase = cols[2].text  # 과세연월    
			wcCorpGB = cols[3].text  # 신고서종류
			wcSingoGB = cols[4].text  # 신고구분
			wcChojung = cols[5].text  # 신고유형
			wcSangho = cols[6].text  # 상호
			wcSangho = wcSangho.replace("'","")
			wcBizNo = cols[7].text  # 사업자번호
			wcJupsuGB = cols[8].text  # 접수방법
			wcIssueT = cols[9].text  # 신고시각
			wcJubsuNum = cols[10].text  # 접수번호      
			wcJubsuPaper = cols[11].text  # 접수여부-서류    
			intmm = wcKwase[-3:].replace("년", "").replace("월", "");strmm = intmm
			if len(intmm) == 1:          strmm = "0" + strmm
			wcKwase = wcKwase[:4] + strmm

			strsql = "Merge 원천세전자신고 as A Using (select '"+wcBizNo+"' as bizno,'"+wcKwase+"' as wcKwase) as B "
			strsql += "On A.과세연월=B.wcKwase  and A.사업자등록번호=B.bizno  "
			strsql += " when matched then update set "
			strsql += "  접수일시 = '" + wcIssueT + "'"
			strsql += " ,접수번호 = '" + wcJubsuNum + "'"
			strsql += " ,접수여부 = '" + wcJubsuPaper + "'"
			strsql += " When Not Matched Then insert values('"+wcKwase+"', '"+wcCorpGB+"', '"+wcSingoGB+"', '"+wcChojung+"', '"+wcSangho+"', '"+wcBizNo +"', '"+wcIssueT+"', '"+wcJubsuNum+"', '"+wcJubsuPaper
			strsql += "', '"+wcJ+"','"+wcK+"','"+str(wcL)+"','"+str(wcM)+"','"+str(wcN)+"','"+str(wcO)+"','"+str(wcP)+"','"+str(wcZ)+"','"+str(wcManDate)
			strsql += "','"+str(wcLman)+"','"+str(wcMman)+"','"+str(wcNman)+"','"+str(wcOman)+"','"+str(wcPman)+"','"+str(wcZman)+"','"+str(wcR)+"','"+str(wcRman)+"','"+str(wcQ)+"','"+str(wcQman)
			strsql += "','"+str(wcLtax)+"','"+str(wcMtax)+"','"+str(wcNtax)+"','"+str(wcOtax)+"','"+str(wcPtax)+"','"+str(wcQtax)+"','"+str(wcZtax)+"','"+issueID 
			strsql += "','"+str(wcS)+"','"+str(wcSman)+"','"+str(wcStax)
			strsql += "');"
			print(strsql) 
			cursor = connection.cursor()
			cursor.execute(strsql) 			
		elif flag=='income' :			
			wcIncomeTax = 0;wcMidTax=0
			record_51C110700=[];record_53C110700=[];
			while True:
				line = elecfile.readline()
				if not line:   break
				if line[:9] == "51C110700":     #일반과세자 부가세 신고서
					htxLoginID = line[43:63].replace(' ','')
					# if line[9:22].replace(' ','')!=memuser.ssn:pyautogui.prompt('선택된 전자신고파일 : '+line[69:99])  
					record_51C110700.append(line)
				if line[:9] == "52C110713":     #종합소득세 중간예납 레코드
					wcMidTax = int(line[9:22])     #중간예납
				if line[:9] == "53C110700":     #종합소득세 세액의계산 레코드
					record_53C110700.append(line)        
					if int(line[261:276])<0 :   wcIncomeTax  = (int(line[203:215])-wcMidTax/10)*-1     
					else:                         wcIncomeTax  =  (int(line[203:215])+wcMidTax/10)          
			elecfile.close() 
			record_ssn="";record_workyy="";singokubun=""
			cursor = connection.cursor()
			i=0;j=0
			for i,record in enumerate(record_51C110700):
				if i==0:
					record_ssn = record[9:22]
					record_workyy =  record[32:36]
					singokubun = record[26:28]
					strsql = "delete from Elec_Income where work_YY='" + record_workyy + "' and ssn='" + record_ssn + "'";print(strsql)
					cursor.execute(strsql)   
			for j,record in enumerate(record_53C110700):
				if j==0:
					print(record)
					str_ins = "INSERT into Elec_Income VALUES ('"
					str_ins += record_ssn + "', '" 
					str_ins += record_workyy + "', '" 
					str_ins += singokubun + "', '"	#'신고구분상세코드 01:정기신고, 02:기한후신고, 03:수정신고, 04:경정청구
					str_ins += record[9:22]  +  "','"			##종합소득금액
					str_ins += record[22:35]  +  "','"			#'소득공제
					str_ins += record[35:50]  +  "','"			##종합소득세_과세표준
					taxRate = '0'
					kp = int(record[35:50])
					if kp<12000000 :  taxRate = '600'
					elif kp<46000000 :  taxRate = '1500'
					elif kp<88000000 :  taxRate = '2400'
					elif kp<150000000 :  taxRate = '3500'
					elif kp<300000000 :  taxRate = '3800'
					elif kp<500000000 :  taxRate = '4000'
					elif kp<1000000000 :  taxRate = '4200'
					else:  taxRate = '4500'
					str_ins += taxRate  +  "','"
					str_ins += record[55:70]  +  "','"			#종합소득세_산출세액
					str_ins += record[70:85]  +  "','"			#종합소득세_세액감면
					str_ins += record[85:100]  +  "','"			#종합소득세_세액공제
					str_ins += record[130:145]  +  "','"			#종합소득세_결정세액
					str_ins += record[145:160]  +  "','"			#종합소득세_가산세
					str_ins += record[160:173]  +  "','"			#종합소득세_추가납부세액
					str_ins += record[173:186]  +  "','"			#종합소득세_합계
					str_ins += record[186:201]  +  "','"			#종합소득세_기납부세액
					str_ins += record[201:216]  +  "','"			#종합소득세_납부할총세액
					str_ins += record[216:231]  +  "','"			#종합소득세 납부특례세액_차감
					str_ins += record[231:246]  +  "','"			#종합소득세 납부특례세액_가산
					str_ins += record[246:261]  +  "','"			#종합소득세_분납할세액
					str_ins += record[261:276]  +  "','"			#종합소득세_신고기한내납부할세액
					str_ins += "000000000000000"  +  "','"			##지방소득세_과세표준
					str_ins += "00000"  +  "','"			          ##지방소득세_세율
					str_ins += "000000000000000"  +  "','"			##지방소득세_산출세액
					str_ins += "0000000000000"  +  "','"			  ##지방소득세_기납부세액
					str_ins += record[248:261]  +  "','"			##지방소득세_납부할총세액
					if int(record[261:276])<0 : 
						str_ins +=   str(  (int(record[203:215])-wcMidTax/10)*-1     )  +  "','"			##지방소득세_신고기한내납부할세액
					else:  str_ins += "0"+ str(  (int(record[203:215])+wcMidTax/10)     )  +  "','"			##지방소득세_신고기한내납부할세액
					str_ins += record[276:281]  +  "','"			#농어촌특별세_과세표준
					str_ins += record[291:296]  +  "','"			#농어촌특별세_세율
					str_ins += record[296:309]  +  "','"			#농어촌특별세_산출세액
					str_ins += record[333:346]  +  "','"			#농어촌특별세_결정세액
					str_ins += record[348:361]  +  "','"			#농어촌특별세_가산세
					str_ins += record[361:374]  +  "','"			#농어촌특별세_환급세액
					str_ins += record[374:387]  +  "','"			#농어촌특별세_합계
					str_ins += record[387:400]  +  "','"			#농어촌특별세_기납부세액
					str_ins += record[400:413]  +  "','"			#농어촌특별세_납부할총세액
					str_ins += record[413:426]  +  "','"			#농어촌특별세_분납할세액
					str_ins += record[426:439]  +  "','"			#농어촌특별세_신고기한내납부할세액
					str_ins += record[439:440]  +  "','"			#'비교과세적용구분코드
					str_ins += "000000000000000"  +  "','"			#지방소득세_세액감면
					str_ins += "000000000000000"  +  "','"			#지방소득세_세액공제
					str_ins += "000000000000000"  +  "','"			#지방소득세_결정세액
					str_ins += "000000000000000"  +  "','"			#지방소득세_가산세
					str_ins += "0000000000000"  +  "','"			#지방소득세_추가납부세액
					str_ins += "0000000000000"  +  "')"			#지방소득세_합계
					cursor.execute(str_ins)    ;print(str_ins)

					strUdt = "update tbl_income2 set YN_5='"+record[173:186]+"' where seq_no=(select top 1 seq_no from Mem_User where Ssn='"+record_ssn+"' and biz_type>3) and work_yy='"+record_workyy+"'"
					cursor.execute(strUdt)     ;print(strUdt)
				
				wcKwase = cols[2].text  # 과세기간    
				wcCorpGB = cols[3].text  # 신고서종류
				wcSingoGB = cols[4].text  # 신고구분
				wcChojung = cols[5].text  # 신고유형
				wcSangho = cols[6].text  # 상호
				wcSsnNo = cols[7].text  # 주민번호
				wcJupsuGB = cols[8].text  # 접수방법
				wcIssueT = cols[9].text  # 신고시각
				wcJubsuNum = cols[10].text  # 접수번호      
				wcJubsuPaper = cols[11].text  # 접수여부-서류      
				issueID = cols[30].text  # 제출자

				strsql = "Merge 종합소득세전자신고2 as A Using (select '"+wcSsnNo+"' as ssn_no,'"+wcKwase+"' as wcKwase,'"+wcSangho+"' as ceo_name) as B "
				strsql += "On A.과세년월=B.wcKwase  and A.주민번호=B.ssn_no and A.이름=B.ceo_name "
				strsql += " when matched then update set "
				strsql += "  신고구분 = '" + wcSingoGB + "'"
				strsql += " ,신고유형 = '" + wcChojung + "'"
				strsql += " ,이름 = '" + wcSangho.replace("'","") + "'"
				strsql += " ,주민번호 = '" + wcSsnNo + "'"
				strsql += " ,신고시각 = '" + wcIssueT + "'"    
				strsql += " ,신고번호 = '" + wcJubsuNum + "'"
				strsql += " ,접수여부 = '" + wcJubsuPaper + "'"    
				strsql += " When Not Matched Then insert values('" 
				strsql += wcKwase + "', '" 
				strsql += wcCorpGB + "', '"  
				strsql += wcSingoGB + "', '" 
				strsql += wcChojung + "', '"  
				strsql += wcSangho + "', '"  
				strsql += wcSsnNo + "', '"  
				strsql += wcIssueT + "','"  
				strsql += wcJubsuNum + "', '"  
				strsql += wcJubsuPaper + "', '"  
				strsql += issueID + "');"   
				print(strsql) 
				cursor = connection.cursor()
				cursor.execute(strsql)					
		elif flag=='corp' :
			wcKwase = cols[2].text  # 과세기간    
			wcCorpGB = cols[3].text  # 신고서종류
			wcSingoGB = cols[4].text  # 신고구분
			wcChojung = cols[5].text  # 신고유형
			wcSangho = cols[6].text  # 상호
			wcSangho = wcSangho.replace("'","")
			wcBizNo = cols[7].text  # 사업자번호
			wcJupsuGB = cols[8].text  # 접수방법
			wcIssueT = cols[9].text  # 신고시각
			wcJubsuNum = cols[10].text  # 접수번호      
			wcJubsuPaper = cols[11].text  # 접수여부-서류      
			issueID = cols[30].text  # 제출자
			
			strsql = "Merge 법인세전자신고2 as A Using (select '"+wcBizNo+"' as biz_no,'"+wcKwase+"' as work_YY,'"+wcChojung+"' as wcChojung) as B "
			strsql += "On A.과세년월=B.work_YY  and A.사업자번호=B.biz_no  and A.신고유형=B.wcChojung "
			strsql += f" when matched then update set 신고번호='{wcJubsuNum}',신고시각='{wcIssueT}',접수여부='{wcJupsuGB}',사용자ID='{issueID}'"
			strsql += f" When Not Matched Then insert values('{wcKwase}','{wcCorpGB}','{wcSingoGB}','{wcChojung}','{wcSangho}','{wcBizNo}','{wcJubsuNum}','{wcIssueT}','{wcJupsuGB}','{issueID}');"  
			print(strsql) 
			cursor = connection.cursor()
			cursor.execute(strsql)		

			record_81D100100 = ""
			record_83D100100 = ""
			record_83D100200 = ""
			record_83D100300 = ""
			record_83D103700_813 = ""
			record_83D103700_816 = ""
			record_83D103700_817 = ""
			record_83D103700_818 = ""
			record_83D103700_819 = ""
			record_83D103700_820 = ""
			record_83D103700_822 = ""
			record_83D103700_955 = ""
			record_83D103700_300 = ""
			record_83D103700_301 = ""
			record_83D100500_100 = ""
			record_83D100500_176 = ""
			record_83D100500_200 = ""
			record_93D108700 = 0
			record_94D108600 = ""

			while True:
				sr = elecfile.readline()
				if not sr:   break
				tmpcnt = utils.count_korean_characters(sr)
				if sr.startswith("81D100100"):						record_81D100100= sr
				elif sr.startswith("83D100200"):					record_83D100200 = sr[84:144]
				elif sr.startswith("83D100100"):						record_83D100100= sr
				elif sr.startswith("83D100300"):						record_83D100300= sr
				elif sr.startswith("83D103700"):
						if sr[9:11] == "01":
								
								if "접대" in sr:
										record_83D103700_813 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
								elif "벌금" in sr or "과금" in sr or "과태료" in sr:
										record_83D103700_816 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
								elif "세금과" in sr:
										record_83D103700_817 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
										print(record_83D103700_817)
								elif "무관" in sr and "이자" not in sr:
										record_83D103700_818 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
								elif "외화" in sr:
										record_83D103700_955 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )																				
								elif "이자" in sr and "인정" not in sr:
										record_83D103700_819 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
								elif "승용" in sr:
										record_83D103700_822 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )																				
								elif "감가" in sr:#'소득금액조정-감가상각비한도초과  ==> 업무용승용차 유보먼저 걸러야 순수 감비부인액이 아래 나온다
										record_83D103700_820 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )										
						elif utils.unicode_slice(sr, 9, 2) == "02":
								if "배당" in sr:
										record_83D103700_300 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )
								elif "외화" in sr:
										record_83D103700_301 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )			
								elif "승용" in sr:
										record_83D103700_301 = int(utils.mid_union(sr,58+tmpcnt,15).strip() )			
		    
				elif sr.startswith("83D100500"):
						if utils.mid_union(sr, 10+tmpcnt, 6) == "210071":
								record_83D100500_100 = int(utils.mid_union(sr, 16+tmpcnt, 16).strip())
						elif utils.mid_union(sr, 10+tmpcnt, 6) == "210102":
								record_83D100500_200 = int(utils.mid_union(sr, 16+tmpcnt, 16).strip())
						elif utils.mid_union(sr, 10+tmpcnt, 6) == "210176":
								record_83D100500_176 = int(utils.mid_union(sr, 16+tmpcnt, 16).strip())
				elif sr.startswith("94D108600"):
						record_94D108600 = int(utils.mid_union(sr,157+tmpcnt,15).strip()) 
				elif sr.startswith("93D108700"):
						record_93D108700 = int(utils.mid_union(sr,101+tmpcnt,15).strip() )
			elecfile.close() 
			tmpcnt = utils.count_korean_characters(record_81D100100)
			tmpcnt3 = utils.count_korean_characters(record_83D100300)
			wcKwasekikan = record_81D100100[11:17]
			corp_no = utils.mid_union(record_81D100100, 49, 13).strip()
			wcBizName = record_81D100100[61:100]
			wcBizNameCnt = utils.count_korean_characters(wcBizName)
			wcCeoName = utils.mid_union(record_81D100100, 122+wcBizNameCnt, 20).strip()
			wcCeoNameCnt = utils.count_korean_characters(wcCeoName)
			wcAddr = utils.mid_union(record_81D100100, 152+wcCeoNameCnt, 70).strip()	
			wcAddrCnt = utils.count_korean_characters(wcAddr)		
			wcYupTae = utils.mid_union(record_81D100100, 266+wcAddrCnt+wcCeoNameCnt+wcBizNameCnt, 41).strip()
			elements = wcYupTae.split()
			for element in elements:
				if not utils.contains_only_numbers(element):
					wcYupTae = element.strip()
					continue
    # Calculate the value containing only numbers for each element
    
			wcYupTaeCnt = utils.count_korean_characters(wcYupTae)		
			wcJongMok = utils.mid_union(record_81D100100, 296+wcYupTaeCnt+wcAddrCnt+wcCeoNameCnt+wcBizNameCnt, 50).strip()
			wcJongMokCnt = utils.count_korean_characters(wcJongMok)		
			wcYJCode = utils.mid_union(record_81D100100, 346+wcJongMokCnt+wcYupTaeCnt+wcAddrCnt+wcCeoNameCnt+wcBizNameCnt, 6).strip()

			wcSayupFiscalYear = utils.mid_union(record_81D100100, 352+tmpcnt, 8) + utils.mid_union(record_81D100100, 360+tmpcnt, 8)
			wcSayupKB = utils.mid_union(record_83D100100, 18, 2)
			wcTotCorpTax = int(utils.mid_union(record_83D100100, 197, 15).strip())  # Total corporate tax burden
			sanchul = utils.mid_union(record_83D100100, 152, 15).strip()  # Tax amount calculated total

			# Calculate total local tax based on 'sanchul'
			wcTotLocalTax = 0
			if float(sanchul) > 0:
					wcTotLocalTax = int(float(sanchul) / 100) * 10

			wcKibuExceed = utils.mid_union(record_83D100300, 70+tmpcnt3, 15).strip()  # Exceeding donation limit amount
			wcKibuInceed = utils.mid_union(record_83D100300, 85+tmpcnt3, 15).strip()  # Confirmed exceeding donation limit amount
			wcKackIncome = utils.mid_union(record_83D100300, 100+tmpcnt3, 15).strip()  # Income amount for each business year
			wcLimitTaxTarget = utils.mid_union(record_83D100300, 245+tmpcnt3, 15).strip()  # Minimum tax application target
			wcLimitTaxFree = utils.mid_union(record_83D100300, 275+tmpcnt3, 15).strip()  # Exclusion from minimum tax application
			userID = utils.mid_union(record_81D100100, 456+tmpcnt, 30).strip()
						
			cursor = connection.cursor()

			# DELETE 쿼리 실행
			strdel = f"DELETE FROM tbl_equityeval WHERE 사업연도말='{wcKwasekikan}' AND 사업자번호='{wcBizNo}'";print(strdel)
			cursor.execute(strdel)

			str_ins = "INSERT into tbl_equityeval VALUES ('"
			str_ins += wcBizNo + "', '" 
			str_ins += wcKwasekikan + "', '" 
			str_ins += corp_no + "', '" 
			str_ins += wcYupTae +  "', '"  # 
			str_ins += wcJongMok +  "', '"  # 
			str_ins += wcYJCode+  "', '"  # 
			str_ins += wcSayupFiscalYear + "', '" 
			str_ins += wcSayupKB + "', '"			#'회사종류
			str_ins +=  f"{record_83D100500_100}', '"	#'재무재표상 자산
			str_ins +=  "0', '"					#'자산가산1 : 평가차액
			str_ins +=  f"{record_93D108700}', '" #'자산가산2 : 법인세법상 유보금액
			str_ins +=  "0', '" 					#'자산가산3 : 유상증자 등
			str_ins +=  f"{record_83D100500_176}', '"			#'자산차감1 : 선급비용
			str_ins +=  "0', '" 		#'자산차감2 : 증자일전의잉여금의유보액
			str_ins +=  f"{record_83D100500_200}', '"		#'재무재표상 부채
			str_ins +=  "0', '"			#'부채가산배당
			str_ins +=  "0', '"			#'부채가산퇴추
			str_ins +=  f"{wcKackIncome}', '"			#'각사업연도소득금액
			str_ins +=  f"{record_83D103700_301}', '"			#'환급이자 ==> 이월된 업무용승용차 손금추인액 25.8.26
			str_ins +=  f"{record_83D103700_300}', '"			#'소득가산배당
			str_ins +=  f"{wcKibuInceed}', '"			#'소득가산기부추인
			str_ins +=  f"{record_83D103700_816}', '"			#'벌금
			str_ins +=  f"{record_83D103700_817}', '"			#'공과금
			str_ins +=  f"{record_83D103700_818}', '"			#'업무무관
			str_ins +=  f"{record_83D103700_822}', '"			#징수불  ==> 업무용승용차 손금불산입 25.8.26
			str_ins +=  f"{wcKibuExceed}', '"			#'기부금
			str_ins +=  f"{record_83D103700_813}', '"			#'접대비
			str_ins +=  f"{record_83D103700_955}', '"			#과다경비 ==> 외화환산손실 25.8.26
			str_ins +=  f"{record_83D103700_819}', '"			#'지급이자
			str_ins +=  f"{record_83D103700_820}', '"			#'감비추인
			str_ins +=  f"{wcTotCorpTax}', '"			#'법인세
			str_ins +=  f"{record_83D100200}', '"			#'농특세
			str_ins += f"{wcTotLocalTax}', '"			#'지방세
			str_ins +=  f"{record_93D108700}', '"			#'익금유보
			str_ins +=  "0', '"			#'손금유보
			str_ins +=  f"{record_94D108600}', '"			#'결손금누계
			str_ins +=  f"{wcLimitTaxTarget}', '"			#'최저한세적용대상
			str_ins += f"{wcLimitTaxFree}','"			#'최저한세적용제외
			str_ins += str(int(utils.mid_union(record_83D100100,62,15).strip()))  +  "','"			#'수입금액
			str_ins += str(int(utils.mid_union(record_83D100100,77,15).strip()))  +  "','"			#'과세표준_법인세
			str_ins += str(int(utils.mid_union(record_83D100100,92,15).strip()))  +  "','"			#'과세표준_토지
			str_ins += str(int(utils.mid_union(record_83D100100,107,15).strip()))  +  "','"			#'과세표준_합계
			str_ins += str(int(utils.mid_union(record_83D100100,122,15).strip()))  +  "','"			#'산출세액_법인세
			str_ins += str(int(utils.mid_union(record_83D100100,137,15).strip()))  +  "','"			#'산출세액_토지
			str_ins += str(int(utils.mid_union(record_83D100100,152,15).strip()))  +  "','"			#'산출세액_합계
			str_ins += str(int(utils.mid_union(record_83D100100,167,15).strip()))  +  "','"			#'총부담세액_법인세
			str_ins += str(int(utils.mid_union(record_83D100100,182,15).strip()))  +  "','"			#'총부담세액_토지
			str_ins += str(int(utils.mid_union(record_83D100100,197,15).strip()))  +  "','"			#'총부담세액_합계
			str_ins += str(int(utils.mid_union(record_83D100100,212,15).strip()))  +  "','"			#'기납부세액_법인세
			str_ins += str(int(utils.mid_union(record_83D100100,227,15).strip()))  +  "','"			#'기납부세액_토지
			str_ins += str(int(utils.mid_union(record_83D100100,242,15).strip()))  +  "','"			#'기납부세액_합계
			str_ins += str(int(utils.mid_union(record_83D100100,257,15).strip()))  +  "','"			#'차감납부세액_법인세
			str_ins += str(int(utils.mid_union(record_83D100100,272,15).strip()))  +  "','"			#'차감납부세액_토지
			str_ins += str(int(utils.mid_union(record_83D100100,287,15).strip()))  +  "','"			#'차감납부세액_합계
			str_ins += str(int(utils.mid_union(record_83D100100,302,15).strip()))  +  "','"			#'분납세액
			str_ins += str(int(utils.mid_union(record_83D100100,317,15).strip()))  +  "'"			#'차감납부세액
			str_ins += ")"	;print(str_ins)
			cursor.execute(str_ins)
			
			# 회원 정보 업데이트 쿼리 실행
			# str_update = f"UPDATE mem_user SET uptae='{wcYupTae}', Jongmok='{wcJongMok}', Ceo_name='{wcCeoName}', biz_addr1='{wcAddr}' WHERE biz_no='{wcBizNo}'"
			str_update = f"UPDATE mem_user SET  Jongmok='{wcJongMok}', Ceo_name='{wcCeoName}', biz_addr1='{wcAddr}' WHERE biz_no='{wcBizNo}'"
			cursor.execute(str_update)
			print(str_update)
			# 변경 사항을 커밋하여 데이터베이스에 반영
			connection.commit()
			
				
		return 1


class ACCOUNT:
      

	def semusarang_Acct_Excel(seqno,work_yy,fiscalMM,biz_type,endMM):
		pyautogui.hotkey('ctrl', 'enter');pyperclip.copy('분개장')    #메뉴검색
		pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter')
		time.sleep(1)
		# 연도말일 경우     분기별 업데이트는 종료월일 지정 / 
		if len(endMM)==2:
			pyautogui.press('enter',presses=2, interval=0.3);pyautogui.write(endMM);time.sleep(0.3);pyautogui.press('enter',presses=7, interval=0.3);
		else:
			pyautogui.press('enter',presses=10, interval=0.3)
		time.sleep(2) #필수  
		if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_hasNoExactData.png'):
			pyautogui.press('esc',presses=2, interval=0.3)
			time.sleep(0.25)  
		else:#결과값이 있으면
			pyautogui.hotkey('ctrl','e');    time.sleep(0.5)
			writeFileName = str(seqno)+"_"+str(work_yy)
			pyautogui.write(writeFileName);    time.sleep(0.3)
			pyautogui.press('enter',presses=1, interval=1)
			time.sleep(4)
			# 엑셀닫고 열린화면 닫기
			utils.semusarang_Excelclose_Openmenuclose()  #
			downloads = 'C:\\NewGen\\Rebirth\\리버스문서보관함'
			file_name = max([downloads + "\\" + f for f in os.listdir(downloads)],key=os.path.getctime)  
			if  downloads+"\\"+writeFileName+".xls"==file_name:
				df = pd.read_excel(file_name,header=1, dtype = {'전표번호':str,'코드': str})
				df = df.fillna('')  # 3. excel 의 nill 값을 '' 로 변환
				cursor = connection.cursor()
				if fiscalMM=="12":
					str_del = "delete from DS_SlipLedgr2 where seq_no="+ str(seqno)  + " and work_yy='" + str(work_yy)  + "'   and not Tran_Dt='00-00'" 
					cursor.execute(str_del)
					str_del_feedback = "delete from DS_SlipLedgr2_Feedback where seq_no="+ str(seqno)  +  " and work_yy='" + str(work_yy)  + "'"
					cursor.execute(str_del_feedback)
				else:#fiscalMM!="12"
					fiscalDate=""
					if fiscalMM == "6": fiscalDate = "06-30"
					elif fiscalMM == "3": fiscalDate = "03-31"
					str_del = "delete from DS_SlipLedgr2 where seq_no="+ str(seqno)  
					str_del += " AND  ( (work_yy = "+ str(work_yy-1)  +" AND Tran_Dt > '"+ fiscalDate +"' ) OR (work_yy = "+ str(work_yy)  +" AND Tran_Dt <= '"+ fiscalDate +"') ) "
					str_del += " and not Tran_Dt='00-00'" 
					cursor.execute(str_del)
					str_del_feedback = "delete from DS_SlipLedgr2_Feedback where seq_no="+ str(seqno)  + " and work_yy='" + str(work_yy)  + "'"
					cursor.execute(str_del_feedback)
				amt_sales=0
				amt_cost=0
				for row in df.itertuples():
					if len(row[1])==10:
						CRDR		= row[3]
						acnt_cd		= str(row[4]).replace(".0","")[-3:]
						acnt_nm		= str(row[5])
						Tran_Dt_Year	= row[1][:4]  
						Tran_Dt_MMDD	= row[1][5:10]
						# if proValue=1 세무사랑인경우
						Remk		= str(row[8])
						Trader_Code = str(row[9]).replace(".0","")
						Trader_Name	= str(row[10])
						billKind	= str(row[20])      
						Tran_Cr		= row[6]
						Tran_Dr		= row[7]
						Slip_No		= str(row[2]).replace(".0","")
						Trader_Bizno = str(row[11])
						strsql = "INSERT INTO DS_SlipLedgr2 VALUES ('"+str(seqno)+"', '"+Tran_Dt_Year + "', '" + acnt_cd + "', '" + acnt_nm + "', '"+Tran_Dt_MMDD+"', '"+Remk+"', '"+ Trader_Code +"', '"+Trader_Name+"', '"+Trader_Bizno + "', '"+Slip_No+"',   '"+billKind+"','" + CRDR + "', '" + str(Tran_Cr) + "', '" + str(Tran_Dr) + "', '', '', '', '', '', '', '', '', '', left(replace(GETDATE(),' ',''),8))"
						print(strsql)
						cursor.execute(strsql)
						if int(acnt_cd)>=401 and int(acnt_cd)<=430 :
							amt_sales = amt_sales + Tran_Dr - Tran_Cr
						elif  (int(acnt_cd)>=451 and int(acnt_cd)<=470) or (int(acnt_cd)>501 and int(acnt_cd)<=999) :
							amt_cost =  amt_cost + Tran_Cr - Tran_Dr

				cursor.execute("Exec up_Act_PreBSInquiry '" + str(work_yy) + "','" +str(seqno)+ "'")

				tableName = "tbl_income2"
				if int(biz_type)<4 : tableName = "tbl_corporate2"
				strsql = "Merge " + tableName + " as A Using (select '"+str(seqno)+"' as seq_no,'"+str(work_yy)+"' as work_YY) as B "
				strsql += "On A.seq_no=B.seq_no  and A.work_YY=B.work_YY "
				#strsql += " when matched then update set YN_1= " + str(amt_sales)+  ",YN_2= " + str(amt_cost)+  ",YN_3= " + str(amt_sales - amt_cost)
				strsql += " when matched then update set YN_2= " + str(amt_cost)+  ",YN_3= " + str(amt_sales - amt_cost)
				strsql += " When Not Matched Then insert values(" + seqno + "," + str(work_yy)  + "," + str(amt_sales)  + "," + str(amt_cost) + "," + str(amt_sales - amt_cost) + ",0,0,0,0,0,'','',0,'',0,0,0);"    
				print(strsql) 
				cursor.execute(strsql)
				#======================== 월별 업로드 현황
				strsql = "select left(tran_dt,2) work_mm from DS_SlipLedgr2 where seq_no=" + seqno + " and Work_YY="+ str(work_yy) +" and left(tran_dt,2)!='00' group by left(tran_dt,2) order by left(tran_dt,2)"
				cursor.execute(strsql)
				results = cursor.fetchall()
				connection.commit()
				for work_mm in results:
					strsql3 =  " Merge tbl_mng_jaroe as A Using (select '"+str(seqno)+"' as seq_no,'"+str(work_yy)+"' as work_YY, '"+ str(int(work_mm[0])) +"' as work_MM) as B "
					strsql3 += " On A.seq_no=B.seq_no  and A.work_YY=B.work_YY and A.work_MM=B.work_MM "
					strsql3 += " when matched then update  set YN_5='1', YN_6='1', YN_7='1', YN_8='1', YN_9='1' "
					strsql3 += " When Not Matched Then insert  values("+ "'" + seqno + "','" + str(work_yy) + "','"+ str(int(work_mm[0])) + "'"
					for j in range(1,15):
						if j>=5 and j<=9 : strsql3 = strsql3 + ",'1'" 
						else:              strsql3 = strsql3 + ",'0'" 
					strsql3 = strsql3 +",'');"
					print(strsql3)
					cursor.execute(strsql3)
				connection.close()
				os.remove(file_name)
			else:
				print('작성된 분개장파일이 없습니다.')


	#이달의 회계처리 - 해당월 최초분개인 경우 / 수정신고 있는 경우 추가할 것
	def semusarang_MakeAccount_ThisMonth():
		utils.semusarang_Menu_Popup('급여자료회계처리');time.sleep(1)
		# pyautogui.hotkey('ctrl', 'enter');pyperclip.copy('급여자료회계처리')    #메뉴검색
		# pyautogui.hotkey('ctrl', 'v');pyautogui.press('enter');time.sleep(3)
		pyautogui.press('enter',presses=4,interval=0.3)
		pyautogui.press('left');time.sleep(0.25);print('체크박스로이동')
		pyautogui.press('space');time.sleep(0.25);print('체크박스 선택')
		pyautogui.press('f7');time.sleep(1);print('분개설정')
		pyautogui.write('1');time.sleep(0.35);print('전표발생일-귀속월의 말일')
		pyautogui.press('tab');pyautogui.press('enter');time.sleep(3.5);print('설정반영 - 2초이상 소요')
		pyautogui.press('f4');time.sleep(0.25);print('전표추가')
		pyautogui.press('enter');time.sleep(0.25);print('전표추가 - 예')
		pyautogui.press('esc',presses=4,interval=0.25)
		return 1
	def semusarang_MakeAccount_Insa_A(flag,biz_no,biz_type,workyy,text_mm):
		whiteBtn = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_CheckAll_white.png'
		blueBtn = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_CheckAll.png'
		deCheck = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_DeCheckAll.png'
		accDate = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Insa_AccDate.png'
		if flag=='a01':
			utils.semusarang_Menu_Popup('급여자료회계처리');time.sleep(1)
			pyautogui.write('01');time.sleep(0.25);pyautogui.write(text_mm);time.sleep(0.25);pyautogui.press('enter',presses=2,interval=0.3)
			if int(text_mm)>1: 
				if pyautogui.locateCenterOnScreen(whiteBtn):  pyautogui.click(pyautogui.locateCenterOnScreen(whiteBtn));    time.sleep(1); print('whitebtn 클릭')
				else: print('whitebtn 없음'); return 1
			else              :pyautogui.click(pyautogui.locateCenterOnScreen(blueBtn));    time.sleep(1); print('bluebtn 클릭')
			pyautogui.press('f6');time.sleep(1);print('전표삭제');pyautogui.press('enter');time.sleep(int(text_mm)*0.5)
			pyautogui.press('f12');time.sleep(1);print('새로불러오기');pyautogui.press('enter');time.sleep(int(text_mm)*0.5)
			if pyautogui.locateCenterOnScreen(deCheck):  pyautogui.click(pyautogui.locateCenterOnScreen(deCheck));    time.sleep(1); print('deCheck 클릭') 
			if int(text_mm)>1: 
				if pyautogui.locateCenterOnScreen(whiteBtn):  pyautogui.click(pyautogui.locateCenterOnScreen(whiteBtn));    time.sleep(1); print('whitebtn 클릭')
				else: print('whitebtn 없음'); return 1
			else              :pyautogui.click(pyautogui.locateCenterOnScreen(blueBtn));    time.sleep(1); print('bluebtn 클릭')
			pyautogui.press('f7');time.sleep(1);print('분개설정'); pyautogui.write('1');time.sleep(0.35);print('전표발생일-귀속월의 말일')
			pyautogui.press('tab');time.sleep(0.4);pyautogui.press('enter');time.sleep(2+int(text_mm)*0.5);print('설정반영 - 2초이상 소요')
			pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(int(text_mm)*0.5);print('전표추가 - 예')
			pyautogui.press('esc',presses=4,interval=0.25)
		elif flag=='a03':
			strsql = " select right(과세연월,2), a03 from 원천세전자신고 where 사업자등록번호='"+biz_no+"' and left(과세연월,4)="+workyy+" and a03>0 order by 과세연월"
			cursor = connection.cursor()
			cursor.execute(strsql);print(strsql)
			results = cursor.fetchall()
			connection.commit()
			connection.close()    
			for result in results:       
				utils.semusarang_Menu_Popup('일용직급여자료회계처리');time.sleep(1)
				pyautogui.press('enter');pyautogui.write(result[0]);time.sleep(0.25);pyautogui.write(result[0]);time.sleep(0.25);pyautogui.press('enter');time.sleep(0.5)
				blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
				if blueXY:              
					pyautogui.click(pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7));    time.sleep(1); print('bluebtn 클릭')
					pyautogui.press('f6');time.sleep(1);print('전표삭제');pyautogui.press('enter');time.sleep(int(text_mm)*0.5)
					if blueXY:  pyautogui.click(blueXY);    time.sleep(1); print('bluebtn 클릭')
					pyautogui.press('f8');time.sleep(1);print('기본계정설정'); 
					pyautogui.write('805');pyautogui.press('enter',presses=5,interval=0.3);
					if biz_type>3:pyautogui.write('101');pyautogui.press('enter')
					else          :pyautogui.write('103');pyautogui.press('enter')
					pyautogui.press('tab');time.sleep(0.4)
					pyautogui.press('f12');time.sleep(1);print('새로불러오기');pyautogui.press('enter');time.sleep(int(text_mm)*0.5);pyautogui.write(workyy+result[0]+'25')
					if blueXY:  pyautogui.click(blueXY);    time.sleep(1); print('bluebtn 클릭')
					pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(int(text_mm)*0.5);print('전표추가 - 예')    
				pyautogui.press('esc',presses=4,interval=0.25)
		elif flag=='a30' or  flag=='a20':
			strsql = " select right(과세연월,2), a30 from 원천세전자신고 where 사업자등록번호='"+biz_no+"' and left(과세연월,4)="+workyy+" and a30>0 order by 과세연월"
			cursor = connection.cursor()
			cursor.execute(strsql);print(strsql)
			results = cursor.fetchall()
			connection.commit()
			connection.close()    
			for result in results:    
				utils.semusarang_Menu_Popup('사업소득자료회계처리');time.sleep(1)
				pyautogui.write(result[0]);time.sleep(0.25);pyautogui.press('enter');pyautogui.write(result[0]);time.sleep(0.25);pyautogui.press('enter');time.sleep(0.5)
				accDateXY =  pyautogui.locateCenterOnScreen(accDate,confidence=0.7)
				if accDateXY: pyautogui.click(accDateXY);time.sleep(0.7);print('Accnt Date checked')
				blueXY = pyautogui.locateCenterOnScreen(blueBtn,confidence=0.7)
				if blueXY: 
					pyautogui.click(blueXY);    time.sleep(1); print('bluebtn 클릭')
					pyautogui.press('f6');time.sleep(0.25);print('전표삭제');pyautogui.press('enter');time.sleep(0.25);print('전표삭제 - 예')
					pyautogui.press('f4');time.sleep(0.25);print('전표추가');pyautogui.press('enter');time.sleep(0.25);print('전표추가 - 예')
				else:print('blue Button does not exist')
				pyautogui.press('esc',presses=4,interval=0.25)
		elif flag=='a40':#기타
			utils.semusarang_Menu_Popup('기타이자배당자료회계처리');time.sleep(1)
			confirm = pyautogui.confirm('기타소득 회계처리 관련 조치하고 확인 누르세요. 취소누르면 다음 프로세스로 이동')
			if confirm=='Cancel':return False   #중단 
			else : pyautogui.press('esc',presses=4,interval=0.25)
		elif flag=='a50':#이자
			utils.semusarang_Menu_Popup('기타이자배당자료회계처리');time.sleep(1)
			confirm = pyautogui.confirm('이자소득 회계처리 관련 조치하고 확인 누르세요. 취소누르면 다음 프로세스로 이동')
			if confirm=='Cancel':return False   #중단 
			else : pyautogui.press('esc',presses=4,interval=0.25)
		elif flag=='a60':#배당
			utils.semusarang_Menu_Popup('기타이자배당자료회계처리');time.sleep(1)
			confirm = pyautogui.confirm('배당소득 회계처리 관련 조치하고 확인 누르세요. 취소누르면 다음 프로세스로 이동')
			if confirm=='Cancel':return False   #중단 
			else : pyautogui.press('esc',presses=4,interval=0.25)
		return 1  

	def semusarang_MakeAccount_Insa_B(seq_no,work_yy,text_mm):
		strsql = " select  max(biz_no),max(year(getdate())-year(reg_date)),a.seq_no,max(fiscalMM),max(biz_type),max(duzon_id),max(과세연월),"
		strsql +=" sum(a01) a01,sum(a03) a03,sum(a20) a20,sum(a30) a30,sum(a40) a40,sum(a50) a50,sum(a60) a60 "
		strsql += " from mem_user a,mem_deal b,원천세전자신고 c where a.seq_no=b.seq_no and a.biz_no=c.사업자등록번호 and keeping_yn='Y' and kijang_yn='Y'   "
		strsql += " and  left(과세연월,4)='"+str(work_yy)+"'  "
		strsql += " and a.seq_no ='"+seq_no+"'   "    
		strsql += " group by a.seq_no,biz_name order by a.seq_no/1,biz_name " 
		cursor = connection.cursor();print(strsql)
		cursor.execute(strsql)
		result = cursor.fetchall()
		connection.commit()
		connection.close()    
		if result:
			if result[0][7]>0: semusarang_MakeAccount_Insa_AA('a01',result[0][0],result[0][4],str(work_yy),text_mm) #a01
			if result[0][8]>0: semusarang_MakeAccount_Insa_AA('a03',result[0][0],result[0][4],str(work_yy),text_mm) #a03
			if result[0][9]>0: semusarang_MakeAccount_Insa_AA('a20',result[0][0],result[0][4],str(work_yy),text_mm) #a20
			if result[0][10]>0: semusarang_MakeAccount_Insa_AA('a30',result[0][0],result[0][4],str(work_yy),text_mm)  #a30
			if result[0][11]>0: semusarang_MakeAccount_Insa_AA('a40',result[0][0],result[0][4],str(work_yy),text_mm)  #a40 - 기타
			if result[0][12]>0: semusarang_MakeAccount_Insa_AA('a50',result[0][0],result[0][4],str(work_yy),text_mm)
			if result[0][13]>0: semusarang_MakeAccount_Insa_AA('a60',result[0][0],result[0][4],str(work_yy),text_mm)
		return 1

	def semusarang_KyulsanAccnt(work_mm):
		utils.semusarang_Menu_Popup('결산자료입력');time.sleep(1);pyautogui.press('enter');pyautogui.write(work_mm);time.sleep(1)
		pyautogui.press('enter');time.sleep(0.3);pyautogui.press('f3');time.sleep(0.3)
		pyautogui.press('enter');time.sleep(0.3);pyautogui.press('left');time.sleep(0.3);pyautogui.press('enter');time.sleep(0.3)
		pyautogui.press('esc',presses=2,interval=0.3);time.sleep(0.3)
		return 1


class PAY:


	# 세무사랑 간이지급 전자신고
	def electric_Issue_KNZK(flag,bizNo,workyear,period,semusarangID):
		if flag=='1' or flag=='2':utils.semusarang_MenuCode_Popup('2150','간이지급명세서전자신고')#semusarang_Menu_Popup('간이지급명세서전자신고')
		elif flag=='3'          :utils.semusarang_MenuCode_Popup('2072','일용근로소득지급명세서전자신고')
		memuser = MemUser.objects.get(biz_no=bizNo[:3]+"-"+bizNo[3:5]+"-"+bizNo[5:10])  
		semusarang_elec_ID = SemusarangID_Check(flag,memuser.seq_no,workyear,period,'KwaseKikan','KwaseyuHyung',semusarangID)  
		#전자신고 아이디 세팅
		pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('up');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)
		pyautogui.press('right');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.hotkey('ctrl','2');time.sleep(0.5)
		pyautogui.write('1');time.sleep(0.3) #필수    #신고인구분 :세무대리인신고
		if flag=='1' or flag=='2':pyautogui.write(flag);print(f"명세서구분 : {flag}");time.sleep(0.3) #필수    #명세서구분 : 1. 근로소득 2.사업소득
		pyautogui.write(period);time.sleep(0.3);print(f"제출대상구분 : {period}") #필수    #제출대상구분 : 1.상반기 2.하반기    사업 : 해당월
		pyautogui.press('enter',presses=3, interval=0.3) #제출연월일 & 회사구분
		pyautogui.write('1'); time.sleep(0.3);pyautogui.press('enter',presses=3,interval=0.3) ;  time.sleep(0.3) #필수  #
		pyperclip.copy('c:\ABC'); pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)#'c:\ABC'
		pyautogui.press('enter');time.sleep(3) 
		if  pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_hasNoExactData(Exist).png',confidence=0.7):
			pyautogui.press('enter');print('조회조건에 맞는 데이터가 존재하지 않습니다.확인')
			pyautogui.press('esc', presses=4, interval=0.3);print('esc 4회');time.sleep(0.5)
			return 0
		else:
			print('팝업없음 : 조회조건에 맞는 데이터가 존재하지 않습니다.')         
		pyautogui.press('f4') ;  time.sleep(1) ;  pyautogui.press('enter');time.sleep(0.5) 
		pyautogui.press('esc', presses=3, interval=1)  

		if flag=='1':  SS_ElecIssue('Kani-Kunro',memuser.seq_no,workyear,period,1)
		elif flag=='2':  SS_ElecIssue('Kani-Saup',memuser.seq_no,workyear,period,1)
		elif flag=='3':  SS_ElecIssue('Kani-Ilyoung',memuser.seq_no,workyear,period,1)
		return 1

	# 지급명세서 - 사업/이자/배당/기타/퇴직    
	def semusarang_Menu_ZZJS(flag,bizNo,workyear,period,htxLoginID):
		if flag=='01':				utils.semusarang_Menu_Popup_App('지급명세서전자신고(연말정산)')  
		elif flag=='20':			utils.semusarang_Menu_Popup_App('퇴직소득원천징수영수증')          
		elif flag=='30':			utils.semusarang_Menu_Popup_App('사업소득지급명세서(연간집계표)')  
		elif flag=='60' or flag=='50':		utils.semusarang_Menu_Popup_App('이자배당소득원천징수영수증')	
		elif flag=='40':			utils.semusarang_Menu_Popup_App('기타소득지급명세서(영수증)')	     
		
		if flag!='01'	:
			pyautogui.press('enter',presses=4, interval=0.5);time.sleep(1)   #지급연도
			if flag=='60' or flag=='50':
				pyautogui.press('f8');time.sleep(0.5)
				location = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_MagamCancelYN_Insa_Kyumung.png', confidence=0.7)
				if location:      pyautogui.press('N');time.sleep(0.5);      
				else: pyautogui.press('f8');time.sleep(0.5);print('마감 ')				
			else:pyautogui.press('f8',presses=2, interval=0.5);time.sleep(1)   #마감
			pyautogui.press('esc',presses=3, interval=0.5);time.sleep(1)   #종료
			utils.semusarang_Menu_Popup_App('지급명세서전자신고(연말정산)')  ;time.sleep(1)

		flagZZMS = "ZZMS-"
		pyautogui.press('enter');time.sleep(0.5)  #엔터한번 더해야 들어온다
		memuser = MemUser.objects.get(biz_no=bizNo[:3]+"-"+bizNo[3:5]+"-"+bizNo[5:10])  
		semusarang_elec_ID = SemusarangID_Check(flag,memuser.seq_no,workyear,period,'KwaseKikan','KwaseyuHyung',htxLoginID)  
		#전자신고 아이디 세팅
		pyautogui.hotkey('ctrl','1');time.sleep(0.5);pyautogui.press('up');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)
		pyautogui.press('right');time.sleep(0.3);pyperclip.copy(semusarang_elec_ID);  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5);pyautogui.hotkey('ctrl','2');time.sleep(0.5)	
		pyautogui.write('1');time.sleep(0.5)  #신고인구분
		if   flag=='01': pyautogui.write('1');flagZZMS += "Kunro"
		elif flag=='20': pyautogui.write('2');flagZZMS += "Toijik"
		elif flag=='30': pyautogui.write('4');flagZZMS += "Saup"
		elif flag=='40': pyautogui.write('3');flagZZMS += "Kita"
		elif flag=='60' or flag=='50': pyautogui.write('6');flagZZMS += flag
		time.sleep(0.5);pyautogui.press('enter',presses=3, interval=0.5);time.sleep(0.5)
		pyautogui.write('1');   time.sleep(0.3) #회사구분
		pyautogui.press('enter',presses=3, interval=0.5);time.sleep(1)   #지급연도
		pyperclip.copy('c:\ABC'); pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)#'c:\ABC'
		pyautogui.press('enter');time.sleep(3) 			 #필수
		pyautogui.press('f4') ;  time.sleep(1) ;  pyautogui.press('enter');time.sleep(0.5) 
		pyautogui.press('esc', presses=3, interval=1) 						

		SS_ElecIssue(flagZZMS,memuser.seq_no,workyear,period,1)
		return 1

	def SS_Zkzs(workyear,driver,directory,fileName):
		print('신고 안내자료 클릭');
		driver.find_element(By.ID,'tabControl1_tab_tabs3').click();time.sleep(0.5)
		driver.find_element(By.ID,'group10121').click();time.sleep(1);print('일괄조회')  #원천징수영수증 
		wait = WebDriverWait(driver, 30)
		iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#UTERNAAT71_iframe")))
		driver.switch_to.frame(iframe)
		element = driver.find_element(By.CSS_SELECTOR,"#mskApplcYn_input_1")
		radio = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#mskApplcYn_input_1')));     
		driver.execute_script("arguments[0].click();", element)		;print('개인정보공개전환')
		# radio.click()
		max_num = 0;index_400 = 0;target_name = fileName.split('-')[0];print(target_name)
		if directory.find('AAA')!=-1:index_400 = 1
		matched_files = []
		for files2 in os.listdir(directory):
			if index_400 == 0:
				matched_files.append(files2)
			else:
				if files2.find(target_name) != -1:              matched_files.append(files2)
		for files in matched_files:
			fname, extension = os.path.splitext(files)
			if fname.split('-')[index_400].isdigit():
				if index_400==1 and fname.split('-')[0]==target_name:
						num = int(fname.split('-')[index_400])
						max_num = max(max_num, num)
				elif index_400==0:
						num = int(fname.split('-')[index_400])
						max_num = max(max_num, num)
		table = driver.find_element(By.CSS_SELECTOR,'#grdList_body_table');  print("테이블획득"); time.sleep(3)# driver.implicitly_wait(30)    
		tbody = table.find_element(By.CSS_SELECTOR,'#grdList_body_tbody'); print("티바디획득");print('조회할테이블수:'+str(len(tbody.find_elements(By.TAG_NAME,'tr'))))
		rows = tbody.find_elements(By.TAG_NAME, 'tr')
		for j, tr in enumerate(rows):
			td = tr.find_elements(By.TAG_NAME,"td")
			txtYear="";txtTitle="";txtBizName="";txtBizNo="";txtID="";saveName=str(max_num+j+1)
			if index_400==1:saveName=fileName.split('-')[0]+"-"+str(max_num+j+1)
			for i, tag in enumerate(td):
				id_td = tag.get_attribute('id');print(id_td)
				txt_td = tag.get_attribute("innerText");print(txt_td)                
				if i==2:txtYear = txt_td
				if i==3:txtTitle = txt_td
				if i==5:txtBizName = txt_td.replace('주식회사 ','')
				if i==6:txtBizNo = txt_td
				if i==7:txtID = id_td;
			tail = ""
			if txtYear==str(workyear-1):
				if txtTitle.find('사업')!=-1:   tail="-사업원천징수("+txtBizNo.replace('-','')+txtBizName+")"  
				elif txtTitle.find('근로')!=-1:   tail="-근로원천징수("+txtBizNo.replace('-','')+txtBizName+")"  
				elif txtTitle.find('기타')!=-1:   tail="-기타원천징수("+txtBizNo.replace('-','')+txtBizName+")" 
				elif txtTitle.find('연금')!=-1:   tail="-연금원천징수("+txtBizNo.replace('-','')+txtBizName+")"  
				elif txtTitle.find('이자')!=-1:   tail="-이자원천징수("+txtBizNo.replace('-','')+txtBizName+")"  
				elif txtTitle.find('배당')!=-1:   tail="-배당원천징수("+txtBizNo.replace('-','')+txtBizName+")"  
				saveName+=tail
			if not utils.find_similar_strings(matched_files, tail):      
				utils.Htx_Popup_Print(driver,txtID,saveName,directory,False)
				iframe = driver.find_element(By.CSS_SELECTOR,'#UTERNAAT71_iframe');      driver.switch_to.frame(iframe);      time.sleep(1); print('iframe 전환txppIframe')
		time.sleep(1)#;driver.find_element(By.ID,'trigger93').click();print('지급조서(원천징수영수증) 닫기버튼')  #  group2745
		element = driver.find_element(By.ID,'trigger93');print('지급조서(원천징수영수증) 닫기버튼')
		driver.execute_script("arguments[0].click();", element)

	def semusarang_Pay_Monthly_Excel(seqno,work_yy,startMM,endMM,menuName,cursor):
		pyautogui.hotkey('ctrl', 'enter');  time.sleep(0.5)   ;  pyperclip.copy(menuName) 
		pyautogui.hotkey('ctrl', 'v');  time.sleep(0.5)  ;  pyautogui.press('enter');  time.sleep(1)  
		#수당공제합계
		pyautogui.hotkey('ctrl', '3') ;  time.sleep(1.5)  ;  #pyautogui.press('enter');time.sleep(1)
		if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_ZKJS_NoPerson.png'): 
			pyautogui.press('esc',presses=2,interval=0.3);print('등록된 직원이 없는 경우')
			return 1
		print(f"시작월:{startMM}")
		print(f"종료월:{endMM}")
		for work_mm in range(int(startMM),int(endMM)+1):
			pyautogui.press('enter',presses=3, interval=0.3)#학생수 체크
			time.sleep(0.3) #필수   
			if work_mm<10:  
				pyautogui.write(str(work_mm));      pyautogui.press('enter')
				pyautogui.write(str(work_mm));      pyautogui.press('enter')
			else:    
				print(work_mm)
				pyautogui.write(str(work_mm));      time.sleep(0.3)
				pyautogui.write(str(work_mm));      time.sleep(0.3)
			time.sleep(1) #필수
			#결과값이 없으면
			print('조회기간에 해당하는 데이터가 없습니다:')
			print(pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_hasNoData.png',confidence=0.7))
			if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_hasNoData.png',confidence=0.7):
				pyautogui.press('esc',presses=3,interval=0.3);print('조회기간에 해당하는 데이터가 없습니다');				 
				pyautogui.hotkey('ctrl', 'enter');  time.sleep(0.5)   ;  pyperclip.copy(menuName) 
				pyautogui.hotkey('ctrl', 'v');  time.sleep(0.5)  ;  pyautogui.press('enter');  time.sleep(1)  
				pyautogui.hotkey('ctrl', '3') ;  time.sleep(1.5) 
				continue; 
			else:
				print("엑셀업로드대기")
				pyautogui.hotkey('ctrl','e')
				time.sleep(1.5)
				pyautogui.press('enter',presses=1, interval=1)
				time.sleep(3.5)    
				downloads = 'C:\\NewGen\\Rebirth\\리버스문서보관함'
				if os.listdir(downloads):
					file_name = max([downloads + "\\" + f for f in os.listdir(downloads)],key=os.path.getctime)  
					if file_name.find('급여지급현황') and os.path.splitext(file_name)[1]=='.xls':
						try:
							with open(file_name, 'rb') as f:
								df = pd.read_excel(f, header=1)
						except Exception as e:
							print(f"파일 읽기 실패: {e}")
							continue # 혹은 적절한 에러 처리						
						df['new_index'] = 0
						df.set_index('new_index',inplace=True)
						df = df.fillna('')  # 3. excel 의 nill 값을 '' 로 변환

						sudang = {};cnt=1;gongjeStartCnt = 0
						sudang['기본급']=0;sudang['상여']=0;sudang['성과금']=0;sudang['식대']=0;sudang['자가운전보조금']=0;sudang['육아수당']=0;sudang['연구개발수당']=0;sudang['가족수당']=0;sudang['노트북지원비']=0;
						sudang['급여소급']=0;sudang['직책수당']=0;sudang['근속수당']=0;sudang['연월차수당']=0;sudang['자격증수당']=0;sudang['통신비']=0;sudang['추가연장수당']=0;sudang['고정야간수당']=0;
						sudang['연장근로수당']=0;sudang['주말근무수당']=0;sudang['휴일수당']=0;sudang['만근수당']=0;sudang['휴가비']=0;sudang['기타수당1']=0;sudang['기타수당3']=0;sudang['기타수당4']=0;sudang['기타수당5']=0
						sudang['국민연금']=0;sudang['건강보험']=0;sudang['장기요양보험료']=0;
						sudang['고용보험']=0;sudang['학자금상환']=0;sudang['건강보험정산']=0;sudang['장기요양보험정산']=0;sudang['고용보험정산']=0;sudang['중도정산소득세']=0;sudang['중도정산지방소득세']=0;sudang['소득세']=0;
						sudang['지방소득세']=0;sudang['농특세']=0;sudang['연말정산소득세']=0;sudang['연말정산지방소득세']=0;sudang['연말정산농특세']=0;sudang['기타수당1']=0;sudang['기타공제']=0;
						for col in df.columns:
							if col=='국민연금': gongjeStartCnt = cnt  #국민연금 컬럼 까지의 순번
							cnt = cnt + 1
						cnt=1
						for col in df.columns:
							if col=='기본급': sudang['기본급']=cnt
							elif col=='상여': sudang['상여']=cnt
							elif col[:2]=='상여': sudang['상여']=cnt
							elif col[:2]=='성과': sudang['성과금']=cnt
							elif col[:4]== '경영성과': sudang['성과금']+=cnt
							elif col[:2]=='실적': sudang['성과금']+=cnt
							elif col=='식대': sudang['식대']=cnt
							elif col=='식대(비과세)': sudang['식대']+=cnt
							elif col[:4]=='자가운전': sudang['자가운전보조금']=cnt
							elif col[:2]=='차량': sudang['자가운전보조금']=cnt
							elif col[:2]=='챠량': sudang['자가운전보조금']=cnt
							elif col=='육아수당': sudang['육아수당']=cnt
							elif col[:2]=='보육': sudang['육아수당']=cnt
							elif col[:2]=='연구': sudang['연구개발수당']=cnt
							elif col=='가족수당': sudang['가족수당']=cnt
							elif col[:3]=='노트북': sudang['노트북지원비']=cnt
							elif col in '소급': sudang['급여소급']=cnt
							elif col=='직책수당': sudang['직책수당']=cnt
							elif col[:2]=='직급': sudang['직책수당']+=cnt
							elif col=='근속수당': sudang['근속수당']=cnt
							elif col=='연차수당': sudang['연월차수당']=cnt
							elif col[:2]=='월차': sudang['연월차수당']+=cnt
							elif col[:2]=='결근': sudang['연월차수당']+=cnt
							elif col[:3]=='자격증': sudang['자격증수당']=cnt
							elif col[:2]=='통신': sudang['통신비']=cnt
							elif col=='추가연장수당': sudang['추가연장수당']=cnt
							elif col[:5]=='시간외수당': sudang['추가연장수당']+=cnt
							elif col=='고정야간수당': sudang['고정야간수당']=cnt
							elif col[:4]=='야간근로': sudang['고정야간수당']+=cnt
							elif col=='연장근로수당': sudang['연장근로수당']=cnt
							elif col[:4]=='고정연장': sudang['연장근로수당']+=cnt
							elif col[:2]=='특근'        : sudang['연장근로수당']+=cnt
							elif col=='주말근무수당': sudang['주말근무수당']=cnt
							elif col[:2]=='주휴': sudang['주말근무수당']+=cnt
							elif col in '휴일': sudang['휴일수당']=cnt
							elif col[:2]=='휴일': sudang['휴일수당']=cnt
							elif col[:2]=='휴무': sudang['휴일수당']=cnt
							elif col=='만근수당': sudang['만근수당']=cnt
							elif col=='휴가비': sudang['휴가비']=cnt
							elif col=='국민연금': sudang['국민연금']=cnt
							elif col=='건강보험': sudang['건강보험']=cnt
							elif col=='장기요양보험료': sudang['장기요양보험료']=cnt
							elif col=='고용보험': sudang['고용보험']=cnt
							elif col=='학자금상환': sudang['학자금상환']=cnt
							elif col=='건강보험정산': sudang['건강보험정산']=cnt
							elif col=='장기요양보험정산': sudang['장기요양보험정산']=cnt
							elif col=='고용보험정산': sudang['고용보험정산']=cnt
							elif col=='중도정산소득세': sudang['중도정산소득세']=cnt
							elif col=='중도정산지방소득세': sudang['중도정산지방소득세']=cnt
							elif col=='소득세': sudang['소득세']=cnt
							elif col=='지방소득세': sudang['지방소득세']=cnt
							elif col=='농특세': sudang['농특세']=cnt
							elif col=='연말정산소득세': sudang['연말정산소득세']=cnt
							elif col=='연말정산지방소득세': sudang['연말정산지방소득세']=cnt
							elif col=='연말정산농특세': sudang['연말정산농특세']=cnt
							elif col=='기타수당': sudang['기타수당3']=cnt
							elif col=='추가수당': sudang['기타수당4']=cnt
							elif col[:2]=='외근': sudang['기타수당5']=cnt
							elif col[:2]=='금연': sudang['기타수당5']+=cnt
							elif col[:3]=='제수당': sudang['기타수당5']+=cnt
							elif cnt>6 and cnt< gongjeStartCnt: sudang['기타수당1']=cnt #비과세 기타수당
							elif cnt>gongjeStartCnt: sudang['기타공제']=cnt
							cnt = cnt + 1

						str_del = "delete from 급여지급현황 where seq_no="+ str(seqno)  + " and work_yy='" + str(work_yy)  + "'   and work_mm='"+str(work_mm)+"'" 
						cursor.execute(str_del)          
						for row in df.itertuples():
							# if row[1] and row[1]!='' and str(row[1]) in "]":
							if row[1] :
								# row[0] = 0#중요
								empNum = row[1].split("]")[0].replace("[","")
								empName = row[1].split("]")[1]
								strsql = "INSERT INTO 급여지급현황 VALUES ('"+ str(seqno)  + "','" + str(work_yy)  + "','"+str(work_mm)+"','"+empNum+"','"+empName+"','"+row[2]+"',"
								strsql += str(row[3]) + "," + str(row[4]) + "," + str(row[5]) + ","
								strsql += str(row[sudang['기본급']]) + "," + str(row[sudang['상여']]) + "," + str(row[sudang['성과금']]) + "," + str(row[sudang['식대']]) + "," + str(row[sudang['자가운전보조금']]) + ","
								strsql += str(row[sudang['육아수당']]) + "," + str(row[sudang['가족수당']]) + "," + str(row[sudang['노트북지원비']]) + "," + str(row[sudang['급여소급']]) + "," + str(row[sudang['직책수당']]) + ","
								strsql += str(row[sudang['근속수당']]) + "," + str(row[sudang['연월차수당']]) + "," + str(row[sudang['자격증수당']]) + "," + str(row[sudang['통신비']]) + "," + str(row[sudang['추가연장수당']]) + ","
								strsql += str(row[sudang['고정야간수당']]) + "," + str(row[sudang['연장근로수당']]) + "," + str(row[sudang['주말근무수당']]) + "," + str(row[sudang['휴일수당']]) + "," + str(row[sudang['만근수당']]) + ","
								strsql += str(row[sudang['휴가비']]) + "," + str(row[sudang['기타수당1']]) + "," + str(row[sudang['연구개발수당']]) + "," + str(row[sudang['기타수당3']]) + "," + str(row[sudang['기타수당4']]) + "," + str(row[sudang['기타수당5']]) + ","
								strsql += str(row[sudang['국민연금']]) + "," + str(row[sudang['건강보험']]) + "," + str(row[sudang['장기요양보험료']]) + "," + str(row[sudang['고용보험']]) + "," + str(row[sudang['학자금상환']]) + ","
								strsql += str(row[sudang['기타공제']]) + "," + str(row[sudang['건강보험정산']]) + "," + str(row[sudang['장기요양보험정산']]) + "," + str(row[sudang['고용보험정산']]) + "," + str(row[sudang['중도정산소득세']]) + ","
								strsql += str(row[sudang['중도정산지방소득세']]) + "," + str(row[sudang['소득세']]) + "," + str(row[sudang['지방소득세']]) + "," + str(row[sudang['농특세']]) + "," + str(row[sudang['연말정산소득세']]) + ","
								strsql += str(row[sudang['연말정산지방소득세']]) + "," + str(row[sudang['연말정산농특세']])
								strsql +=")"
								print(strsql)
								cursor.execute(strsql)
						# 엑셀닫고 동일메뉴 시작시점으로 전환  
						
						# 엑셀 창 닫기 로직
						del df
						try:
								procs = pywinauto.findwindows.find_elements()
								handle = ''
								for proc in procs:
										if proc.name[:6] == '급여지급현황': handle = proc.handle; break
								
								if handle:
										app = Application().connect(handle=handle)
										w_open = app.window(handle=handle)
										w_open.set_focus()
										pyautogui.hotkey('alt', 'f4')
										time.sleep(1)
										pyautogui.press('esc')
						except Exception as e:
								print(f"창 닫기 중 오류 (무시 가능): {e}")

						# [핵심 수정 3] 파일 삭제 재시도(Retry) 로직 구현
						# 윈도우가 파일 잠금을 해제할 때까지 잠시 대기하며 반복 시도
						max_retries = 10
						for i in range(max_retries):
								try:
										if os.path.exists(file_name):
												os.remove(file_name)
												print(f"파일 삭제 성공: {file_name}")
										break # 삭제 성공 시 루프 탈출
								except PermissionError:
										print(f"파일 삭제 대기 중... ({i+1}/{max_retries})")
										time.sleep(1) # 1초 대기 후 재시도
								except Exception as e:
										print(f"파일 삭제 중 알 수 없는 오류: {e}")
										break
				else:
					print('해당월에 데이터가 없는 경우 다음월로 넘어감')
					continue
		pyautogui.press('esc') 
		return 1

	#지방세납부서 작성
	def semusarang_Issue_Wonchun_wetax(text_mm,flagYear,isBanki,member):
		
		confidence = 0.7 # 검색할 이미지 파일 경로와 유사도(0~1)를 지정합니다.
		pyautogui.hotkey('ctrl', 'enter');time.sleep(0.5) #메뉴검색
		pyperclip.copy('지방소득세납부서(명세서)');  pyautogui.hotkey('ctrl', 'v');time.sleep(0.5)
		pyautogui.press('enter');time.sleep(0.5) ;pyautogui.press('enter');time.sleep(1.5)    
		pyautogui.hotkey('ctrl', '2');time.sleep(0.25)
		time.sleep(2)
		if isBanki=="N":
			if "귀속지급차이" not in member[6]:
				for i in range(4):
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)
					if i<3:pyautogui.press('enter');time.sleep(0.35)
					elif i==3:time.sleep(2)
			else:
				for i in range(2):
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)		
					pyautogui.press('enter');time.sleep(0.35);print('귀속년')
				pay_mm = int(text_mm)+1
				if pay_mm==13:pay_mm = 1
				if pay_mm<10 : 	text_mm = "0" + str(pay_mm)
				else:						text_mm = str(pay_mm)									
				for i in range(2):
					pyautogui.write(text_mm);time.sleep(0.35);print('지급월:'+text_mm)
					if text_mm == "01":					pyautogui.write(str(int(flagYear)+1));time.sleep(0.35);print('지급년')
					else:												pyautogui.press('enter');time.sleep(0.35);print('지급년')
					
		else:
			for i in range(4):
				if i in (0,2):	
					pyautogui.write(f'0{str(int(text_mm)-5)}');time.sleep(0.1)
				else:
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)
				if i<3:pyautogui.press('enter');time.sleep(0.35)
				elif i==3:time.sleep(2)			
			
		image_path = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_SaveDataCall_Insa.png'
		location = pyautogui.locateOnScreen(image_path, confidence=confidence)# 기존에 저장된 데이터를 불러오겠습니까?
		if location:      pyautogui.press('N');time.sleep(0.5);  
		pyautogui.press('f8');time.sleep(0.1);print('마감하시겠습니까')
		image_path = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_MagamCancelYN_Insa.png'
		location = pyautogui.locateOnScreen(image_path, confidence=confidence)# 마감을 취소하시겠습니까
		if location:      pyautogui.press('N');time.sleep(0.5);      
		else: pyautogui.press('f8');time.sleep(0.5);print('마감 ')
		pyautogui.press('esc',presses=2,interval=0.25) 
		return 1

	# 급여대장 작성
	def semusarang_MakePayDaejang(text_mm,member,fileName_Month,directory):
		utils.semusarang_Menu_Popup_App('급여자료입력');time.sleep(1)
		payDay = member[5]
		isDifferent = member[6]
		if "귀속지급차이" not in isDifferent : isDifferent=""
		if payDay=="" : payDay="25"
		if int(text_mm)==2 and int(payDay)>28:payDay = '28'
		if payDay=='31' and (text_mm=='02' or text_mm=='04' or text_mm=='06' or text_mm=='09' or text_mm=='11'):  payDay = '30'

		if int(text_mm)==1: 
			confirm = pyautogui.confirm('[2024년 보험료율]\n건강보험료 : 3.545%\n장기요양보험료 : 12.95%\n고용보험료 : 0.9%\n (재계산기능사용)보험료율에 따라 임금명세서 작성문구 수정후 확인버튼 누르세요  ')
			if confirm=='OK': 
				utils.SET_FOCUS('급여자료입력');time.sleep(0.7)
				pyautogui.write(text_mm);time.sleep(0.7);print('귀속월:'+text_mm)
				pyautogui.press('enter');time.sleep(0.5);print('구분:급여')
				if "귀속지급차이" not in isDifferent :
					pyautogui.press('enter');time.sleep(0.5);print('지급연도')
					pyautogui.press('enter');time.sleep(0.8);print('지급월');print('지급일 : '+payDay)
				else:
					pay_mm = int(text_mm)+1
					if pay_mm==13:pay_mm = 1
					if pay_mm<10 : 	text_mm = "0" + str(pay_mm)
					else:						text_mm = str(pay_mm)
					pyautogui.press('enter');time.sleep(0.5);print('지급연도')
					pyautogui.write(text_mm);time.sleep(0.7);print('지급월:'+text_mm)
					pyautogui.press('enter');time.sleep(0.8);print('지급월');print('지급일 : '+payDay)
				pyautogui.write(payDay);time.sleep(0.35);pyautogui.press('enter');time.sleep(0.35);print('전월복사여부')
				pyautogui.press('f8');time.sleep(1);print('마감')
				isMagam = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Magam_PayDaejang.png'
				location = pyautogui.locateOnScreen(isMagam, confidence=0.7)# 마감하시겠습니까    
				if location:      
					pyautogui.press('Y');time.sleep(0.25);print('마감 - 예')     
				else:
					isMagamCancel = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_MagamCancel_PayDaejang.png'
					location = pyautogui.locateOnScreen(isMagamCancel, confidence=0.7)# 마감을 취소하시겠습니까
					if location:      pyautogui.press('N');time.sleep(0.25);  
		else:
			pyautogui.write(text_mm);time.sleep(0.7);print('귀속월:'+text_mm)
			pyautogui.press('enter');time.sleep(0.5);print('구분:급여')
			if "귀속지급차이" not in isDifferent :
				pyautogui.press('enter');time.sleep(0.5);print('지급연도')
				pyautogui.press('enter');time.sleep(0.8);print('지급월');print('지급일 : '+payDay)
			else:
				pay_mm = int(text_mm)+1
				if pay_mm==13:pay_mm = 1
				if pay_mm<10 : 	text_mm = "0" + str(pay_mm)
				else:						text_mm = str(pay_mm)			
				pyautogui.press('enter');time.sleep(0.5);print('지급연도')
				pyautogui.write(text_mm);time.sleep(0.7);print('지급월:'+text_mm)
				pyautogui.press('enter');time.sleep(0.8);print('지급월');print('지급일 : '+payDay)				
			pyautogui.write(payDay);time.sleep(0.5);pyautogui.press('enter');time.sleep(0.35);print('전월복사여부')
			pyautogui.press('f8');time.sleep(1);print('마감')
			isMagam = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_Magam_PayDaejang.png'
			location = pyautogui.locateOnScreen(isMagam, confidence=0.7)# 마감하시겠습니까    
			if location:      
				pyautogui.press('Y');time.sleep(0.25);print('마감 - 예')     
			else:
				isMagamCancel = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_MagamCancel_PayDaejang.png'
				location = pyautogui.locateOnScreen(isMagamCancel, confidence=0.7)# 마감을 취소하시겠습니까
				if location:      pyautogui.press('N');time.sleep(0.25);      

		title = "[급여자료입력] 인쇄"
		select1 = "급여대장"
		select2 = "임금명세서(계산방법)"
		utils.semusarang_Print_Sheet(title,select1,fileName_Month,directory)
		utils.semusarang_Print_Sheet(title,select2,fileName_Month,directory)
		pyautogui.press('esc',presses=3,interval=0.25)  
		return 1

	#원천징수이행상황신고서 작성
	def semusarang_Issue_Wonchun(text_mm,fileName,directory,isJungKi,flagYear,isBanki,member):
		utils.semusarang_Menu_Popup('원천징수이행상황신고서');time.sleep(1)
		pyautogui.press('left');time.sleep(0.5) ;print('귀속년으로 이동')
		if isBanki=="N":
			if "귀속지급차이" not in  member[6] :
				for i in range(4):
					pyautogui.press('enter');time.sleep(0.35);print('귀속년')
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)
			else:
				for i in range(2):
					pyautogui.press('enter');time.sleep(0.35);print('귀속년')
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)			
				pay_mm = int(text_mm)+1
				if pay_mm==13:pay_mm = 1
				if pay_mm<10 : 	text_mm = "0" + str(pay_mm)
				else:						text_mm = str(pay_mm)									
				for i in range(2):
					if text_mm == "01":					pyautogui.write(str(int(flagYear)+1));time.sleep(0.35);print('지급년')
					else:												pyautogui.press('enter');time.sleep(0.35);print('지급년')
					pyautogui.write(text_mm);time.sleep(0.35);print('지급월:'+text_mm)								
		else:
			for i in range(4):
				pyautogui.press('enter');time.sleep(0.35);print('귀속년')
				if i in (0,2):		
					pyautogui.write(str(int(text_mm)-5));time.sleep(0.35);print(f'귀속월:{int(text_mm)-5}')
					pyautogui.press('enter');time.sleep(0.35);print('귀속년')
				else:							
					pyautogui.write(text_mm);time.sleep(0.35);print('귀속월:'+text_mm)
		if  (datetime.now().month-int(text_mm))>=2 or isJungKi==3: pyautogui.write('3');time.sleep(0.35);print('기한후신고')
		else                                      : pyautogui.write('1');time.sleep(0.35);print('정기신고')
		if int(text_mm)==2:pyautogui.press('enter');time.sleep(0.35);print('연말정산 추가 납부세액 분납 적용? 아니오')
		image_path = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_SaveDataCall_Wonchun.png'
		location = pyautogui.locateOnScreen(image_path, confidence=0.7)# 저장된 데이터를 불러오시겠습니까? 아니오
		if location:      pyautogui.press('N');time.sleep(0.5);      
		pyautogui.press('f8');time.sleep(1);print('마감')
		image_path = 'K:/noa-django/Noa/static/assets/images/autowork/semusarang_MagamCancelYN_Insa.png'
		location = pyautogui.locateOnScreen(image_path, confidence=0.7)# 마감을 취소하시겠습니까
		if location:      pyautogui.press('N');time.sleep(0.5);      
		else: 
			pyautogui.press('enter');time.sleep(1);print('마감 - 예')
		utils.semusarang_Print(fileName,directory)
		pyautogui.press('esc',presses=2,interval=0.25)  
		return 1


	#소득세 접수후 지방세 신고
	def Htx_WetaxIssue(driver,memuser,directory,fileName,savefile,wcIncomeTax):
		driver.find_element(By.ID,'btn_jumin').click();print('주민번호 뒷자리 확인')
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print('이미 지방세신고서를 제출한 경우')
		driver.find_element(By.ID,'rptNm').send_keys('세무법인대승');print('성명/법인명');time.sleep(0.5)
		pyautogui.press('tab');time.sleep(0.5);pyautogui.press('space');time.sleep(0.5)
		driver.find_element(By.ID,'rptRegNo1').send_keys('120171');print('법인번호 앞자리');time.sleep(0.5)
		driver.find_element(By.ID,'rptRegNo2').send_keys('0005046');print('법인번호 뒷자리');time.sleep(0.5)
		driver.find_element(By.XPATH,'/html/body/div[3]/div/div/div[2]/form/div[3]/div[2]/div/div/table/tbody/tr[1]/td[2]/a').click();print('실명인증')
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1) ;print(' 법인명과 법인등록번호가 일치합니다!') 
		driver.find_element(By.ID,'rptTel').send_keys('010-9349-7120');print('세무대리인연락처');time.sleep(0.5)
		if memuser.hp_no!='--':        driver.find_element(By.ID,'moTel').send_keys(memuser.hp_no);print('상대방연락처');time.sleep(0.5)
		else:                        driver.find_element(By.ID,'moTel').send_keys('01011111111');print('상대방연락처');time.sleep(0.5)
		if wcIncomeTax<0:
			bankRfnd = memuser.etc.split(' ')[0]
			if bankRfnd!='농축협' and bankRfnd!='새마을금고':  bankRfnd = bankRfnd.replace('은행','')+"은행";
			select = Select(driver.find_element(By.ID,'bankRfnd'));select.select_by_visible_text(bankRfnd);time.sleep(0.5)
			acctRfnd = memuser.etc.split(' ')[1];driver.find_element(By.ID,'acctRfnd').send_keys(acctRfnd);time.sleep(0.5)
		driver.find_element(By.XPATH,'/html/body/div[3]/div/div/div[2]/form/div[11]/div[2]/div/div/div/div[2]/label/span').click()
		driver.find_element(By.XPATH,'/html/body/div[3]/div/div/div[2]/form/div[12]/ul/li[2]/div/a[3]').click();print('신고 버튼');time.sleep(0.5)
		WebDriverWait(driver, 5).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1.5) ;print('위택스를 이용해 개인지방소득세를 신고한자는 세액이 확정됩니다.') 
		confirmProcess = 'OK'
		try:
			driver.implicitly_wait(10);driver.find_element(By.XPATH,'//*[@id="section"]/div[10]/ul/li[1]/a[2]').click();print('접수증팝업')
		except:
			confirmProcess = pyautogui.confirm('지방세신고 수정사항을 교정하고 신고버튼을 누른 후 에러팝업까지 제거하고 확인을 누르세요.[취소]프로그램 중단')
			driver.implicitly_wait(10);driver.find_element(By.XPATH,'//*[@id="section"]/div[10]/ul/li[1]/a[2]').click();print('접수증팝업')
		if confirmProcess=='OK':
			time.sleep(2)
			main = driver.window_handles;    print(main);    driver.switch_to.window(main[2]) ;time.sleep(3)
			savefile_199 =savefile+ "199.pdf";fullFileName = savefile_199;fileName_199= fileName+"199.pdf";print(fullFileName)
			if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
			pyautogui.press('tab',presses=2,interval=0.7);time.sleep(1);pyautogui.press('enter');time.sleep(1)
			utils.FileSave_Downloaded_PDF(directory,'',fileName_199,memuser.seq_no);print(memuser.biz_name + '지방세 접수증 저장완료')
			pyautogui.hotkey('alt','f4')
			if wcIncomeTax>0:
				print('납부서조회')
				main = driver.window_handles;    print(main);    driver.switch_to.window(main[1]); 
				driver.implicitly_wait(20);driver.find_element(By.XPATH,'//*[@id="section"]/div[10]/ul/li[1]/a[3]').click();print('납부서팝업')
				driver.implicitly_wait(20);time.sleep(5)
				main = driver.window_handles;    print(main);    driver.switch_to.window(main[2]); 
				savefile_201 =savefile+ "201.pdf";fullFileName = savefile_201;fileName_201= fileName+"201.pdf";print(fullFileName)
				if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
				pyautogui.press('tab',presses=2,interval=0.5);time.sleep(1);driver.implicitly_wait(10);pyautogui.press('enter');time.sleep(1)
				utils.FileSave_Downloaded_PDF(directory,'',fileName_201,memuser.seq_no);print(memuser.biz_name + '지방세 납부서 저장완료')
				pyautogui.hotkey('alt','f4')          
			else:
				main = driver.window_handles;    print(main);    driver.switch_to.window(main[0]);   

class ECOUNT:
	#세무사랑 스크래핑 
	def semusarang_Scrapping(workyear,startMM,endMM):
		utils.semusarang_Menu_Popup('스크래핑내역조회')
		pyautogui.press('f3');time.sleep(0.5);pyautogui.press('enter');time.sleep(0.5)
		pyautogui.press('left');time.sleep(0.5);pyautogui.write(workyear);time.sleep(0.5);pyautogui.write(startMM);time.sleep(0.5);pyautogui.write(endMM);time.sleep(0.5);
		checkbox1 = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_scrap_TI.png', confidence=0.7)
		if checkbox1:	
			pyautogui.click(checkbox1);time.sleep(0.5)
			pyautogui.press('tab')
		# checkbox2 = pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/semusarang_scrap_TI.png', confidence=0.7)
		# if checkbox2:	pyautogui.click(checkbox2)
		# if checkbox1 and checkbox2: pyautogui.press('tab')
		return True
	#거래처코드 업로드
	def TraderUpload(seqno):
		utils.semusarang_MenuCode_Popup('1009','거래처등록')
		pyautogui.hotkey('ctrl','e');time.sleep(1);pyautogui.press('enter');time.sleep(2);
		pyautogui.hotkey('alt','f4')
		utils.DBSave_Downloaded_xlsx('일반',seqno,'거래처등록')	;time.sleep(2)
		utils.SET_FOCUS('거래처등록')	
		pyautogui.hotkey('ctrl','2');time.sleep(1)
		pyautogui.hotkey('ctrl','e');time.sleep(1);pyautogui.press('enter');time.sleep(5);		
		pyautogui.hotkey('alt','f4')
		utils.DBSave_Downloaded_xlsx('금융기관',seqno,'거래처등록')	;time.sleep(2)		
		utils.SET_FOCUS('거래처등록')	
		pyautogui.hotkey('ctrl','3');time.sleep(1)
		pyautogui.hotkey('ctrl','e');time.sleep(1);pyautogui.press('enter');time.sleep(5);
		utils.semusarang_Excelclose_Openmenuclose()
		utils.DBSave_Downloaded_xlsx('신용카드',seqno,'거래처등록')			
		return True
	def MakeResultExcel(seq_no,biz_no,biz_name,workyear,vatKikan,work_qt):
		driver = f"d:\\{biz_name}\\{workyear}\\부가세자료\\{vatKikan}\\"
		manageNo = [seq_no,biz_no,workyear,work_qt]
		utils.MakeExcel_FromDB(driver,manageNo,'엑셀자료 일반전표전송');print(f"{biz_name}:엑셀자료 일반전표전송 파일 작성완료 - {driver}")
		#utils.MakeExcel_FromDB(driver,manageNo,'신용카드 매입 자료 입력')
		return True
	#분개장 업로드 및 자료생성(세무사랑 작업용)
	def TransactionExcelUpDnload(seq_no,biz_name,workyear,vatKikan,work_qt):
		manageNo = [seq_no,workyear,work_qt]
		directory = f"d:\\{biz_name}\\{workyear}\\부가세자료\\{vatKikan}"
		targetFiles = utils.find_target_files(directory,'분개장')
		if targetFiles:
				file_names = [file[1] for file in targetFiles]
				selected_file_name = pyautogui.confirm("업로드할 파일을 선택하세요.",buttons=file_names)		
				if selected_file_name:
						selected_file_index = file_names.index(selected_file_name)
						selected_file = targetFiles[selected_file_index]
						root, file_name = selected_file
						utils.DBSave_Downloaded_xlsx(os.path.join(root, file_name),manageNo,'이카운트분개장업로드')	
				else:
						print("No file selected.")
		else:
			print(f'{directory} 내에 [분개장]을 포함한 파일이 없습니다.')
		return True
	#세무사랑 전표처리
	def Semusarang_TransactionExcelUpload():
		return True

class EDI:
	#사무대행 위탁업체 저장
	def Total_SamuDaehang_Save(driver):
		driver.find_element(By.ID,'mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_1_btn_menu2_Label').click();driver.implicitly_wait(5);print('정보조회 - 상단탭')
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_2_title').click();		driver.implicitly_wait(5);print('사무대행업무조회');time.sleep(1)
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_2_gen_SecondGenerator_side_0_subtitle').click();print('사무수임사업장 내역조회');time.sleep(1)
		button = WebDriverWait(driver, 10).until(
			EC.element_to_be_clickable((By.ID, "mf_wfm_content_bt_johoe"))
		)
		button.click()
		# JavaScript로 포커스 이동
		driver.execute_script("arguments[0].focus();", button);time.sleep(10);print('조회완료')
		pyautogui.press('tab');time.sleep(0.5);pyautogui.press('enter');time.sleep(5);print('엑셀저장')
		downloads = 'C:\\Users\\Administrator\\Downloads'
		file_name = max([downloads + "\\" + f for f in os.listdir(downloads)],key=os.path.getctime)
		extension = os.path.splitext(file_name)[1].lower()  # Get the extension and convert it to lower case
		if extension in ['.xls', '.xlsx']:		
			utils.DBSave_Downloaded_xlsx(driver,'manageNo','사무수임사업장') 
		else:
			print("엑셀파일 없음")		
		return True
	#보수총액신고대상자 엑셀작성 후 토탈에 업로드
	def Total_Bosu_Singo_excelWrite_upload(driver,workyear,path):
		strsql = "select distinct aa.seq_no,aa.Biz_Name,aa.biz_no,aa.biz_zipcode "
		strsql += "from ( select a.biz_name, a.seq_no,a.biz_no,a.biz_zipcode from mem_user a,  보수총액신고_고용 b "
		strsql += "     where a.seq_no=b.seq_no  and work_yy='"+str(workyear)+"' and not (산재연간보수총액=0 and 고용연간보수총액_상반기=0 and 고용연간보수총액_하반기=0)  )  aa "
		strsql += " where aa.seq_no <> ''"
		strsql += " and not exists ( select a.seq_no from mem_user a,  보수총액신고_고용 b where a.seq_no=b.seq_no  and work_yy='"+str(workyear)+"' and  (산재연간보수총액=0 and 고용연간보수총액_상반기=0 and 고용연간보수총액_하반기=0)  and aa.seq_no = a.seq_no)"
		strsql += " and not exists (select a.seq_no from mem_user a, tbl_younmal b where a.Seq_No=b.seq_no and yn_10=1 and work_yy='"+str(workyear)+"'  and aa.seq_no = a.seq_no) "
		strsql += " group by  aa.seq_no,aa.Biz_Name,aa.biz_no,aa.biz_zipcode order by aa.Biz_Name"
		cursor = connection.cursor()
		cursor.execute(strsql)
		result = cursor.fetchall()
		connection.commit()
		workyear = datetime.now().year


		# 관리번호 입력 - 번호넣고 5초대기  
		cnt=1
		for member in result:
			# if cnt==1:
					totalPath = path+"\\"+member[1]+"\\"+str(workyear)+"\\사대보험\\";utils.createDirectory(totalPath) 
					firstFile = "고용산재보수총액신고대상자(OK).xlsx"
					secondFile = "고용산재보수총액신고대상자(최종).xlsx"
					# if os.path.isfile(totalPath+firstFile):
					strsql2 = "select trim(성명),trim(주민번호),부과부호구분,건설업근무이력자,산재취득일,산재상실일,"
					strsql2 += "    CASE         WHEN 산재연간보수총액 = 0 THEN ''         ELSE TRIM(산재연간보수총액)     END AS 산재연간보수총액,"
					strsql2 += f"'{member[3]}',고용취득일,고용상실일,"
					strsql2 += "    CASE         WHEN 고용연간보수총액_상반기 = 0 THEN ''         ELSE TRIM(고용연간보수총액_상반기)     END AS 고용연간보수총액_상반기,"
					strsql2 += "trim(고용연간보수총액_하반기) "
					strsql2 += " from 보수총액신고_고용 where seq_no="+str(member[0])+" and work_yy="+str(workyear-1)
					print(strsql2)
					cursor.execute(strsql2)
					result2 = cursor.fetchall()
					connection.commit()
					df = DataFrame(result2)
					df.columns = ["성명","주민번호","부과부호구분","건설업근무이력자","산재취득일","산재상실일","산재연간보수총액","근무지코드","고용취득일","고용상실일","고용연간보수총액_상반기","고용연간보수총액_하반기"]
					excel_writer = pd.ExcelWriter(totalPath+secondFile)
					df.to_excel(excel_writer,index=False)
					excel_writer.close()
					print(totalPath+secondFile+" 파일저장성공")

					print("진입:"+member[2])
					driver.find_element(By.ID,'mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_0_btn_menu2_Label').click();driver.implicitly_wait(5);print('민원접수/신고 - 상단탭')
					driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_4_title').click();		driver.implicitly_wait(5)   ;print('보수신고') ;time.sleep(1)
					driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_4_gen_SecondGenerator_side_0_subtitle').click();print('보수신고2')
					driver.implicitly_wait(5)  					
					driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_maeGwanriNo"]').clear()
					time.sleep(1)
					driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_maeGwanriNo"]').send_keys(member[2]+"-0")    
					time.sleep(2)
					try:
						WebDriverWait(driver, 1.5).until(EC.alert_is_present())
						print('알럿 발생')
						al = Alert(driver)
						prtTxt = "임시 저장된 내용이 존재합니다."
						al.accept()
						print("alert 해제: "+member[1] + " - "+prtTxt) 
					except TimeoutException:   
						attr = driver.switch_to.active_element.get_attribute("value")# 알럿 ID가 매번 바뀐다 ㅎㅎㅎ
						print(attr)
						if attr=="확인": 
							prtTxt = "보수총액신고서는 해당년도 1회 제출 가능합니다. 보수총액수정신고 화면으로 이동합니다."
							print(prtTxt)
							driver.find_element(By.ID,driver.switch_to.active_element.get_attribute("id")).click()
						else:    
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_saveStep0_excelup.png')
							# pyautogui.click(center)
							# print("엑셀업로드 버튼")     
							# time.sleep(1)      
							pyautogui.press('tab',presses=11,interval=0.25)  
							pyautogui.press('enter')             
							# excelUp = driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_wq_uuid_1812"]')
							# driver.execute_script('arguments[0].scrollIntoView(true);', excelUp)
							# time.sleep(1)
							# excelUp.click()  #엑셀업로드
							print('엑셀업로드')
							# attr = driver.switch_to.active_element#.get_attribute("id")
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_selectFile.png')
							# pyautogui.click(center)
							pyautogui.press('tab');time.sleep(0.25)
							pyautogui.press('enter');time.sleep(0.5)           
							print("엑셀업로드대기")
							time.sleep(0.5)      
							pyautogui.hotkey('alt','d');print('alt + d')
							time.sleep(0.5)
							pyperclip.copy(totalPath)
							pyautogui.hotkey('ctrl', 'v')
							pyautogui.press('enter')
							time.sleep(0.5)            
							pyautogui.hotkey('alt','N');print('alt + N')
							pyperclip.copy(secondFile);print("파일명:"+secondFile)
							pyautogui.hotkey('ctrl', 'v')
							time.sleep(0.5)
							pyautogui.hotkey('alt','o')
							time.sleep(0.5)
							pyautogui.press('tab');time.sleep(0.25)
							pyautogui.press('enter');time.sleep(3)             
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_uploadFile.png')
							# pyautogui.click(center);print('업로드클릭')
							# time.sleep(1)
							element = driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_chkAgreeGubun"]/span[1]')
							driver.execute_script('arguments[0].scrollIntoView(true);', element)
							element.click();print('충당 동의')
							time.sleep(0.5)
							driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnImsiSave"]').click()
							time.sleep(2)
							pyautogui.press('shift');time.sleep(0.25)
							pyautogui.press('enter');time.sleep(2) ;print('임시저장')
							pyautogui.press('shift');time.sleep(2)
							pyautogui.press('enter',presses=2,interval=3);time.sleep(1);print('임시저장 되었습니다')             
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_saveStep1_confirm.png')
							# pyautogui.click(center);print('임시저장')
							# time.sleep(2)
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_saveStep2_confirm.png')
							# pyautogui.click(center);print('임시저장 되었습니다')
							# time.sleep(2)            
							driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnVerify"]').click()
							time.sleep(10)
							WebDriverWait(driver, 1).until(EC.alert_is_present())
							print('알럿 발생')
							al = Alert(driver)
							al.accept()
							time.sleep(2)
							driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnSave"]').click();print('접수')
							time.sleep(2)
							# center = pyautogui.locateCenterOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_saveStep1_confirm.png')
							# pyautogui.click(center);print('접수 되었습니다')
							pyautogui.press('shift');time.sleep(1)
							pyautogui.press('enter');time.sleep(2) ;print('접수 되었습니다')            
							# time.sleep(4)      
							strsql = "Merge tbl_younmal as A Using (select '"+str(workyear-1)+"' as work_yy,'"+member[0]+"' as seq_no) as B "
							strsql += "On A.work_yy=B.work_yy  and A.seq_no=B.seq_no "
							strsql += "when matched then update set YN_10='1' "
							strsql += "When Not Matched Then insert  values('" + member[0] + "','" + str(workyear-1) + "','0','0','0','0','0','0','0','','0','1');"  
							print(strsql)
							cursor = connection.cursor()
							cursor.execute(strsql)
							cursor.commit()  
							time.sleep(1);print('서식인쇄1')
							driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnDocPrint"]').click() 
							time.sleep(1);print('서식인쇄2')
							iframe = driver.find_element(By.CSS_SELECTOR,'#mf_wfm_content_WZ0202_wframe_ifr_Report')
							driver.switch_to.frame(iframe)
							time.sleep(1)
							driver.find_element(By.XPATH,'/html/body/div/div/div[1]/table/tbody/tr/td/div/nobr/button[5]').click()
							# time.sleep(2)
							# driver.find_element(By.XPATH,'/html/body/div[7]/div[1]/div[2]/a').click()
							# # driver.find_element(By.ID,'mf_wfm_content_WZ0202_close').click()    
							# time.sleep(1);print('출력닫기1')         
							# driver.find_elemenemt(By.XPATH,'/html/body/div[7]/div[1]/div[3]/a').click()
							directory = 'd:/'
							utils.FileSave_Downloaded_PDF(totalPath,'','보수총액신고접수증.pdf',member[0])
							driver.switch_to.default_content()
							pyautogui.press('f5');time.sleep(2)
			# cnt += 1
		connection.close()    
		driver.quit()
		return 1

	# 세무사랑 보수총액신고자 엑셀저장하면서 토탈세액수정
	def Total_Bosu_Singo_SS_excelupdate(driver,workyear,semusarangID):
		strsql = f"select replace(biz_no,'-',''),a.seq_no,duzon_id,biz_name from mem_user a,(select seq_no from 보수총액신고_고용 where work_yy='{workyear}' group by seq_no ) b where a.seq_no=b.seq_no "
		strsql += f" and a.seq_no not in (select seqno_lastTry from 스크래핑관리 where crt_dt='{workyear}' and bigo='보수총액신고대상자업데이트') "  		
		strsql += "order by a.biz_no"
		cursor = connection.cursor()
		cursor.execute(strsql)
		result = cursor.fetchall()
		connection.commit()
		if result:    
			dig =  utils.semusarang_LaunchProgram_App(semusarangID)
			for member in result:
				if member[2]=='1':  utils.semusarang_ChangeCompany(member[0])
				else:               utils.semusarang_ChangeCompany_ID_App(dig,member[2])   
				utils.semusarang_ChangeFiscalYear('insa',str(workyear))
				pyautogui.hotkey('ctrl', 'enter') #메뉴검색
				time.sleep(0.5) 
				pyperclip.copy('산재보험보수총액신고서')   
				pyautogui.hotkey('ctrl', 'v')
				time.sleep(1)  
				pyautogui.press('enter',presses=2, interval=0.5); time.sleep(2);print('메뉴진입')
				pyautogui.press('enter',presses=2, interval=0.5) 
				time.sleep(2)#필수 
				print('안내문 확인 알람 대기중')
				if pyautogui.locateOnScreen('K:/noa-django/Noa/static/assets/images/autowork/total_Annaejangshow.png', confidence=0.7):
					pyautogui.press('N') ;print('안내장보기 아니오')
				pyautogui.press('enter',presses=2, interval=1)
				pyautogui.press('f11');print('불러오기')
				pyautogui.press('tab') ;time.sleep(5)
				pyautogui.press('tab')
				pyautogui.hotkey('ctrl','e')
				time.sleep(1.5)
				pyautogui.press('enter')
				time.sleep(3)
				utils.semusarang_Excelclose_Openmenuclose()
				isOK = utils.DBSave_Downloaded_xlsx(driver,member[1],'보수총액신고대상자업데이트')			
				if isOK:
					strsql = f"merge 스크래핑관리  as A using(select '{member[1].strip()}' as seqno_lastTry,'{workyear}' as crt_dt, '보수총액신고대상자업데이트' as bigo) as B  "   
					strsql += " on A.seqno_lastTry=B.seqno_lastTry  and A.crt_dt=B.crt_dt and A.bigo=B.bigo "
					strsql += f" when matched then update set seqno_lastTry='{member[1].strip()}'"   
					strsql += f" when not matched then insert values('{workyear}','{member[1].strip()}','{member[3].strip()}','보수총액신고대상자업데이트');" 
					print(strsql)
					cursor.execute(strsql) 
			return 1

	# 보수총액신고 사전작업 - 대상자 엑셀 내려받기
	def Total_Bosu_Singo_Prework(driver,workyear):
		#민원접수/신고 - 상단탭     mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_0_btn_menu2_Label
		driver.find_element(By.ID,'mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_0_btn_menu2_Label').click()
		driver.implicitly_wait(5)
		#보수신고
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_4_title').click()
		driver.implicitly_wait(5)  
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_4_gen_SecondGenerator_side_0_subtitle').click()
		driver.implicitly_wait(5)  
		strsql = "select c.관리번호, trim(a.biz_name), a.seq_no from edi_comwel c , mem_user a, mem_deal b "
		strsql += " where a.seq_no=b.seq_no and left(c.관리번호,12) = isnull(a.biz_no, '') and   isnull(a.biz_no, '') <> '' and b.keeping_yn='Y' and b.kijang_YN='y' "
		strsql += " and c.구분='고용' and c.상태='정상' and c.소멸일자='' and c.사업구분='계속' and 부과고지여부='Y'     "
		strsql += f" and a.seq_no not in (select seqno_lastTry from 스크래핑관리 where crt_dt='{workyear}' and bigo='보수총액신고대상자 엑셀내려받기') "  
		strsql += " order by c.관리번호 "  
		cursor = connection.cursor()
		cursor.execute(strsql)
		result = cursor.fetchall()
		for manageNo in result:  
			# 관리번호 입력 - 번호넣고 5초대기
			print("진입:"+manageNo[0])
			driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_maeGwanriNo"]').clear()
			time.sleep(0.2)
			driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_maeGwanriNo"]').send_keys(manageNo[0])    
			try:
				WebDriverWait(driver, 1).until(EC.alert_is_present())
				al = Alert(driver)
				al.accept()
				print("alert 해제")
			except TimeoutException:    
				# 로딩 요소가 사라질 때까지 기다림
				WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "___processbar2"))				)
				driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnDownIlban"]').click()  #입력정보엑셀저장
				print('입력정보엑셀저장')
				try:
					WebDriverWait(driver, 2).until(EC.alert_is_present());	al = Alert(driver);	al.accept()
					print("alert 해제")
				except TimeoutException:
					time.sleep(3)  
					isOK = utils.DBSave_Downloaded_xlsx(driver,manageNo,'보수총액신고대상자') 
				strsql = f"merge 스크래핑관리  as A using(select '{manageNo[2].strip()}' as seqno_lastTry,'{workyear}' as crt_dt, '보수총액신고대상자 엑셀내려받기' as bigo) as B  "   
				strsql += " on A.seqno_lastTry=B.seqno_lastTry  and A.crt_dt=B.crt_dt and A.bigo=B.bigo "
				strsql += f" when matched then update set seqno_lastTry='{manageNo[2].strip()}'"   
				strsql += f" when not matched then insert values('{workyear}','{manageNo[2].strip()}','{manageNo[1].strip()}','보수총액신고대상자 엑셀내려받기');" 
				print(strsql)
				cursor.execute(strsql) 
		return driver


	# 근로자고용정보현황조회(20103)
	def Total_Employ_Searchlist(driver,workyear):
		#정보조회 - 상단탭          
		driver.find_element(By.ID,'mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_1_btn_menu2_Label').click();		driver.implicitly_wait(5)
		#근로자 보험가입정보조회 (메인화면 바닥링크)
		driver.find_element(By.ID,'mf_wfm_content_gen_firstGenerator_0_gen_SecondGenerator_4_subtitle').click();		driver.implicitly_wait(5)

		strsql = "select c.관리번호, c.사업장명, a.seq_no from edi_comwel c , mem_user a, mem_deal b "
		strsql += " where a.seq_no=b.seq_no and left(c.관리번호,12) = isnull(a.biz_no, '') and   isnull(a.biz_no, '') <> '' and b.keeping_yn='Y' and b.kijang_YN='y' "
		strsql += " and c.구분='고용' and c.상태='정상' and c.소멸일자='' and c.사업구분='계속' "
		strsql += f" and a.seq_no not in (select seqno_lastTry from 스크래핑관리 where crt_dt='{workyear}' and bigo='근로자고용정보현황조회') "  
		strsql += " order by a.seq_no/1 ";print(strsql)
		cursor = connection.cursor()
		cursor.execute(strsql)
		result = cursor.fetchall()
		connection.commit()
		for manageNo in result:
			# 관리번호 입력 - 번호넣고 5초대기
			print("진입:"+manageNo[0])
			driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_edtGwanriNo"]').send_keys(manageNo[0]);time.sleep(7)#번호넣고 기다리면 데이터는 조회됨
			try:
				WebDriverWait(driver, 2).until(EC.alert_is_present());	al = Alert(driver);al.accept();print(f"{manageNo[1]}:조회대상 없음 - alert 해제")
				driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_edtGwanriNo"]').clear()
				time.sleep(0.5)
			except TimeoutException:
				pyautogui.press('pgdn');time.sleep(0.3)
				driver.find_element(By.ID,'mf_wfm_content_excelDownLoad').click();time.sleep(3);print('엑셀저장')

				# 로딩 요소가 사라질 때까지 기다림
				WebDriverWait(driver, 30).until(EC.invisibility_of_element_located((By.ID, "___processbar2"))				)
				# 요소 클릭 시도
				driver.find_element(By.ID,'mf_wfm_content_excelDownLoad').click();time.sleep(3);print('엑셀저장')		
				#pyautogui.press('tab',presses=39,interval=0.1);pyautogui.press('enter');time.sleep(3);print('엑셀저장')#ID로 엑셀저장버튼에 접근 안됨
				isOK = utils.DBSave_Downloaded_xlsx(driver,manageNo,'근로자고용정보현황조회') 
				if isOK:
					strsql = f"merge 스크래핑관리  as A using(select '{manageNo[2].strip()}' as seqno_lastTry,'{workyear}' as crt_dt, '근로자고용정보현황조회' as bigo) as B  "   
					strsql += " on A.seqno_lastTry=B.seqno_lastTry  and A.crt_dt=B.crt_dt and A.bigo=B.bigo "
					strsql += f" when matched then update set seqno_lastTry='{manageNo[2].strip()}'"   
					strsql += f" when not matched then insert values('{workyear}','{manageNo[2].strip()}','{manageNo[1].strip()}','근로자고용정보현황조회');" 
					print(strsql)
					cursor.execute(strsql) 				
		return driver


	#일용직 근로내용확인서(10506)
	def Total_IlyoungIssue(bizNo,bizName,workyear,text_mm):
		memuser = MemUser.objects.get(biz_no=bizNo[:3]+"-"+bizNo[3:5]+"-"+bizNo[5:10]) 
		driver = utils.conTotalComwelLogin('220-85-33586')
		driver.find_element(By.ID,'mf_wfm_header_gen_firstGenerator_1_gen_SecondGenerator_0_btn_menu2_Label').click();  time.sleep(2);print('민원접수/신고 - 상단탭')  
		#자격관리
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_3_title').click();  driver.implicitly_wait(5);print('자격관리')
		driver.find_element(By.ID,'mf_wfm_side_gen_firstGenerator_side_3_gen_SecondGenerator_side_5_subtitle').click();  time.sleep(3)
		WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mf_wfm_content_chkSingoGubun > span.w2radio_item.w2radio_item_1 > label"))).click()
		WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mf_wfm_content_chkGybSingoYn > span > label"))).click();print('보험구분 - 고용보험 체크')
		if bizNo != '1298648992':#도경개발
			WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#mf_wfm_content_chkSjbSingoYn > span > label"))).click();print('보험구분 - 산재보험 체크')
		
		select = Select(driver.find_element(By.ID,'mf_wfm_content_comYear_input_0'));select.select_by_visible_text(f'{workyear} 년');  driver.implicitly_wait(1)  
		select = Select(driver.find_element(By.ID,'mf_wfm_content_comMM_input_0'));select.select_by_visible_text(f'{text_mm} 월');  driver.implicitly_wait(1)  	
		driver.find_element(By.ID,'mf_wfm_content_maeGwanriNo').clear();	time.sleep(0.1)	
		tmpManageNo = bizNo+"0"
		if bizNo=='1428116111': tmpManageNo = '91001107561'
		driver.find_element(By.ID,'mf_wfm_content_maeGwanriNo').send_keys(tmpManageNo);print('관리번호 : {bizNo}0');time.sleep(3)  
		try:
			print(f'{bizNo} : 수임 안됏거나 임시저장파일이 잇거나')
			WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(1)
			return ''
		except:
			print(f'bizNo : 수임된 사업장 맞음.')
		driver.find_element(By.ID,'mf_wfm_content_maeSaeopjaDrno').clear();	time.sleep(0.3)	
		driver.find_element(By.ID,'mf_wfm_content_maeSaeopjaDrno').send_keys(f"{bizNo}");print('사업자번호 : {bizNo}');time.sleep(1)  
		pyautogui.press('tab') ;time.sleep(0.5)
		WebDriverWait(driver, 3).until(EC.alert_is_present());al = Alert(driver);al.accept();time.sleep(0.5);print('사업자번호를 입력할 경우 국세청으로전송됩니다')
		pyautogui.press('pgdn',presses=3,interval=0.3);time.sleep(0.3)
		driver.find_element(By.ID,'mf_wfm_content_btnExcelIlban').click();print('엑셀 작성파일 불러오기');  driver.implicitly_wait(1)  
		pyautogui.press('tab');time.sleep(0.5);		pyautogui.press('enter');time.sleep(0.5);print('파일선택 아이디로 작동안함!!')
		# 파일열기 - 선택까지
		downloads = 'C:\\NewGen\\Rebirth\\리버스문서보관함\\EDI'
		file_Origin_name = max([downloads + "\\" + f for f in os.listdir(downloads)],key=os.path.getctime) ;print(f'{file_Origin_name}')     
		pyautogui.hotkey('alt','d');print('alt + d');	time.sleep(0.5)
		pyperclip.copy(downloads);	pyautogui.hotkey('ctrl', 'v');	pyautogui.press('enter');	time.sleep(0.5)            
		pyautogui.hotkey('alt','N');print('alt + N');	
		pyperclip.copy(file_Origin_name);print("파일명:"+file_Origin_name);	pyautogui.hotkey('ctrl', 'v');	time.sleep(0.5)
		pyautogui.hotkey('alt','o');	time.sleep(0.5)
		
		driver.find_element(By.ID,'mf_wfm_content_mf_wfm_content_grdMokrokExcel_excelPop_wframe_sendFILE').click();print('파일 업로드 버튼 클릭');  time.sleep(10)
		driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnImsiSave"]').click();print('임시저장 버튼 클릭');  time.sleep(1)
		pyautogui.press('shift');time.sleep(0.25);pyautogui.press('enter');time.sleep(1) ;print('임시저장하시겠습니까')
		pyautogui.press('shift');time.sleep(0.25);pyautogui.press('enter');time.sleep(1) ;print('임시저장 완료되었습니다')
		pyautogui.press('shift');time.sleep(0.25);pyautogui.press('enter');time.sleep(1) ;print('임시저장된 내역이 존재합니다')
		driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnVerify"]').click();print('신고자료검증 버튼 클릭');  time.sleep(5)
		pyautogui.press('shift');time.sleep(0.25);pyautogui.press('enter');time.sleep(1) ;print('신고자료 검증되었습니다')
		driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnSave"]').click();print('접수 버튼 클릭');  time.sleep(1)
		pyautogui.press('shift');time.sleep(0.25);pyautogui.press('enter');time.sleep(3) ;print('접수 하시겠습니까')
		
		driver.find_element(By.XPATH,'//*[@id="mf_wfm_content_btnDocPrint"]').click();print('접수증 인쇄');  time.sleep(2)
		pyautogui.press('tab',presses=6,interval=0.5);pyautogui.press('enter'); time.sleep(2)
		downloadsPDF = f'C:\\Users\\Administrator\\Downloads'
		file_downPDF_name = max([downloadsPDF + "\\" + f for f in os.listdir(downloadsPDF)],key=os.path.getctime) ;print(f'{file_downPDF_name}')   
		fullFileName = f"{downloadsPDF}\\{file_downPDF_name}"  
		directory = f"d:\\{bizName}\\{workyear}\\인건비\\일용직"
		file_Purpose_name = f"{text_mm}월 근로내용확인신고 접수증"
		utils.FileSave_Downloaded_PDF(directory,fullFileName,file_Purpose_name,memuser.seq_no)
		# if  os.path.isfile(fullFileName.replace('/',"\\")):os.remove(fullFileName.replace('/',"\\"));print(fullFileName+" 삭제완료") 
		driver.close()
		jubsuYN = "인건비/일용직 : 접수증 저장"
		return jubsuYN
	
class SMPT:
	
	#출금조회
	def smpt_SearchExcract(driver):
		#회원정보저장
		driver.get('https://www.semuportal.com/cms/manage/payer/payer010.do');time.sleep(2)
		driver.execute_script("javascript:downloadExcel();");time.sleep(5);print('회원정보 다운로드')
		utils.DBSave_Downloaded_xlsx(driver,['3639'],'CMS회원목록')

		#인트라넷에 출금실패정보 업로드
		driver.get('https://www.semuportal.com/cms/payment/pay/pay010.do');time.sleep(2)
		driver.execute_script("javascript:preMonths(-1);");time.sleep(1);print('1개월')
		driver.execute_script("javascript:doSearch();");time.sleep(5);print('검색')
		driver.execute_script("javascript:downloadExcel()");time.sleep(10);print('엑셀다운로드')
		utils.DBSave_Downloaded_xlsx(driver,['3639'],'CMS출금내역업로드')
		return 1

	#4. 엑셀자료 일반전표 전송
	def smpt_SaveExcractResult(file_name):
		# df = pd.read_excel(file_name, engine='openpyxl', header=0)

		df = None
		if file_name.endswith('.xls'):
			df = pd.read_excel(file_name, engine='xlrd', header=0)
		elif file_name.endswith('.xlsx'):
			df = pd.read_excel(file_name, engine='openpyxl', header=0)
		else:
			raise ValueError("지원하지 않는 파일 형식입니다.") 		
		df.replace('', np.nan, inplace=True)
		# 두 번째 열을 숫자로 변환하고, 오류가 발생하면 NaN으로 변환
		# pandas 열은 0부터 시작하는 인덱싱을 사용하기 때문에 df.columns[1]은 두 번째 열을 가리킵니다
		df[df.columns[1]] = pd.to_numeric(df[df.columns[1]], errors='coerce')
		# DataFrame을 두 번째 열 기준으로 정렬
		# 마찬가지로, df.columns[1]을 사용하여 두 번째 열을 기준으로 정렬합니다
		df_sorted = df.sort_values(by=df.columns[1])		
		current_date = None
		sum_for_current_date = 0	
		totXlsArr = []
		for row in df_sorted[:-1].itertuples(index=False):  # 마지막행은 제외한다
			duedate,seq_semu,semuName,promisedate, promisevalue,value_to_sum,gubun,sangtae = row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]
			if '성공' in sangtae:   
				strsql = f"select trim(seq_SEMU),trim(회원명) from CMS_MEMBER where trim(seq_CMS)='{seq_semu.strip()}'"
				cursor = connection.cursor()
				cursor.execute(strsql)#;print(strsql)
				CMS_MEMBER = cursor.fetchone()
				connection.commit()
				semu_code =""; semu_name = semuName
				if 	CMS_MEMBER:
					semu_code = CMS_MEMBER[0];					semu_name = CMS_MEMBER[1]
				if current_date is None:
					current_date = duedate
					sum_for_current_date = value_to_sum
					if semuName[:3]=="임선희":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","00107","임선희(성지하이츠)"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
					elif semuName[:3]=="ANC":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","03836","APM"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 								
					else:
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum];	totXlsArr.append(bankLine) 								
				elif duedate == current_date:
					if semuName[:3]=="임선희":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","00107","임선희(성지하이츠)"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
					elif semuName[:3]=="ANC":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","03836","APM"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 
					else:						
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum];  totXlsArr.append(bankLine) 				
					sum_for_current_date += value_to_sum# 날짜가 안바꼈으면 더해라
				else:
					# 날짜가 바뀐 경우, process the sum for the previous date
					# print(f"Sum for {current_date}: {sum_for_current_date}")
					bankLine = [current_date,"3","108","보통예금","98002","CMS"," ","CMS자동이체",sum_for_current_date]  ;totXlsArr.append(bankLine) 		
					if semuName[:3]=="임선희":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","00107","임선희(성지하이츠)"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 	
					elif semuName[:3]=="ANC":
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
						bankLine = [duedate,"4","108","외상매출금","03836","APM"," ",semu_name,value_to_sum/2];	totXlsArr.append(bankLine) 		
					else:							
						bankLine = [duedate,"4","108","외상매출금",semu_code,semu_name," ",semu_name,value_to_sum];	totXlsArr.append(bankLine) 	
					# 새날로 업데이트
					current_date = duedate
					sum_for_current_date = value_to_sum				
					
		utils.Make98002(totXlsArr)
		return 1
	

