import json
import mimetypes
import os
import re
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET, require_POST
from django.db import connection
from django.utils import timezone
from django.db.models import Q
from app.models import MemUser
from app.models import MemAdmin  
from django.http import Http404
from django.conf import settings
from pathlib import Path
from django.core.files.storage import FileSystemStorage
from dotenv import load_dotenv
from popbill import MessageService, PopbillException
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

@require_GET
def mngMsg(request):
  admin_grade, admin_biz_level, admin_biz_area, arr_adid = _get_admin_list(request)

  ADID = (request.session.get("ADID") or request.user.username or "").strip()
  if not ADID:
      ADID = arr_adid[0] if arr_adid else ""

  admin_name = ""
  admin_tel_no = ""
  if ADID:
      contact = (
          MemAdmin.objects.filter(admin_id=ADID)
          .values("admin_name", "admin_tel_no")
          .first()
      )
      if contact:
          admin_name = contact.get("admin_name") or ""
          admin_tel_no = contact.get("admin_tel_no") or ""

  flag = (request.GET.get("flag") or "sms").lower()
  print(f"[mngMsg] flag:{flag},ADID:{ADID}")

  returnUrl = ""
  if flag == "sms":
    returnUrl =  "admin/mng_MsgSms.html"
  if flag == "mail":
    returnUrl =  "admin/mng_MsgMail.html"
  context = {
      "admin_grade": admin_grade,
      "admin_biz_level": admin_biz_level,
      "ADID": ADID,
      "arr_ADID": json.dumps(arr_adid, ensure_ascii=False),
      "admin_name": admin_name,
      "admin_tel_no": admin_tel_no,
      "flag":flag
  }
  return render(request,returnUrl, context)
  
def _get_admin_list(request):
    admin_grade     = (request.session.get("Admin_Grade") or "").strip()
    admin_biz_level = (request.session.get("Admin_Biz_Level") or "").strip()
    admin_biz_area  = (request.session.get("Admin_Area") or "").strip()

    arr_adid = []
    if admin_grade != "SA":
        if admin_biz_level == "세무사":
            arr_adid = list(
                MemAdmin.objects.filter(
                    ~Q(grade="SA"),
                    ~Q(biz_level="세무사"),
                    ~Q(del_yn="y"),
                    admin_biz_area=admin_biz_area,
                ).order_by("admin_id").values_list("admin_id", flat=True)
            )
    else:
        arr_adid = list(
            MemAdmin.objects.filter(
                ~Q(grade="SA"),
                ~Q(biz_level="세무사"),
                ~Q(del_yn="y"),
            ).order_by("admin_id").values_list("admin_id", flat=True)
        )
        arr_adid.insert(0, "전체")

    return admin_grade, admin_biz_level, admin_biz_area, arr_adid

# ─────────────────────────────────────────────────────────
# SMS
# ─────────────────────────────────────────────────────────
@require_GET
def sms_data(request):
    """
    문자 대상 리스트 (JSON)

    """
    sms_class = request.GET.get("sms_class", "vat")   # 기존 ASP의 flag 역할(부가세/급여/종소세 등)
    search_text = (request.GET.get("search_text") or "").strip()
    ADID = (request.GET.get("ADID") or "").strip()
    if not ADID:
        ADID = (request.session.get("ADID") or "").strip()
    request.session["ADID"] = ADID

    where_parts = [
        "a.Del_YN <> 'Y'",
        "b.keeping_YN = 'Y'",
        "a.duzon_ID <> ''",
    ]
    params = []

    if search_text:
        where_parts.append("(a.biz_name LIKE %s OR a.ceo_name LIKE %s OR a.hp_no LIKE %s)")
        like = f"%{search_text}%"
        params += [like, like, like]

    # 담당자(ADID) 필터: '전체'가 아니면 biz_manager로 필터
    if ADID and ADID != "전체":
        where_parts.append("b.biz_manager = %s")
        params.append(ADID)

    where_sql = " AND ".join(where_parts)

    # 템플릿별 추가 조건 (mailFlag 참고)
    template_where_map = {
        "pay": "(b.goyoung_jungkyu = 'Y' OR b.goyoung_sayoup = 'Y' OR b.goyoung_ilyoung = 'Y')",
        "yearend": "",  # 연말정산은 조건 없음
        "younmal": "(b.goyoung_jungkyu = 'Y')",
        "ilyoung": "(b.goyoung_ilyoung = 'Y')",
        "vat": "(a.Biz_Type IN ('1','4'))",
        "nonvat": "(a.Biz_Type IN ('2','6'))",
        "corptax": "(a.Biz_Type BETWEEN '1' AND '3')",
        "incometax": "(a.Biz_Type BETWEEN '4' AND '7')",
    }
    extra_where = template_where_map.get(sms_class.lower())
    if extra_where:
        where_sql = f"({where_sql}) AND {extra_where}"

    sql = f"""
        SELECT
            b.biz_manager as groupManager,
            c.admin_name,
            c.admin_tel_no,        
            a.ceo_name,
            a.biz_name,
            a.hp_no,
            a.seq_no,
            a.biz_no,
            ISNULL(CONVERT(varchar(16), d.sms_send_dt, 120), '')     AS sms_send_dt,
            ISNULL(d.sms_send_result, '')                             AS sms_send_result
        FROM mem_user a
        JOIN mem_deal b ON a.seq_no = b.seq_no
        left join mem_admin c on b.biz_manager=c.admin_id
        LEFT JOIN Tbl_SMS d
               ON a.seq_no = d.seq_no
              AND d.sms_class = %s
              AND d.sms_send_dt = (
                    SELECT MAX(sms_send_dt)
                    FROM Tbl_SMS
                    WHERE seq_no = a.seq_no
                      AND sms_class = %s
              )
        WHERE {where_sql}
        ORDER BY a.biz_name
    """
    params = [sms_class, sms_class] + params

    rows = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        for idx, r in enumerate(cur.fetchall()):
            obj = dict(zip(cols, r))
            obj["row_num"] = idx
            rows.append(obj)

    return JsonResponse({"ok": True, "rows": rows})

