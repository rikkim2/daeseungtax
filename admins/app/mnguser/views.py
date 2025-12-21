import json
import datetime
import logging
from django.db import connection
from django.http import JsonResponse
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse

from app.models import MemAdmin
from app.models import MemDeal
from app.models import MemUser  # KijangMember는 "기장회원관리"와 관련된 모델이라고 가정합니다.
from .forms import MemUserForm  # 기장회원 생성/수정 폼이라고 가정합니다.
from app.models import userProfile
from admins.utils import (
    kijang_member_popup,
    getMailContent,
    getSentMails,
    sendMail,
    send_kakao_notification,
    send_sms_popbill,
    get_sms_prefill,
    get_popbill_balance,
    get_sent_sms_list
)
from .forms import MemberProfileUploadForm
from django.db.models import Q
from admins.utils import get_mail_date
from admins.utils import render_tab_template  # ★ 공통 함수 임포트 확인
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Max

logger = logging.getLogger(__name__)

@login_required(login_url="/login/")
def index(request):
  context = {}

  admin_grade       = request.session.get('Admin_Grade')
  admin_biz_level = request.session.get('Admin_Biz_Level')
  admin_biz_area  = request.session.get('Admin_Area')
  admin_id        = request.session.get('Admin_Id')
  ADID = request.GET.get("ADID", "")
  flag = request.GET.get("flag", "")
 
  arr_ADID = []
  if admin_grade != "SA":
      if admin_biz_level == "세무사":
          # Query for admin_id
          arr_ADID = MemAdmin.objects.filter(
              ~Q(grade="SA"),
              ~Q(biz_level="세무사"),
              ~Q(del_yn="y"),
              admin_biz_area = admin_biz_area
          ).order_by('admin_id').values_list('admin_id', flat=True)
  else:  # admin_grade == "SA"
      arr_ADID = list(MemAdmin.objects.filter(
          ~Q(grade="SA"),
          ~Q(biz_level="세무사"),
          ~Q(del_yn="y")
      ).order_by("admin_id").values_list('admin_id', flat=True))
      arr_ADID.insert(0, "전체")

  if not ADID:
    ADID = arr_ADID[0] if arr_ADID else ""
  request.session['ADID'] = ADID  
  request.session.save()
  gridTitle = templateMenu = ""
  if flag == 'All' or flag=='Can' or flag=='Nor':
    if flag == "All":
      gridTitle = "기장회원관리"
    elif flag == "Can":
      gridTitle = "해임회원관리"
    elif flag == "Nor":
      gridTitle = "일반가입회원"      
    templateMenu = 'admin/kijang_member_list.html';
  elif flag == "Goji":
    gridTitle = "고지세액 안내(지방세 제외)"    
    templateMenu = 'admin/kijang_goji_list.html'; 
  elif flag == 'RND':
    gridTitle = "연구인력개발세액공제 사전심사 안내"  
    templateMenu = 'admin/kijang_RND_list.html'; 
  elif flag == "SaleTIMail":
    gridTitle = "매출세금계산서 발송대행"  
    templateMenu = 'admin/kijang_SaleTIMail_list.html';
  context.update({
    "ADID" : ADID,
    "flag" : flag,
    "arr_ADID" : json.dumps(list(arr_ADID)),
    "admin_biz_level" : admin_biz_level,
    "admin_grade" : admin_grade,
    'gridTitle' :  gridTitle,
  })  
  # ★ [변경] 탭 요청인 경우 fragment 템플릿 렌더링을 위해 render 대신 render_tab_template 사용
  return render_tab_template(request, templateMenu, context)

