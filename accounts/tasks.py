import traceback
from celery import shared_task
from django.core.management import call_command
from io import StringIO


@shared_task
def run_update_play_schedules():
    from .models import TaskLog
    out = StringIO()
    try:
        call_command('update_play_schedules', stdout=out)
        TaskLog.objects.create(
            task_name='update_play_schedules',
            success=True,
            detail=out.getvalue(),
        )
    except Exception:
        TaskLog.objects.create(
            task_name='update_play_schedules',
            success=False,
            detail=traceback.format_exc(),
        )
        raise