@require_POST
def sms_send(request):
    """
    SMS 전송(즉시/예약)
    - EmmaSMS/외부 전송은 여기서 처리
    - 결과 Tbl_SMS 저장
    """
    sms_class = request.POST.get("sms_class", "vat")
    msg = (request.POST.get("msg") or "").strip()
    seqs = request.POST.getlist("seq_no[]")
    hps = request.POST.getlist("hp_no[]")

    toSendDate = request.POST.get("toSendDate", "")
    toSendHours = request.POST.get("toSendHours", "")
    toSendMinute = request.POST.get("toSendMinute", "")

    # SMS 내용 길이 제한(테이블 컬럼 초과 방지)
    MAX_SMS_LEN = 400
    if len(msg) > MAX_SMS_LEN:
        msg = msg[:MAX_SMS_LEN]

    if not msg:
        return JsonResponse({"success": False, "ok": False, "message": "내용을 입력하세요."}, status=400)
    if not seqs or not hps or len(seqs) != len(hps):
        return JsonResponse({"success": False, "ok": False, "message": "대상을 선택하세요."}, status=400)

    # Popbill 설정 로드 (admins/.env 우선, 없으면 프로젝트 루트/noa/.env)
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    env_candidates = [
        os.path.join(os.path.dirname(os.path.dirname(CURRENT_DIR)), ".env"),  # admins/.env
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))), ".env"),  # 프로젝트 루트/.env
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))), "noa", ".env"),  # noa/.env
    ]
    env_loaded = None
    for env_path in env_candidates:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            env_loaded = env_path
            break
    LinkID = os.getenv("LinkID")
    SecretKey = os.getenv("SecretKey")
    CorpNum = os.getenv("CorpNum")
    senderNumber = (os.getenv("senderNumber") or "").replace("-", "").strip()
    if not (LinkID and SecretKey and CorpNum and senderNumber):
        print(f"[sms_send] Popbill env missing. loaded_from={env_loaded} LinkID={LinkID} CorpNum={CorpNum} senderNumber={senderNumber}")
    if not (LinkID and SecretKey and CorpNum and senderNumber):
        return JsonResponse({"success": False, "ok": False, "message": "Popbill 설정을 확인하세요."}, status=500)

    try:
        messageService = MessageService(LinkID, SecretKey)
        messageService.IsTest = False
    except Exception as e:
        return JsonResponse({"success": False, "ok": False, "message": f"Popbill 초기화 실패: {e}"}, status=500)

    now = timezone.now()
    success_cnt = 0
    fail_items = []

    def _byte_len(s: str) -> int:
        try:
            return len(s.encode("utf-8"))
        except Exception:
            return len(s)

    def _cut_by_bytes(s: str, max_bytes: int) -> str:
        out = []
        total = 0
        for ch in s:
            bl = _byte_len(ch)
            if total + bl > max_bytes:
                break
            out.append(ch)
            total += bl
        return "".join(out)

    def get_sender_number(seq_no):
        with connection.cursor() as c2:
            c2.execute(
                """
                SELECT m.admin_tel_no
                FROM mem_deal d
                LEFT JOIN Mem_Admin m ON d.biz_manager = m.admin_id
                WHERE d.seq_no = %s
                """,
                [seq_no],
            )
            row = c2.fetchone()
            if row and row[0]:
                return (row[0] or "").replace("-", "").strip()
        return senderNumber

    with connection.cursor() as cur:
        print(f"[sms_send] send count={len(seqs)} sms_class={sms_class} msg_len={len(msg)}")
        for seq_no, hp in zip(seqs, hps):
            hp_clean = (hp or "").replace("-", "").strip()
            if not hp_clean:
                fail_items.append(f"seq_no {seq_no}: 수신번호 없음")
                continue

            send_ok = False
            error_msg = ""
            byte_len = _byte_len(msg)
            is_lms = byte_len > 90
            subject = _cut_by_bytes(msg, 40) if is_lms else ""
            sender_hp = get_sender_number(seq_no)
            try:
                if is_lms:
                    receiptNum = messageService.sendLMS(
                        CorpNum,
                        sender_hp,
                        hp_clean,
                        "",
                        subject,
                        msg,
                        "",
                        False,
                        None,
                    )
                else:
                    receiptNum = messageService.sendSMS(
                        CorpNum,
                        sender_hp,
                        hp_clean,
                        "",
                        msg,
                        "",
                        False,
                        None,
                    )
                send_ok = True
            except PopbillException as pe:
                error_msg = f"{pe.code}: {pe.message}"
            except Exception as e:
                error_msg = str(e)

            try:
                cur.execute(
                    """
                    INSERT INTO Tbl_SMS (seq_no, sms_class, sms_send_dt, sms_send_result, sms_contents, sms_tel_no)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    [seq_no, sms_class, now, "Y" if send_ok else "N", msg, hp_clean],
                )
            except Exception as e:
                send_ok = False
                error_msg = (error_msg + " / DB: " + str(e)) if error_msg else f"DB: {e}"

            if send_ok:
                success_cnt += 1
            else:
                fail_items.append(error_msg or f"seq_no {seq_no}: 알 수 없는 오류")

    if fail_items:
        return JsonResponse(
            {"success": False, "ok": False, "message": f"성공 {success_cnt}건, 실패 {len(fail_items)}건. 첫 실패 사유: {fail_items[0]}"},
            status=200,
        )

    return JsonResponse({"success": True, "ok": True, "message": f"성공 {success_cnt}건 발송 완료"}, status=200)

# ─────────────────────────────────────────────────────────
# MAIL 
# ─────────────────────────────────────────────────────────
@require_GET
def mngMsg_mail_data(request):
    ADID = (request.GET.get("ADID") or "").strip()
    # '전체' 선택 시 ADID가 빈 값으로 넘어오는 경우가 있어 세션값으로 보정
    if not ADID:
        ADID = (request.session.get("ADID") or "").strip()
    request.session["ADID"] = ADID

    adminflag = (request.GET.get("adminflag") or "").strip().lower()
    if adminflag == "get_admin_info":
        admin_id = (request.GET.get("admin_id") or "").strip()
        if not admin_id or admin_id == "전체":
            return JsonResponse({"ok": True, "admin_name": "", "admin_tel_no": ""})

        contact = (
            MemAdmin.objects.filter(admin_id=ADID)
            .values("admin_name", "admin_tel_no")
            .first()
        )
        print(f"[관리자] ADID={ADID} mailFlag={adminflag} ")
        return JsonResponse({
            "ok": True,
            "admin_name": (contact.get("admin_name") if contact else "") or "",
            "admin_tel_no": (contact.get("admin_tel_no") if contact else "") or "",
        })
        
    mailFlag = (request.GET.get("mailFlag") or "").strip().lower()
    print(f"[mngMsg_mail_data] ADID={ADID} mailFlag={mailFlag}")

    # 공통 조건
    where_parts = [
        "a.Del_YN <> 'Y'",
        "b.keeping_YN = 'Y'",
        "a.duzon_ID <> ''",
        # "ISNULL(a.email,'') <> ''",  # 이메일 없는 업체도 보이게 하려면 주석 유지
    ]
    params = []

    # 템플릿(=mailFlag)별 추가 조건
    template_where_map = {
        "pay": "(b.goyoung_jungkyu = 'Y' OR b.goyoung_sayoup = 'Y' OR b.goyoung_ilyoung = 'Y')",
        "yearend": "",
        "younmal": "(b.goyoung_jungkyu = 'Y')",
        "ilyoung": "(b.goyoung_ilyoung = 'Y')",
        "vat": "(a.Biz_Type IN ('1','4'))",
        "nonvat": "(a.Biz_Type IN ('2','6'))",
        "corptax": "(a.Biz_Type BETWEEN '1' AND '3')",
        "incometax": "(a.Biz_Type BETWEEN '4' AND '7')",
    }
    extra_where = template_where_map.get(mailFlag)
    if extra_where:
        where_parts.append(extra_where)

    # 담당자(ADID) 필터
    if ADID and ADID != "전체":
        where_parts.append("b.biz_manager = %s")
        params.append(ADID)
    where_sql = " AND ".join(where_parts)

    # 상태표시용: 해당 템플릿(mailFlag)을 mail_class로 보고 마지막 발송일을 가져온다.
    maillog_where = ["year(d.mail_date) = year(getdate())"]
    maillog_params = []
    if mailFlag:
        maillog_where.append("d.mail_class = %s")
        maillog_params.append(mailFlag)
    maillog_where_sql = " AND ".join(maillog_where)

    sql_page = f"""
        SELECT
            b.biz_manager as groupManager,
            c.admin_name,
            c.admin_tel_no,
            a.seq_no,
            a.biz_name,
            ISNULL(a.email,'') AS email,
            ISNULL(CONVERT(varchar(16), d.mail_date, 120), '') AS mail_date
        FROM mem_user a
        JOIN mem_deal b ON a.seq_no = b.seq_no
        left join mem_admin c on b.biz_manager=c.admin_id
        LEFT JOIN (
            SELECT d.seq_no, MAX(d.mail_date) as mail_date
            FROM Tbl_MAIL d
            WHERE {maillog_where_sql}
            GROUP BY d.seq_no
        ) d ON a.seq_no = d.seq_no
        WHERE {where_sql}
        order by a.biz_name
    """

    with connection.cursor() as cur:
        cur.execute(sql_page, maillog_params + params)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return JsonResponse({"ok": True, "rows": rows, "total": len(rows)})

@require_GET
def mngMsg_mail_view(request):
    seq_no = request.GET.get("seq_no")
    mail_class = (request.GET.get("mail_class") or "mail").strip()
    print(f"[mngMsg_mail_view] seq_no={seq_no} mail_class={mail_class}")
    if not seq_no:
        raise Http404("seq_no required")

    sql = """
        SELECT TOP 1
            seq_no, mail_class,
            ISNULL(mail_subject,'') AS mail_subject,
            ISNULL(mail_content,'') AS mail_content,
            ISNULL(mail_send_result,'') AS mail_send_result,
            ISNULL(CONVERT(varchar(19), mail_date, 120), '') AS mail_date
        FROM Tbl_MAIL
        WHERE seq_no = %s AND mail_class = %s
        ORDER BY mail_date DESC
    """
    with connection.cursor() as cur:
        cur.execute(sql, [seq_no, mail_class])
        row = cur.fetchone()
        if not row:
            raise Http404("not found")
        cols = [c[0] for c in cur.description]
        data = dict(zip(cols, row))

    return render(request, "admin/mng_MsgMail_view.html", {"row": data})


# views.py



def get_mail_targets(request):
    """
    Flag에 따라 발송 대상자 리스트를 JSON으로 반환
    """
    flag = request.GET.get('flag', 'pay') # 기본값 pay
    search_text = request.GET.get('q', '')

    print(f"[get_mail_targets] start flag={flag} q={search_text}")

    # 1. 공통 조건 (예: 삭제되지 않고 기장 서비스 이용 중인 업체)
    # select_related는 memdeal 테이블과 조인하기 위해 사용
    queryset = MemUser.objects.select_related('memdeal').filter(
        del_yn='N', 
        memdeal__keeping_yn='Y'
    )

    # 2. 주제(Flag)별 동적 필터링 조건
    if flag == 'pay':
        # 급여신고: 고용 정규직이 'Y' 이거나 ...
        queryset = queryset.filter(memdeal__goyoung_jungkyu='Y')
    elif flag == 'ilyoung':
        # 일용직
        queryset = queryset.filter(memdeal__goyoung_ilyoung='Y')
    elif flag == 'vat':
        # 부가세: 과세/면세 등 조건 추가
        # 예: queryset = queryset.filter(biz_type__in=['1', '4']) 
        pass 
    elif flag == 'yearend':
        # 연말정산
        pass
    
    # 3. 검색어 필터링 (선택사항)
    if search_text:
        queryset = queryset.filter(biz_name__icontains=search_text)

    # 4. JSON 변환
    data = []
    for user in queryset:
        data.append({
            'seq_no': user.seq_no,
            'biz_name': user.biz_name,
            'email': user.email,
            'hp_no': user.hp_no,
            # 필요한 필드 추가
        })

    print(f"[get_mail_targets] rows={len(data)}")
    return JsonResponse({'rows': data, 'total': len(data)})

@require_POST
def mngMsg_mail_upload(request):
    """
    첨부파일을 임시 업로드하고 저장된 파일명을 반환
    { ok: true, uploaded_name: "xxx.pdf" }
    """
    uploaded_file = request.FILES.get("file") or request.FILES.get("uploadFile")
    if not uploaded_file:
        return JsonResponse({"ok": False, "msg": "file is required"})

    upload_root = Path(getattr(settings, "MEDIA_ROOT", Path("."))) / "mail_uploads"
    upload_root.mkdir(parents=True, exist_ok=True)

    try:
        storage = FileSystemStorage(location=str(upload_root))
        saved_name = storage.save(uploaded_file.name, uploaded_file)
    except Exception as e:
        return JsonResponse({"ok": False, "msg": str(e)}, status=500)

    return JsonResponse({"ok": True, "uploaded_name": saved_name})


@require_POST
def mngMsg_mail_send(request):
    """
    {seq_no, email, biz_name, title, content, fileCount, uploaded_name, mail_class}
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"ok": False, "msg": "invalid json"})

    seq_no = payload.get("seq_no")
    raw_email = (payload.get("email") or "").strip()
    title = payload.get("title") or ""
    content = payload.get("content") or ""
    uploaded_name = payload.get("uploaded_name") or ""
    print(f"[mngMsg_mail_send] seq_no={seq_no} email_raw='{raw_email}' title_len={len(title)} content_len={len(content)} uploaded_name={uploaded_name}")

    if not seq_no or not raw_email or not title:
        return JsonResponse({"ok": False, "msg": "seq_no/email/title required"})

    from django.core.mail import EmailMultiAlternatives
    from django.utils.html import strip_tags
    from django.utils import timezone

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    if not from_email:
        return JsonResponse({"ok": False, "msg": "메일 발신 계정이 설정되지 않았습니다."}, status=500)

    # 여러 이메일을 ; 또는 , 로 구분한 경우 지원
    def parse_emails(addr_str):
        parts = re.split(r"[;,]", addr_str)
        addrs = []
        for p in parts:
            p = p.strip()
            if not p:
                continue
            try:
                validate_email(p)
                addrs.append(p)
            except ValidationError:
                return None, p
        return addrs, None

    to_emails, invalid = parse_emails(raw_email)
    if invalid or not to_emails:
        return JsonResponse({"ok": False, "msg": f"잘못된 이메일 주소: {invalid or raw_email}"}, status=400)

    attachment_path = None
    if uploaded_name:
        safe_name = Path(str(uploaded_name)).name
        candidate = Path(getattr(settings, "MEDIA_ROOT", Path("."))) / "mail_uploads" / safe_name
        if candidate.exists() and candidate.is_file():
            attachment_path = candidate
        else:
            return JsonResponse({"ok": False, "msg": "첨부파일을 찾을 수 없습니다. 다시 업로드해주세요."}, status=400)

    try:
        msg = EmailMultiAlternatives(
            subject=title,
            body=strip_tags(content),
            from_email=from_email,
            to=to_emails,
        )
        msg.attach_alternative(content, "text/html")
        if attachment_path:
            # 한메일(Daum) 등 일부 클라이언트에서 첨부파일 누락 방지를 위해 MIME 타입 명시 및 직접 첨부
            ctype, _ = mimetypes.guess_type(attachment_path)
            if ctype is None:
                ctype = 'application/octet-stream'
            with open(attachment_path, 'rb') as f:
                msg.attach(attachment_path.name, f.read(), ctype)
        msg.send()
        sent_at = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        return JsonResponse({"ok": True, "sent_at": sent_at})
    except Exception as e:
        # SMTP 오류 등을 프론트에서 처리할 수 있도록 200으로 내려준다.
        print(f"[mngMsg_mail_send][error] {e}")
        return JsonResponse({"ok": False, "msg": str(e)}, status=200)
