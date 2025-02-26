from datetime import datetime

from celery import Task, shared_task
from django.conf import settings
from django.db import transaction

from core.event_log_client import EventLogClient

from .models import EventLogRecord


@shared_task(bind=True)
def process_event_log_record(self: Task) -> None:
    events_to_process = list(EventLogRecord.objects.all()[:settings.BATCH_SIZE])

    if not events_to_process:
        return

    events_data = []
    for event in events_to_process:
        event.event_data[1] = datetime.fromisoformat(event.event_data[1])
        events_data.append(event.event_data)

    try:
        with EventLogClient.init() as client:
            client.insert(
                data=events_data,
            )

        with transaction.atomic():
            EventLogRecord.objects.filter(id__in=[event.id for event in events_to_process]).delete()

    except Exception as e:
        raise self.retry(exc=e, countdown=5) from e

