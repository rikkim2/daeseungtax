# income_manage는 초기 화면만 렌더
# 연도/담당자/검색 변경 시 api_income_list로 store reload
# 셀 수정/체크 변경 시 api_income_update로 저장(Upsert)

import json
import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db import connection
from django.db.models import Q

from app.models import MemAdmin  


def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


def _get_income_work_year_from_asp_rule(today: datetime.date, work_mm: int | None):
    """
    ASP 규칙 기반 대략:
    - input_workyear 없으면 work_month<=11 이면 올해-1, 아니면 올해
    """
    mm = work_mm or today.month
    if mm <= 11:
        return today.year - 1
    return today.year


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


def _fetch_income_rows(work_yy: int, adid: str, search_text: str, is_sa: bool):
    """
    ✅ ASP 핵심 SQL을 Django/SQLServer에서 재구성 (현실적으로 100% 동일하긴 어려워서)
    - mem_user/mem_deal 기본 조건
    - tbl_income2 (당해) + tbl_income2 (전년)
    - 종합소득세전자신고2, elec_income 일부 연결
    - MailGrade/isIssue/is1pdf는 “최소 기능” 형태로 구성 (필요하면 추가 확장 가능)
    """
    params = [work_yy, work_yy - 1, work_yy]

    admin_where = ""
    if adid and adid != "전체":
        admin_where = " AND b.biz_manager = %s "
        params.append(adid)

    search_where = ""
    if search_text:
        # 상호/사업자번호/대표자명 검색(원하면 확장)
        search_where = """
          AND (
              a.biz_name LIKE %s
              OR REPLACE(a.biz_no,'-','') LIKE %s
              OR a.ceo_name LIKE %s
          )
        """
        like = f"%{search_text}%"
        params += [like, like.replace("-", ""), like]

    sql = f"""
    SELECT
        a.seq_no                                       AS seq_no,
        REPLACE(a.biz_no,'-','')                       AS biz_no,
        a.biz_name                                     AS biz_name,
        a.ceo_name                                     AS ceo_name,
        ISNULL(b.hometaxAgree,'')                      AS hometaxAgree,

        -- 당해 tbl_income2
        ISNULL(d.YN_1, 0)                              AS YN_1,
        -- ASP의 kb(경비율 비슷하게 쓰던 값): (1 - yn_3/yn_1)
        CASE WHEN ISNULL(d.YN_1,0)=0 THEN 0
             ELSE (1 - (CAST(ISNULL(d.YN_3,0) AS float) / NULLIF(CAST(d.YN_1 AS float),0)))
        END                                            AS YN_2,
        ISNULL(d.YN_3, 0)                              AS YN_3,
        ISNULL(d.YN_4, 0)                              AS YN_4,
        ISNULL(d.YN_5, 0)                              AS YN_5,

        -- 파일/메일/전자신고는 최소표현(필요시 확장)
        ''                                             AS is1pdf,
        ''                                             AS MailGrade,
        CASE WHEN e.과세년월 IS NULL THEN '' ELSE 'Y' END AS isIssue,

        -- 결재/수금/수수료 등
        ISNULL(d.YN_6, 0)                              AS YN_6,
        ISNULL(d.YN_8, 0)                              AS YN_8,
        ISNULL(d.YN_7, 0)                              AS YN_7,

        ISNULL(d.YN_10, NULL)                          AS YN_10,
        ISNULL(d.YN_11, 0)                             AS YN_11,
        ISNULL(d.YN_12, NULL)                          AS YN_12,
        ISNULL(d.YN_13, 0)                             AS YN_13,
        ISNULL(d.YN_14, 0)                             AS YN_14,
        ISNULL(d.YN_15, 0)                             AS YN_15,
        ISNULL(d.YN_9, '')                             AS YN_9,

        ISNULL(a.user_id,'')                           AS userID,

        -- 전년(bf_*)
        ISNULL(p.YN_1, 0)                              AS bf_sale,
        ISNULL(p.YN_3, 0)                              AS bf_cost,
        0                                              AS bf_reve,
        ISNULL(p.YN_8, 0)                              AS bf_fee,

        ISNULL(b.biz_manager,'')                       AS admin_id
    FROM mem_user a
    JOIN mem_deal b ON a.seq_no=b.seq_no
    LEFT JOIN tbl_income2 d
           ON a.seq_no=d.seq_no AND d.work_yy=%s
    LEFT JOIN tbl_income2 p
           ON a.seq_no=p.seq_no AND p.work_yy=%s
    LEFT JOIN 종합소득세전자신고2 e
           ON a.Ceo_Name = e.이름
          AND LEFT(a.ssn,6)=LEFT(e.주민번호,6)
          AND LEFT(RTRIM(e.과세년월),4) = CONVERT(varchar(4), %s)
    WHERE a.duzon_ID <> ''
      AND a.biz_type IN ('4','5','6','7')
      AND b.keeping_YN='Y'
      AND a.Del_YN<>'Y'
      {admin_where}
      {search_where}
    ORDER BY a.biz_name
    """

    rows = []
    with connection.cursor() as cur:
        cur.execute(sql, params)
        cols = [c[0] for c in cur.description]
        for r in cur.fetchall():
            item = dict(zip(cols, r))

            # bool/int normalize
            def _b(v):
                return True if str(v) in ("1", "True", "true", "Y", "y") else False

            item["hometaxAgree"] = _b(item.get("hometaxAgree"))
            for k in ["YN_6","YN_7","YN_11","YN_13","YN_14","YN_15"]:
                item[k] = _b(item.get(k))

            for k in ["YN_1","YN_3","YN_4","YN_5","YN_8","bf_sale","bf_cost","bf_reve","bf_fee"]:
                item[k] = _safe_int(item.get(k), 0)

            # 날짜는 문자열로 내려주기(Ext.dateFormat 쉽게)
            for k in ["YN_10","YN_12"]:
                v = item.get(k)
                if hasattr(v, "strftime"):
                    item[k] = v.strftime("%Y-%m-%d")
                elif not v:
                    item[k] = ""

            # isIssue 표기(아이콘은 프론트 renderer에서 처리)
            item["isIssue"] = True if item.get("isIssue") == "Y" else False

            rows.append(item)

    # before/after fee (기존 로직 유지)
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT ISNULL(SUM(d.YN_8),0)
            FROM mem_user a
            JOIN mem_deal b ON a.seq_no=b.seq_no
            JOIN tbl_income2 d ON b.seq_no=d.seq_no
            WHERE a.duzon_id <> ''
              AND b.keeping_YN='Y'
              AND d.work_yy=%s
            """,
            [work_yy],
        )
        beforefee = _safe_int(cur.fetchone()[0], 0)

        cur.execute(
            """
            SELECT ISNULL(SUM(d.YN_8),0)
            FROM mem_user a
            JOIN mem_deal b ON a.seq_no=b.seq_no
            JOIN tbl_income2 d ON b.seq_no=d.seq_no
            WHERE a.duzon_id <> ''
              AND b.keeping_YN='Y'
              AND d.yn_7='1'
              AND d.work_yy=%s
            """,
            [work_yy],
        )
        afterfee = _safe_int(cur.fetchone()[0], 0)

    return rows, beforefee, afterfee


def _upsert_income_field(seq_no: int, work_yy: int, field: str, value):
    """
    ✅ tbl_income2 Upsert
    - 허용 필드만 업데이트(화이트리스트)
    """
    allowed = {
        "YN_1","YN_3","YN_4","YN_5",
        "YN_6","YN_7","YN_8",
        "YN_9",
        "YN_10","YN_11","YN_12","YN_13","YN_14","YN_15",
    }
    if field not in allowed:
        raise ValueError("허용되지 않은 필드")

    with connection.cursor() as cur:
        # row exists?
        cur.execute(
            "SELECT COUNT(*) FROM tbl_income2 WHERE seq_no=%s AND work_yy=%s",
            [seq_no, work_yy],
        )
        exists = (cur.fetchone()[0] or 0) > 0

        if not exists:
            # 최소 insert
            cur.execute(
                """
                INSERT INTO tbl_income2 (seq_no, work_yy)
                VALUES (%s, %s)
                """,
                [seq_no, work_yy],
            )

        # update
        cur.execute(
            f"UPDATE tbl_income2 SET {field}=%s WHERE seq_no=%s AND work_yy=%s",
            [value, seq_no, work_yy],
        )


@login_required
def income_manage(request):
    # ✅ 로그인은 되어있는데 세션키가 비어있어도 죽지 않게 “안전 기본값” 처리
    admin_grade, admin_biz_level, admin_biz_area, arr_adid = _get_admin_list(request)

    ADID = (request.session.get("ADID") or request.user.username or "").strip()
    if not ADID:
        ADID = arr_adid[0] if arr_adid else ""

    today = datetime.date.today()
    work_mm = _safe_int(request.GET.get("work_MM") or request.session.get("workmonth") or today.month, today.month)
    work_yy = request.GET.get("work_YY") or request.session.get("workyearIncome")
    if not work_yy:
        work_yy = _get_income_work_year_from_asp_rule(today, work_mm)
    work_yy = _safe_int(work_yy, today.year)

    request.session["workyearIncome"] = work_yy
    request.session["workmonth"] = work_mm

    income_year_base = _get_income_work_year_from_asp_rule(today, work_mm)
    year_options = list(range(income_year_base, income_year_base - 6, -1))

    context = {
        "admin_grade": admin_grade,
        "admin_biz_level": admin_biz_level,
        "ADID": ADID,
        "arr_ADID": json.dumps(arr_adid, ensure_ascii=False),
        "year_options": json.dumps(year_options),
        "work_YY": work_yy,
    }
    return render(request, "admin/mng_income.html", context)


@require_GET
@login_required
def api_income_list(request):
    admin_grade = (request.session.get("Admin_Grade") or "").strip()
    is_sa = admin_grade == "SA"

    work_yy = _safe_int(request.GET.get("work_YY") or request.GET.get("input_workyear"), datetime.date.today().year)
    adid = (request.GET.get("ADID") or request.session.get("ADID") or "").strip()
    if adid == "":  # “전체” 의미
        adid = "전체"
    search_text = (request.GET.get("search_text") or "").strip()

    rows, beforefee, afterfee = _fetch_income_rows(work_yy, adid, search_text, is_sa)

    return JsonResponse({
        "ok": True,
        "work_YY": work_yy,
        "rows": rows,
        "beforefee": beforefee,
        "afterfee": afterfee,
    })


@require_POST
@login_required
def api_income_update(request):
    """
    ✅ ExtJS CellEditing / CheckColumn 변경 저장
    payload 예:
      { "seq_no": 123, "work_YY": 2025, "field": "YN_8", "val": 500000 }
      { "seq_no": 123, "work_YY": 2025, "field": "hometaxAgree", "val": true }
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST

    seq_no = _safe_int(payload.get("seq_no"), 0)
    work_yy = _safe_int(payload.get("work_YY") or payload.get("workyear"), 0)
    field = (payload.get("field") or "").strip()
    val = payload.get("val")

    if not seq_no or not work_yy or not field:
        return JsonResponse({"ok": False, "msg": "필수값 누락"}, status=400)

    # bool normalize
    if isinstance(val, str) and val.lower() in ("true","false"):
        val = True if val.lower() == "true" else False

    # hometaxAgree는 mem_user에 저장한다고 가정(기존 ASP도 별도 ajax였음)
    if field == "hometaxAgree":
        with connection.cursor() as cur:
            cur.execute("UPDATE mem_user SET hometaxAgree=%s WHERE seq_no=%s", [("Y" if val else "N"), seq_no])
        return JsonResponse({"ok": True})

    # 날짜 필드 처리(문자열이면 그대로 저장)
    if field in ("YN_10","YN_12"):
        # 빈 값이면 NULL
        if not val:
            val_db = None
        else:
            val_db = str(val)[:10]
        try:
            _upsert_income_field(seq_no, work_yy, field, val_db)
        except Exception as e:
            return JsonResponse({"ok": False, "msg": str(e)}, status=400)
        return JsonResponse({"ok": True})

    # 체크/숫자/문자
    if field in ("YN_6","YN_7","YN_11","YN_13","YN_14","YN_15"):
        val_db = 1 if bool(val) else 0
    elif field in ("YN_1","YN_3","YN_4","YN_5","YN_8"):
        val_db = _safe_int(val, 0)
    else:
        val_db = val if val is not None else ""

    try:
        _upsert_income_field(seq_no, work_yy, field, val_db)
        return JsonResponse({"ok": True})
    except Exception as e:
        return JsonResponse({"ok": False, "msg": str(e)}, status=400)
