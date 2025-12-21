import requests
import urllib.parse
import http.client
import http.cookiejar
import urllib.request

HTTP_timeout = 3000
HTTP_UserAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36"

_HTTP_ContextType_GET = None
_HTTP_ContextType_POST = "application/x-www-form-urlencoded"
_HTTP_ContextType_XML = "application/xml; charset=UTF-8"
rst = 0
global sbResponseData
sbResponseData = ""
strResData = ""
sbSSOToken = ""
sbuserClCd = ""

class LoginSystemContext:
    def __init__(self):
        self.m_code = None
        self.m_errCode = None
        self.m_errMsg = None
        self.m_lgnRsltCd = None
        self.m_pswdErrNbcnt = None
        self.m_tin = None
        self.m_secCardId = None

    def copyTo(self, ctx):
        ctx.m_code = self.m_code
        ctx.m_errCode = self.m_errCode
        ctx.m_errMsg = self.m_errMsg
        ctx.m_lgnRsltCd = self.m_lgnRsltCd
        ctx.m_pswdErrNbcnt = self.m_pswdErrNbcnt
        ctx.m_secCardId = self.m_secCardId
        ctx.m_tin = self.m_tin

    def copyFrom(self, ctx):
        self.m_code = ctx.m_code
        self.m_errCode = ctx.m_errCode
        self.m_errMsg = ctx.m_errMsg
        self.m_lgnRsltCd = ctx.m_lgnRsltCd
        self.m_pswdErrNbcnt = ctx.m_pswdErrNbcnt
        self.m_secCardId = ctx.m_secCardId
        self.m_tin = ctx.m_tin

mSession_cookiecontainer = {}
mLoginSystem = {}
mLoginSystem_Main = LoginSystemContext()

