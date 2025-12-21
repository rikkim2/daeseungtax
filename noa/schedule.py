from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job


scheduler = BackgroundScheduler()


def update_data():
    # 데이터 업데이트 작업 수행
    pass


# 스케줄링 작업 등록
scheduler.add_job(update_data, 'interval', hours=1)


# 스케줄링 작업 실행
scheduler.start()