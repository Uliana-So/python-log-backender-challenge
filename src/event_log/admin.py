from django.contrib import admin

from event_log.models import EventLogRecord


@admin.register(EventLogRecord)
class EventLogRecordAdmin(admin.ModelAdmin):
    pass
