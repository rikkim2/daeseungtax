import json
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

@require_GET
def mngMsg(request):
  admin_grade, admin_biz_level, admin_biz_area, arr_adid = _get_admin_list(request)

  ADID = (request.session.get("ADID") or request.user.username or "").strip()
  if not ADID:
      ADID = arr_adid[0] if arr_adid else ""

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

    where_sql = " AND ".join(where_parts)

    sql = f"""
        SELECT
            a.ceo_name,
            a.biz_name,
            a.hp_no,
            a.seq_no,
            a.biz_no,
            '' AS sms_send_dt_rsv,
            ISNULL(CONVERT(varchar(16), d.sms_send_dt, 120), '')     AS sms_send_dt,
            ISNULL(d.sms_send_result, '')                             AS sms_send_result
        FROM mem_user a
        JOIN mem_deal b ON a.seq_no = b.seq_no
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

    if not msg:
        return JsonResponse({"ok": False, "msg": "내용을 입력하세요."}, status=400)
    if not seqs or not hps or len(seqs) != len(hps):
        return JsonResponse({"ok": False, "msg": "대상을 선택하세요."}, status=400)

    now = timezone.now()

    # TODO: 예약이면 예약시간 조립해서 sms_send_dt_rsv에 넣고,
    # 실제 발송은 스케줄러/큐로 넘기는 구조가 베스트
    # 여기서는 단순 저장 예시
    with connection.cursor() as cur:
        for seq_no, hp in zip(seqs, hps):
            cur.execute("""
                INSERT INTO Tbl_SMS (seq_no, sms_class, sms_send_dt, sms_send_dt_rsv, sms_send_result, sms_contents)
                VALUES (%s, %s, %s, NULL, %s, %s)
            """, [seq_no, sms_class, now, "OK", msg])

    return JsonResponse({"ok": True, "msg": "전송 처리 완료"})

# ─────────────────────────────────────────────────────────
# MAIL 
# ─────────────────────────────────────────────────────────
@require_GET
def mngMsg_mail_data(request):
    ADID = request.GET.get('ADID')
    if not ADID:ADID = request.session.get('ADID')#전체 선택시 ADID=""상태가 된다
    request.session['ADID'] = ADID  

    mailFlag = (request.GET.get("mailFlag") or "").strip()
    print(f"[mngMsg_mail_data] mailFlag={mailFlag}")

    # 검색조건(회사명/이메일)
    where_parts = [
        "a.Del_YN <> 'Y'",
        "b.keeping_YN = 'Y'",
        "a.duzon_ID <> ''",
        #"ISNULL(a.email,'') <> ''",# 이메일 없는 업체
    ]
    where_sql = " AND ".join(where_parts)
    flag_sql=""
    if mailFlag:
      flag_sql = f" mail_subject LIKE '%{mailFlag}%' "
   
    s_sql = ""
    if ADID!="전체":
      s_sql = f" AND b.biz_manager = '{ADID}'"
    sql_page = f"""
        SELECT
            b.biz_manager as groupManager,
            a.seq_no,
            a.biz_name,
            ISNULL(a.email,'') AS email,
            ISNULL(CONVERT(varchar(16), d.mail_date, 120), '') AS mail_date
        FROM mem_user a
        JOIN mem_deal b ON a.seq_no = b.seq_no
        LEFT JOIN (
            SELECT seq_no, MAX(mail_date) as mail_date
            FROM Tbl_MAIL d
            WHERE year(mail_date) = year(getdate())
            {flag_sql}
            GROUP BY d.seq_no
        ) d ON a.seq_no = d.seq_no        
        WHERE {where_sql}  {s_sql}
        order by a.biz_name
    """
    print(sql_page)
    with connection.cursor() as cur:
        cur.execute(sql_page)

        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    return JsonResponse({"rows": rows})


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
    f = request.FILES.get("file")
    if not f:
        return JsonResponse({"ok": False, "msg": "file is required"})

    # TODO: 저장 경로/보안 정책(확장자 제한, 용량 제한 등)
    # saved_name = ...
    saved_name = f.name

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
    email = payload.get("email")
    title = payload.get("title") or ""
    content = payload.get("content") or ""
    print(f"[mngMsg_mail_send] seq_no={seq_no} email={email} title_len={len(title)} content_len={len(content)}")

    if not seq_no or not email or not title:
        return JsonResponse({"ok": False, "msg": "seq_no/email/title required"})

    # TODO:
    # 1) 메일 발송(사내 SMTP or 외부 API)
    # 2) 발송 로그 저장(테이블: Tbl_Mail / Log_Mail 등)
    # 3) uploaded_name 첨부 처리(저장경로에서 attach)
    # 4) 성공 시 sent_at 내려주기

    sent_at = None  # "2025-12-19 12:34"

    return JsonResponse({"ok": True, "sent_at": sent_at})
