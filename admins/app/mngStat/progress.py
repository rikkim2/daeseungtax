# apps/mngStat/progress.py
from django.core.cache import cache

KEY_PREFIX = "upload:progress:"

def set_progress(job_id: str, pct: int, msg: str = ""):
    cache.set(KEY_PREFIX + job_id, {"pct": int(pct), "msg": msg}, timeout=60*30)

def get_progress(job_id: str):
    return cache.get(KEY_PREFIX + job_id) or {"pct": 0, "msg": "대기 중..."}

def fail_progress(job_id: str, msg: str):
    cache.set(KEY_PREFIX + job_id, {"pct": -1, "msg": msg}, timeout=60*30)
