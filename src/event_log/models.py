from django.db import models


class EventLogRecord(models.Model):
    event_data = models.JSONField()

    class Meta:
        verbose_name = 'EventLogRecord'
        verbose_name_plural = 'EventLogRecords'

    def __str__(self) -> str:
        return f'{self.event_data}'