# 고지세액 안내
def kijang_goji_list(request):
  work_YY = request.GET.get('work_YY', '')
  work_MM = request.GET.get('work_MM', '')  
  if request.method == 'GET':  
    sql = f"""
      SELECT 
          b.biz_manager,
          a.seq_no,
          a.biz_name,
          d.searchDate,
          d.mailDate,
          d.taxMok,
          d.taxAmt,
          d.taxNapbuNum,
          d.taxOffice,
          d.taxDuedate
      FROM 
          mem_user a
      JOIN 
          mem_deal b ON a.seq_no = b.seq_no
      JOIN 
          tbl_goji d ON b.seq_no = d.seq_no
      WHERE 
          d.work_yy = '{work_YY}'
          AND d.work_mm = '{work_MM}'
          AND a.del_yn <> 'Y'
          AND a.duzon_ID <> ''
          AND b.keeping_YN = 'Y'
          AND a.Del_YN <> 'Y'
      ORDER BY 
          b.biz_manager, a.biz_name;
    """.format()
    recordset = []
    with connection.cursor() as cursor:
      cursor.execute(sql)
      results = cursor.fetchall()
      for row in results:
        ( biz_manager,seq_no,biz_name,searchDate,mailDate,taxMok,taxAmt,taxNapbuNum,taxOffice,taxDuedate    ) = row  
        if mailDate.strip()=="":
          mailDate = get_mail_date(seq_no, int(work_YY), int(work_MM),"goji")            
        record_dict  =  {
          'groupManager'          : biz_manager,
          'seq_no'              : seq_no,
          'biz_name'            : biz_name,
          'searchDate'          : searchDate,
          'taxMok'      : taxMok,
          'taxAmt'          : taxAmt,
          'taxNapbuNum'         : taxNapbuNum,
          'taxOffice'              : taxOffice,
          'taxDuedate'        : taxDuedate,
          'mailDate'          : mailDate,
        }
        recordset.append(record_dict)      
        # print(recordset)           
    return JsonResponse(list(recordset), safe=False)
  else:
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
    
# 기장 회원 목록 보기
def kijang_member_list(request):
  ADID = request.GET.get('ADID')
  if not ADID:ADID = request.session.get('ADID')
  request.session['ADID'] = ADID  
  flag = request.GET.get("flag","")
  request.session.save()
  if request.method == 'GET':
      sqlMem = ""
      if flag == "All":
          sqlMem = "a.duzon_id <> '' AND b.keeping_YN = 'Y'  "
      elif flag == "Can":
          sqlMem = "a.duzon_id <> '' AND b.keeping_YN <> 'Y' "
      else:
          sqlMem = "a.duzon_id = '' "
      #영업팀
      if ADID!="전체":
          sqlMem += f" AND (b.biz_manager = '{ADID}' or a.biz_par_chk = '{ADID}')"
      sql = """
          SELECT 
              a.seq_no as sqno,biz_name,duzon_id,Biz_Type,uptae,jongmok,kijang_yn,hometaxAgree,
              goyoung_jungkyu,goyoung_ilyoung,goyoung_sayoup,goyoung_banki,biz_zipcode,(biz_addr1+biz_addr2) as biz_addr,
              FORMAT(a.reg_date, 'yyyy-MM-dd') AS Reg_Date,biz_manager,keeping_yn,ceo_name,biz_manager as groupManager
          FROM 
              mem_user a
          JOIN 
              mem_deal b ON a.seq_no = b.seq_no
          JOIN 
              mem_admin c ON b.biz_manager = c.admin_id
          WHERE 
              a.Del_YN <> 'Y' AND {}
          order by biz_name
      """.format(sqlMem)
      
      # SQL 실행
    #   print(sql)
      with connection.cursor() as cursor:
          cursor.execute(sql)
          results = cursor.fetchall()

      # 데이터 반환
      data = [
          {
              "groupManager":row[18],
              "seq_no": row[0],
              "biz_name":row[1],
              "duzon_id":row[2],
              "biz_type":row[3],
              "uptae":row[4],
              "jongmok":row[5],
              "kijang_yn":row[6],
              "hometaxAgree":row[7],
              "goyoung_jungkyu":row[8],
              "goyoung_ilyoung":row[9],
              "goyoung_sayoup":row[10],
              "goyoung_banki":row[11],
              "biz_zipcode":row[12],
              "biz_addr":row[13],
              "reg_date":row[14],
              "biz_manager":row[15],
              "keeping_yn":row[16],
              "ceo_name":row[17]
          }
          for row in results
      ]             
      # print(data[0]) 
      return JsonResponse(list(data), safe=False)
  else:
      return JsonResponse({'error': 'Invalid request method.'}, status=400)