class JsHometax:
  def __init__(self, parent):
          
      self.mSession_cookiecontainer = parent.mSession_cookiecontainer
      self.mLoginSystem = parent.mLoginSystem
      self.mLoginSystem_Main = parent.mLoginSystem_Main

  def login(id, password, result_LoginSystemCtx):
      global sbResponseData
      url = "https://www.hometax.go.kr/pubcLogin.do?domain=hometax.go.kr&mainSys=Y"
      pos = [0, 0, 0, 0]
      loginsysCode = ""
      loginsysctx = LoginSystemContext()

      flag = 0
      postdata = "ssoLoginYn=Y&secCardLoginYn=&secCardId=&id=" + urllib.parse.quote(id) + "&pswd=" + urllib.parse.quote(password) + "&ssoStatus=&portalStatus=&scrnId=UTXPPABA01&userScrnRslnXcCnt=1280&userScrnRslnYcCnt=960"
      rst = httpRequest_post(url, postdata, "https://www.hometax.go.kr/websquare/websquare.wq?w2xPath=/ui/pp/index_pp.xml", None, _HTTP_ContextType_POST, 'login')
      strResData = sbResponseData
      # print("IN LOGIN : ")
      # print(strResData)
      # while True:
      str = ["", "", "", ""]

      pos[0] = strResData.find("nts_loginSystemCallback")
      # if pos[0] < 0:  break
      pos[0] += 23
      pos[1] = getTagEndPos(strResData, pos[0], '(', ')')
      #print(pos[1]) # [" 'code' : 'S', 'errCode' : null, 'errMsg' : decodeURIComponent('').replace(/\\+/g,' ').replace(/\\\\n/g,'\\n'), 'lgnRsltCd' : '01', 'pswdErrNbcnt' : '0', 'tin' : '100000000030598298', 'secCardId' : null"]
      # if pos[0] < 0:    break
      pos[0] += 1
      pos[1] -= 1
      # print(pos[1])#[" 'code' : 'S', 'errCode' : null, 'errMsg' : decodeURIComponent('').replace(/\\+/g,' ').replace(/\\\\n/g,'\\n'), 'lgnRsltCd' : '01', 'pswdErrNbcnt' : '0', 'tin' : '100000000030598298', 'secCardId' : null"]
      str[0] = strResData[pos[0]:pos[1]]
      pos[0] = str[0].find("{")
      # if pos[0] < 0:    break
      loginsysCode = str[0][:pos[0]].replace("'", "").replace(",", "").strip()
      pos[0] += 1
      pos[1] = str[0].find("}", pos[0])
      # if pos[1] < 0:  break
      str[2] = str[0][pos[0]:pos[1]]
      strarr = str[2].split('\r\n,')
      strarr = strarr[0].replace("/g,","").split(',')
      flag |= 0x00000001
      for tmpstr in strarr:
          strarr2 = tmpstr.split(':')
          tmpname = ""
          tmpvalue = ""
          if len(strarr2) < 2:   continue
          tmpname = strarr2[0].replace("'", "").strip().lower()
          tmpvalue = strarr2[1].strip()

          if tmpname == "code":
              loginsysctx.m_code = tmpvalue.replace("'", "").strip()
              flag |= 0x00000010
          elif tmpname == "errcode":
              loginsysctx.m_errCode = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_errCode.lower() == "null":
                  loginsysctx.m_errCode = None
              flag |= 0x00000020
          elif tmpname == "errmsg":
              pos[2] = tmpvalue.find("'")
              if pos[2] >= 0:
                  pos[2] += 1
                  pos[3] = tmpvalue.find("'", pos[2])
              if pos[2] >= 0 and pos[3] >= 0:
                  loginsysctx.m_errMsg = requests.utils.unquote(tmpvalue[pos[2]:pos[3]])
                  flag |= 0x00000040
          elif tmpname == "ignrsltcd":
              loginsysctx.m_lgnRsltCd = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_lgnRsltCd.lower() == "null":
                  loginsysctx.m_lgnRsltCd = None
          elif tmpname == "pswderrnbcnt":
              loginsysctx.m_pswdErrNbcnt = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_pswdErrNbcnt.lower() == "null":
                  loginsysctx.m_pswdErrNbcnt = None
          elif tmpname == "tin":
              loginsysctx.m_tin = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_tin.lower() == "null":
                  loginsysctx.m_tin = None
          elif tmpname == "seccardid":
              loginsysctx.m_secCardId = tmpvalue.replace("'", "").strip()
              if loginsysctx.m_secCardId.lower() == "null":
                  loginsysctx.m_secCardId = None
          flag |= 0x00000080

      if flag != 0x000000F1:    return -1
      if result_LoginSystemCtx is not None:    result_LoginSystemCtx.copyFrom(loginsysctx)
      if loginsysctx.m_code.upper() == "S":
          result_errorCd = 0
          result_errorMsg = None
          if loginsysCode.upper() == "TXPP":
              # 메인 시스템일 경우 성공 로그인 정보 저장
              mLoginSystem_Main.copyFrom(loginsysctx)
          rst = requestPermission("https://www.hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index.xml", "www", "index", None, None, None, result_errorCd, result_errorMsg)
          return 1
      else:
          return 0
        
def getLoginStatus():
    if mLoginSystem_Main is None:                   return False
    if mLoginSystem_Main.m_code is None:            return False
    if mLoginSystem_Main.m_code.upper() == "S":
      return True
    else:
      return False

def requestPermission(refererurl, subdomain, screenId, domain, ssoToken, userClCd, result_errorCd, result_errorMsg):
    url = f"https://{subdomain}.hometax.go.kr/permission.do?screenId={urllib.parse.quote(screenId)}"
    rst = 0
    sbResponseData = ""
    if not getLoginStatus():   return -10
    if domain is not None:     url += f"&domain={urllib.parse.quote(domain)}"

    postdata = "<map id='postParam'><popupYn>false</popupYn>"
    if ssoToken is not None:        postdata += f"<ssoToken>{ssoToken}</ssoToken>"
    if userClCd is not None:        postdata += f"<userClCd>{userClCd}</userClCd>"
    postdata += "</map>"
    if subdomain == "www":      rst = httpRequest_post(url, postdata, refererurl, "https://www.hometax.go.kr", _HTTP_ContextType_XML, sbResponseData)
    else:                       rst = httpRequest_post(url, postdata, refererurl, "https://tecr.hometax.go.kr", _HTTP_ContextType_XML, sbResponseData)
    return rst

