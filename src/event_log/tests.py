from collections.abc import Generator
from datetime import datetime

import pytest
from clickhouse_connect.driver import Client
from django.conf import settings
from django.utils import timezone

from users.use_cases import UserCreated

from .models import EventLogRecord
from .tasks import process_event_log_record

pytestmark = [pytest.mark.django_db]


@pytest.fixture(autouse=True)
def f_clean_up_event_log(f_ch_client: Client) -> Generator:
    f_ch_client.query(f'TRUNCATE TABLE {settings.CLICKHOUSE_EVENT_LOG_TABLE_NAME}')
    yield


def test_send_log_to_clickhouse(f_ch_client: Generator) -> None:
    event_type = 'user_created'
    event_date_time = timezone.now().isoformat()
    event_env = 'Local'
    event_context = UserCreated(
        email='test@ya.com',
        first_name='Test',
        last_name='Testovich',
    ).model_dump_json()

    EventLogRecord.objects.create(
        event_data=(
            event_type,
            event_date_time,
            event_env,
            event_context,
        ),
    )

    process_event_log_record()

    log_ch = f_ch_client.query("SELECT * FROM default.event_log WHERE event_type = 'user_created'")
    assert log_ch.result_rows == [
        (
            event_type,
            datetime.fromisoformat(event_date_time).replace(tzinfo=None),
            event_env,
            event_context,
            1,
        ),
    ]


def test_process_event_log_record_delete() -> None:
    event_type = 'user_created'
    event_date_time = timezone.now().isoformat()
    event_env = 'Local'
    event_context = UserCreated(
        email='test@ya.com',
        first_name='Test',
        last_name='Testovich',
    ).model_dump_json()

    EventLogRecord.objects.create(
        event_data=(
            event_type,
            event_date_time,
            event_env,
            event_context,
        ),
    )

    assert EventLogRecord.objects.count() == 1

    process_event_log_record()

    assert EventLogRecord.objects.count() == 0