# 관리자 콤보 목록 보기
def kijang_admin_combolist(request):
    admins = MemAdmin.objects.filter(Q(manage_YN="Y") | Q(manage_YN="S")).order_by("admin_id")
    # arrAdmin = list(admins.values_list("admin_id", flat=True))
    # print(arrAdmin)
    if request.method == 'GET':
        data = [
            {
                "id": admin.admin_id,
                "name": admin.admin_id,
            }
            for admin in admins
        ]
        # print(data)
        return JsonResponse(list(data), safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

# 기장 회원 수정하기(컬럼)
def kijang_member_edit(request):
    if request.method == 'GET':
        seq_no = request.GET.get('seq_no')
        target = request.GET.get('target')
        val = request.GET.get('val', '').strip()

        if target == "reg_date":
            val = val[:10]  # reg_date는 처음 10자리만 사용
        elif target == "DK_manage":
            val = 1 if val else 0

        # 해당 seq_no를 가진 사용자가 존재하는지 확인
        mem_user = get_object_or_404(MemUser, seq_no=seq_no)

        # 동적으로 필드 업데이트
        if target in ("biz_manager","keeping_yn"):
            mem_deal = get_object_or_404(MemDeal, seq_no=seq_no)
            if hasattr(mem_deal, target):
                setattr(mem_deal, target, val)
                mem_deal.save()
                return JsonResponse({"status": "success", "message": "Updated successfully."})
            else:
                return JsonResponse({"status": "error", "message": "Invalid target field."}, status=400)
        else:
            if hasattr(mem_user, target):
                setattr(mem_user, target, val)
                mem_user.save()
                return JsonResponse({"status": "success", "message": "Updated successfully."})
            else:
                return JsonResponse({"status": "error", "message": "Invalid target field."}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)

# 기장 회원 수정하기
def kijang_member_update(request, id):
    member = get_object_or_404(MemUser, id=id)
    if request.method == 'POST':
        form = MemUserForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            return redirect('mnguser:kijang_member_detail', id=member.id)
    else:
        form = MemUserForm(instance=member)
    return render(request, 'admin/kijang_member_form.html', {'form': form})

# 기장 회원 상세 보기
def kijang_member_detail(request, id):
    member = get_object_or_404(MemUser, id=id)
    return render(request, 'admin/kijang_member_detail.html', {'member': member})

# 기장 회원 생성하기
def kijang_member_create(request):
    if request.method == 'POST':
        form = MemUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mnguser:kijang_member_list')
    else:
        form = MemUserForm()
    return render(request, 'admin/kijang_member_create.html', {'form': form})
    # return render(request, 'admin/form-advanced.html', {'form': form})    



@require_http_methods(["GET"])
def kijang_member_form(request):
    seq_no = request.GET.get('seq_no')

    member = None
    deal = None
    profile = None

    if seq_no:
        member = get_object_or_404(MemUser, seq_no=seq_no)
        # 기장정보 등 다른 테이블
        try:
            deal = MemDeal.objects.get(seq_no=seq_no)
        except MemDeal.DoesNotExist:
            deal = None
        # ✅ 대상 유저(seq_no) 프로필 조회
        # Pick latest saved profile image.
        # Ordering by description is unreliable because member_form can submit a static timestamp value.
        qs = userProfile.objects.filter(title=member.seq_no)
        profile = qs.order_by("-id").first()
        try:
            print(
                "[kijang_member_form] seq_no=",
                seq_no,
                "profiles=",
                qs.count(),
                "selected_id=",
                getattr(profile, "id", None),
                "selected_url=",
                getattr(getattr(profile, "image", None), "url", None),
            )
        except Exception:
            pass
    context = {
        'user': member,
        'deal': deal,
        'userProfile': profile,                      # ✅ 추가
        'dateNow': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # ✅ 추가
    }
    # 모달로 로드되는 폼이므로 base 상속 없이 render 사용 유지 (TabManager 사용 X)
    return render(request, 'admin/member_form.html', context)


@login_required(login_url="/login/")
@require_http_methods(["POST"])
def kijang_member_fileupload(request):
    """
    회원(=MemUser) 이미지 업로드.
    - staffInfo.fileupload는 관리자(User.profile)용이라 member_form에서는 사용하면 안 됨.
    - member_form은 userProfile.title=member.seq_no 로 조회하므로 userProfile.user는 null로 저장.
    """
    seq_no = (request.POST.get("seq_no") or "").strip()
    image = request.FILES.get("image")

    logger.info(
        "[kijang_member_fileupload] start user=%s seq_no=%s has_image=%s filename=%s size=%s content_type=%s",
        getattr(request.user, "username", None),
        seq_no,
        bool(image),
        getattr(image, "name", None),
        getattr(image, "size", None),
        getattr(image, "content_type", None),
    )
    print(
        "[kijang_member_fileupload] start",
        getattr(request.user, "username", None),
        seq_no,
        bool(image),
        getattr(image, "name", None),
        getattr(image, "size", None),
        getattr(image, "content_type", None),
    )

    if not seq_no or not image:
        logger.warning(
            "[kijang_member_fileupload] missing required fields seq_no=%s has_image=%s",
            seq_no,
            bool(image),
        )
        print("[kijang_member_fileupload] missing required fields", seq_no, bool(image))
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "error": "seq_no and image are required"}, status=400)
        return HttpResponse("seq_no and image are required", status=400)

    get_object_or_404(MemUser, seq_no=seq_no)

    title = (request.POST.get("title") or "").strip() or seq_no
    # Always generate a fresh timestamp so "latest" is deterministic even if the client posts a static value.
    description = timezone.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    form = MemberProfileUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        logger.warning("[kijang_member_fileupload] invalid form seq_no=%s errors=%s", seq_no, form.errors)
        print("[kijang_member_fileupload] invalid form", seq_no, dict(form.errors))
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": False, "errors": form.errors}, status=400)
        return HttpResponse("invalid upload", status=400)

    profile = form.save(commit=False)
    profile.user = None
    profile.title = str(title)
    profile.description = str(description)
    profile.save()

    logger.info(
        "[kijang_member_fileupload] saved seq_no=%s profile_id=%s image_url=%s",
        seq_no,
        getattr(profile, "id", None),
        getattr(profile.image, "url", ""),
    )
    print("[kijang_member_fileupload] saved", seq_no, getattr(profile, "id", None), getattr(profile.image, "url", ""))

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "ok": True,
                "seq_no": seq_no,
                "image_url": getattr(profile.image, "url", ""),
            }
        )

    return redirect(f"{reverse('kijang_member_form')}?seq_no={seq_no}")