def httpRequest_post(url, postdata, refererUrl, originUrl, contentType, tmp):
    global sbResponseData
    try:
        params = urllib.parse.urlencode({'': postdata})
        headers = {
            'Content-type': contentType,
            'Referer': refererUrl,
            'User-Agent': 'Mozilla/5.0'
        }
        if originUrl is not None:            headers['Origin'] = originUrl
        response = requests.post(url, data=postdata.encode('ascii'), headers=headers, cookies=mSession_cookiecontainer)
        mSession_cookiecontainer.update(response.cookies.get_dict())
        # print("httpRequest_post:"+response.text)
        sbResponseData = response.text
        return 1
    except:
        return -1

def httpRequest_get(url, refererUrl, originUrl, tmp):
    global sbResponseData
    try:
        headers = {
            "User-Agent": HTTP_UserAgent,
            "Referer": refererUrl
        }
        cookies = mSession_cookiecontainer
        if originUrl is not None:
            headers["Origin"] = originUrl

        response = requests.get(url, headers=headers, cookies=cookies, timeout=HTTP_timeout)
        # print("httpRequest_get")
        # print(response.text)
        if response.status_code == 200:
            sbResponseData = response.text
            return 1
        else:
            return -1001
    except:
        return -1

def getTagEndPos(string, startpos, begin_tag, end_tag):
    curpos = string.find(begin_tag, startpos)
    if curpos < 0:
        return -1

    dimen = 1
    curpos += 1

    while dimen > 0:
        pos_a = string.find(begin_tag, curpos)
        pos_b = string.find(end_tag, curpos)

        if pos_a < 0:
            if pos_b >= 0:
                dimen -= 1
                curpos = pos_b + 1
                continue
            else:
                break  # ERROR

        if pos_b < pos_a:
            dimen -= 1
        else:
            dimen += 1

        curpos = min(pos_a, pos_b) + 1

    if dimen > 0:
        return -1

    return curpos

def getSSOToken(refererurl):
    global sbResponseData
    global sbSSOToken   
    global sbuserClCd 
    url = "https://www.hometax.go.kr/token.do"

    rst = 0
    sbResponseData = ""
    strResData = ""

    strdata = ""

    pos_a = 0
    pos_b = 0

    if not getLoginStatus():        return -10

    rst = httpRequest_get(url, refererurl, None, sbResponseData)
    strResData = sbResponseData
    # print("IN getSSOToken")
    # print(strResData)
    pos_a = strResData.find("<ssoToken>")
    if pos_a < 0:        return -10000
    pos_a += 10
    pos_b = strResData.find("</ssoToken>")
    if pos_b < 0:        return -10000

    strdata = strResData[pos_a: pos_b]
    if len(strdata) == 0 or strdata.lower() == "null":
        return -10131
    sbSSOToken = strdata

    pos_a = strResData.find("<userClCd>")
    if pos_a < 0:
        return -10000
    pos_a += 10
    pos_b = strResData.find("</userClCd>")
    if pos_b < 0:
        return -10000

    strdata = strResData[pos_a: pos_b]
    if len(strdata) == 0 or strdata.lower() == "null":
        return -10132
    sbuserClCd = strdata

    return 1

def getErrorString(errno):
    if errno == 1:
        return "성공"
    elif errno == 0:
        return "실패"
    elif errno == -1:
        return "기타오류"
    elif errno == -10:
        return "사용할 수 없는 상태입니다. 로그인 상태를 확인해주세요."
    elif errno == -1001:
        return "HTTP오류. 페이지를 찾을 수 없습니다."
    elif errno == -10000:
        return "파싱오류"
    elif errno == -10131:
        return "ssoToken 읽기 실패. 세션이 올바르지 않는 것으로 보입니다."
    elif errno == -10132:
        return "userClCd 읽기 실패. 세션이 올바르지 않는 것으로 보입니다."
    else:
        return "알수없는코드"
