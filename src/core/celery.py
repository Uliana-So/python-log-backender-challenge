from celery import Celery
from celery.schedules import crontab
import os
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery(
    'core',
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_RESULT_BACKEND
)
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_connection_retry_on_startup = True
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "process_event_log_record": {
        "task": "event_log.tasks.process_event_log_record",
        "schedule": crontab(minute="*/10"),
    },
}


if __name__ == "__main__":
    app.start()
