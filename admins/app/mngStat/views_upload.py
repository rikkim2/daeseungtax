# apps/mngStat/views_upload.py
import os, uuid, time, threading
from django.http import JsonResponse, HttpRequest
from django.conf import settings
from django.views.decorators.http import require_POST
from django.db import connection, transaction
from .progress import set_progress, get_progress, fail_progress

def _safe_int(x, d=0):
    try: return int(x)
    except: return d

def _process_upload_job(job_id: str, tmp_path: str, seq_no: int, work_yy: int):
    try:
        # 0. 시작
        set_progress(job_id, 1, "업로드 파일 수신 완료")

        # 1. 엑셀 파싱 (예: openpyxl)
        set_progress(job_id, 10, "엑셀 파싱 중...")
        time.sleep(0.2)  # 데모용
        # rows = parse_excel(tmp_path)  # 구현부 연결

        # 2. 연도 검증
        set_progress(job_id, 25, "연도 검증 중...")
        time.sleep(0.2)
        # if not validate_year(rows, work_yy): raise ValueError("작업연도와 엑셀 연도가 다릅니다.")

        # 3. DB 저장 (트랜잭션)
        set_progress(job_id, 55, "DB 저장 중...")
        with transaction.atomic():
            with connection.cursor() as cur:
                # 예시) 기존 데이터 정리/벌크 인서트
                # cur.execute("DELETE FROM DS_SlipLedgr2 WHERE seq_no=%s AND work_yy=%s", [seq_no, work_yy])
                # bulk_insert_rows(cur, rows)
                time.sleep(0.4)  # 데모용

        # 4. 후처리 프로시저
        set_progress(job_id, 80, "후처리(프로시저) 실행 중...")
        with connection.cursor() as cur:
            # 예시: cur.execute("EXEC up_Rebuild_Summary %s, %s", [seq_no, work_yy])
            time.sleep(0.4)  # 데모용

        # 5. 캐시/요약 계산
        set_progress(job_id, 95, "요약 계산/캐시 반영...")
        time.sleep(0.2)

        # 완료
        set_progress(job_id, 100, "완료")
    except Exception as e:
        fail_progress(job_id, f"오류: {e}")

@require_POST
def upload_slip_ledger_excel(request: HttpRequest):
    """
    프런트에서 FormData에 job_id를 함께 보냄.
    이 뷰는 파일을 temp에 저장하고, 백그라운드 스레드에서 _process_upload_job 실행.
    즉시 {ok, job_id} 반환.
    """
    job_id = request.POST.get("job_id") or uuid.uuid4().hex
    seq_no = _safe_int(request.POST.get("seq_no"))
    work_yy = _safe_int(request.POST.get("work_yy"))

    f = request.FILES.get("uploadFile")
    if not f:
        return JsonResponse({"ok": False, "msg": "파일이 없습니다."}, status=400)

    # temp 저장
    base = getattr(settings, "MEDIA_ROOT", settings.BASE_DIR)
    tmp_dir = os.path.join(base, "tmp_uploads")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_path = os.path.join(tmp_dir, f"{job_id}_{f.name}")
    with open(tmp_path, "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)

    # 초기 진행률 세팅
    set_progress(job_id, 0, "대기 중...")

    # 백그라운드 처리 시작
    t = threading.Thread(target=_process_upload_job, args=(job_id, tmp_path, seq_no, work_yy), daemon=True)
    t.start()

    return JsonResponse({"ok": True, "job_id": job_id})

def get_upload_progress(request: HttpRequest):
    job_id = (request.GET.get("job_id") or "").strip()
    if not job_id:
        return JsonResponse({"pct": 0, "msg": "job_id 없음"}, status=400)
    return JsonResponse(get_progress(job_id))
