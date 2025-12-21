import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import register_events, DjangoJobStore
from apscheduler.triggers.cron import CronTrigger


logger = logging.getLogger(__name__)

def job_function():
    print("테스트1")
sched = BlockingScheduler()


def my_job_a():
  # 실행시킬 Job
  # 여기서 정의하지 않고, import 해도 됨
  pass
  
def my_job_b():
  # 실행시킬 Job
  # 여기서 정의하지 않고, import 해도 됨
  pass

def start():
  def handle(self, *args, **options):
    scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE) # BlockingScheduler를 사용할 수도 있습니다.
    scheduler.add_jobstore(DjangoJobStore(), "default") 

    scheduler.add_job(
      my_job_a,
      trigger=CronTrigger(second="*/60"),  # 60초마다 작동합니다.
      id="my_job",  # id는 고유해야합니다. 
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'my_job_a'.")

    scheduler.add_job(
      my_job_b,
      trigger=CronTrigger(
        day_of_week="mon", hour="06", minute="00"
      ),  # 실행 시간입니다. 여기선 매주 월요일 3시에 실행합니다.
      id="my_job_b",
      max_instances=1,
      replace_existing=True,
    )
    logger.info("Added job 'my_job_b'.")

    try:
      logger.info("Starting scheduler...")
      scheduler.start() # 없으면 동작하지 않습니다.
    except KeyboardInterrupt:
      logger.info("Stopping scheduler...")
      scheduler.shutdown()
      logger.info("Scheduler shut down successfully!")