def _parse_datefield_to_dt(s: str):
    """
    'YYYY-MM-DD' 문자열을 DateTime으로 변환.
    비어있으면 None 반환.
    """
    if not s:
        return None
    d = parse_date(s)
    if not d:
        return None
    return datetime.datetime.combine(d, datetime.time(0, 0))


@csrf_exempt  # Ajax에서 CSRF 토큰 헤더로 잘 보내면 제거해도 됨
@require_http_methods(["POST"])
@transaction.atomic
def kijang_member_save(request):
    """
    기장 회원 신규/수정 저장
    - seq_no 있으면: 수정
    - seq_no 없으면: 신규 (MemUser.seq_no 기준으로 +1 생성)
    """

    seq_no = (request.POST.get('seq_no') or '').strip()
    is_new = not bool(seq_no)

    # ─────────────────────────────────────
    # 1) 신규인 경우 seq_no 생성
    # ─────────────────────────────────────
    if is_new:
        last = MemUser.objects.aggregate(max_no=Max('seq_no'))['max_no']
        try:
            last_int = int(last or "0")
        except ValueError:
            last_int = 0
        seq_no = f"{last_int + 1:04d}"  # 4자리 zero-fill (예: 0001, 0002 ...)

    # ─────────────────────────────────────
    # 2) 공통 입력값 파싱
    # ─────────────────────────────────────
    # 기본정보
    user_id     = (request.POST.get('user_id') or '').strip()
    user_pwd    = (request.POST.get('user_pwd') or '').strip()
    duzon_id    = (request.POST.get('duzon_id') or '').strip()
    biz_manager = (request.POST.get('biz_manager') or '').strip()
    kijang_yn   = (request.POST.get('kijang_yn') or 'Y').strip()
    keeping_yn  = (request.POST.get('keeping_yn') or 'Y').strip()
    reg_date_s  = (request.POST.get('reg_date') or '').strip()
    createddate_s = (request.POST.get('createddate') or '').strip()
    feeamt_raw  = (request.POST.get('feeamt') or '').replace(',', '').strip()

    # 영업담당자(신규 필드)
    biz_par_chk = (request.POST.get('Biz_Par_Chk') or request.POST.get('biz_par_chk') or '').strip()

    # 회사정보
    biz_type_raw = (request.POST.get('biz_type') or '').strip()
    #biz_no    = (request.POST.get('biz_no') or '').replace('-', '').strip()
    biz_no_raw = request.POST.get('biz_no', '').strip()

    biz_name  = (request.POST.get('biz_name') or '').strip()
    ceo_name  = (request.POST.get('ceo_name') or '').strip()
    ssn       = (request.POST.get('ssn') or '').replace('-', '').strip()

    biz_zipcode   = (request.POST.get('biz_zipcode') or request.POST.get('sample6_postcode') or '').strip()
    biz_addr1     = (request.POST.get('biz_addr1') or request.POST.get('sample6_address') or '').strip()
    biz_addr2     = (request.POST.get('biz_addr2') or request.POST.get('sample6_detailAddress') or '').strip()

    zipcode   = (request.POST.get('zipcode') or request.POST.get('sample7_postcode') or '').strip()
    addr1     = (request.POST.get('addr1') or request.POST.get('sample7_address') or '').strip()
    addr2     = (request.POST.get('addr2') or request.POST.get('sample7_detailAddress') or '').strip()

    uptaecd   = (request.POST.get('uptaecd') or '').strip()
    uptae     = (request.POST.get('uptae') or '').strip()
    jongmok   = (request.POST.get('jongmok') or '').strip()
    fiscalmm  = (request.POST.get('fiscalmm') or '').strip()  # MemDeal.fiscalmm

    # 연락처
    name      = (request.POST.get('name') or '').strip()
    email     = (request.POST.get('email') or '').strip()
    tel_no    = (request.POST.get('tel_no') or '').strip()
    hp_no     = (request.POST.get('hp_no') or '').strip()
    biz_tel   = (request.POST.get('biz_tel') or '').strip()
    biz_fax   = (request.POST.get('biz_fax') or '').strip()
    taxmgr_name = (request.POST.get('taxmgr_name') or '').strip()
    taxmgr_tel  = (request.POST.get('taxmgr_tel') or '').strip()
    taxmgr_fax  = (request.POST.get('taxmgr_fax') or '').strip()

    # 세무관리 / 인사급여
    hometaxagree = (request.POST.get('hometaxagree') or 'N').strip()
    hometaxid    = (request.POST.get('hometaxid') or '').strip()
    hometaxpw    = (request.POST.get('hometaxpw') or '').strip()
    taxsaveid    = (request.POST.get('taxsaveid') or '').strip()
    taxsavepw    = (request.POST.get('taxsavepw') or '').strip()
    cms_yn       = (request.POST.get('cms_yn') or 'Y').strip()

    isrnd        = 'Y' if request.POST.get('isrnd') else 'N'
    isventure    = 'Y' if request.POST.get('isventure') else 'N'

    goyoung_jungkyu = 'Y' if request.POST.get('goyoung_jungkyu') else 'N'
    goyoung_ilyoung = 'Y' if request.POST.get('goyoung_ilyoung') else 'N'
    goyoung_sayoup  = 'Y' if request.POST.get('goyoung_sayoup') else 'N'
    goyoung_banki   = 'Y' if request.POST.get('goyoung_banki') else 'N'
    # goyoung_diff 는 모델에 없으므로 생략

    ediid  = (request.POST.get('ediid') or '').strip()
    edipw  = (request.POST.get('edipw') or '').strip()
    sale_ti_name = (request.POST.get('SaleTIName') or '').strip()
    sale_ti_mail = (request.POST.get('SaleTIMail') or '').strip()
    sinca_sale   = (request.POST.get('sinca_sale') or '').strip()
    coution_account = (request.POST.get('coution_account') or '').strip()  # 모델엔 없음

    etc_txt = (request.POST.get('etc') or '').strip()

    taltye_date   = (request.POST.get('taltye_date') or '').strip()
    taltye_reason = (request.POST.get('taltye_reason') or 'empty').strip()

    # ─────────────────────────────────────
    # 3) 필수값 검증
    # ─────────────────────────────────────
    if not user_id or not biz_name:
        return JsonResponse({'ok': False, 'msg': '회원아이디와 상호는 필수입니다.'})

    # 숫자 변환
    try:
        feeamt = Decimal(feeamt_raw or '0')
    except Exception:
        feeamt = Decimal('0')

    try:
        biz_type = int(biz_type_raw) if biz_type_raw else 0
    except ValueError:
        biz_type = 0

    # upjong은 업종코드(uptaecd)를 기준으로 대략 0/기타 처리 (상세 맵핑 있으면 수정)
    try:
        upjong = int(uptaecd) if uptaecd else 0
    except ValueError:
        upjong = 0

    # 날짜 변환
    reg_date_dt = _parse_datefield_to_dt(reg_date_s)
    created_dt  = _parse_datefield_to_dt(createddate_s)

    # ─────────────────────────────────────
    # 4) MemUser 로드/생성
    # ─────────────────────────────────────
    if is_new:
        member = MemUser(seq_no=seq_no)
    else:
        try:
            member = MemUser.objects.get(seq_no=seq_no)
        except MemUser.DoesNotExist:
            # 혹시 없으면 신규로 생성
            member = MemUser(seq_no=seq_no)
            is_new = True

    # MemUser 필드 매핑
    member.duzon_id = duzon_id
    member.user_id  = user_id
    if user_pwd:
        member.user_pwd = user_pwd

    member.name  = name
    member.ssn   = ssn
    member.email = email

    member.zipcode = zipcode
    member.addr1   = addr1
    member.addr2   = addr2
    member.tel_no  = tel_no
    member.hp_no   = hp_no

    # 사업자/회사 정보
    member.biz_type   = biz_type
    member.upjong     = upjong
    member.biz_no     = biz_no_raw
    member.biz_name   = biz_name
    member.ceo_name   = ceo_name
    member.uptae      = uptae
    member.jongmok    = jongmok
    member.biz_zipcode = biz_zipcode
    member.biz_addr1   = biz_addr1
    member.biz_addr2   = biz_addr2
    member.biz_tel     = biz_tel
    member.biz_fax     = biz_fax

    member.biz_par_chk = biz_par_chk
    member.uptaecd   = uptaecd
    member.isrnd     = isrnd
    member.isventure = isventure

    member.saletiname = sale_ti_name
    member.saletimail = sale_ti_mail

    member.reg_date = reg_date_dt or member.reg_date
    member.up_date  = timezone.now()

    member.etc = etc_txt

    # 아래 값들은 기존 시스템 default가 있다면 그에 맞게 조정 필요
    if is_new:
        # 신규 기본값들 (필요에 맞게 수정)
        member.del_yn = getattr(member, 'del_yn', 'N') or 'N'
        member.del_date = timezone.now()
        member.del_reason = getattr(member, 'del_reason', '') or ''
        member.pay_month = member.pay_month or 0
        member.pay_year  = member.pay_year or 0
        member.pay_not   = member.pay_not or 0
        member.sale_confirm = member.sale_confirm or ''
        member.taxation_no  = member.taxation_no or ''
        member.taxoffice_code = member.taxoffice_code or ''
        member.taxbank_acc    = member.taxbank_acc or ''
        member.ward_off       = member.ward_off or ''
        member.biz_start_day  = member.biz_start_day or ''
        member.biz_end_day    = member.biz_end_day or ''
        member.biz_end_reason = member.biz_end_reason or ''
        member.ret_bank_code  = member.ret_bank_code or ''
        member.ret_bank_name  = member.ret_bank_name or ''
        member.ret_account    = member.ret_account or ''
        member.biz_area       = member.biz_area or ''

    member.save()

    # ─────────────────────────────────────
    # 5) MemDeal 로드/생성
    # ─────────────────────────────────────
    deal, _created = MemDeal.objects.get_or_create(seq_no=seq_no)

    deal.biz_manager    = biz_manager
    deal.kijang_yn      = kijang_yn
    deal.keeping_yn     = keeping_yn
    deal.cms_yn         = cms_yn
    deal.goyoung_jungkyu = goyoung_jungkyu
    deal.goyoung_ilyoung = goyoung_ilyoung
    deal.goyoung_sayoup  = goyoung_sayoup
    deal.goyoung_banki   = goyoung_banki

    deal.ediid = ediid
    deal.edipw = edipw

    deal.taxsaveid = taxsaveid
    deal.taxsavepw = taxsavepw
    deal.hometaxid = hometaxid
    deal.hometaxpw = hometaxpw
    deal.hometaxagree = hometaxagree

    deal.taxmgr_name = taxmgr_name
    deal.taxmgr_tel  = taxmgr_tel
    deal.taxmgr_fax  = taxmgr_fax

    deal.createddate = created_dt or deal.createddate
    deal.feeamt      = feeamt
    deal.taltyoedate   = taltye_date
    deal.taltyoereason = taltye_reason if taltye_reason != 'empty' else ''

    deal.fiscalmm    = fiscalmm
    deal.tel_sincasale = sinca_sale

    # sanjaerate는 별도 입력 없으니 기본값 유지
    if not deal.sanjaerate:
        deal.sanjaerate = '0'

    deal.save()

    msg = '신규 등록되었습니다.' if is_new else '수정되었습니다.'
    return JsonResponse({'ok': True, 'msg': msg, 'seq_no': seq_no})


# 기장 회원 삭제하기
def kijang_member_delete(request, id):
    member = get_object_or_404(MemUser, id=id)
    if request.method == 'POST':
        member.delete()
        return redirect('mnguser:kijang_member_list')
    return render(request, 'admin/kijang_member_confirm_delete.html', {'member': member})
