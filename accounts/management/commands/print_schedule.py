from django.core.management.base import BaseCommand
from accounts.models import AccountDetail, PlayInfo
import json


class Command(BaseCommand):
    help = 'Print out current account schedule'

    def handle(self, *args, **options):
        accounts = AccountDetail.objects.all()
        play_info = PlayInfo.objects.all()
        total = accounts.count()
        for account in accounts:
            try:
                schedule = account.play_info.schedule_of_the_week
                formatted = json.dumps(schedule, indent=2)
            except:
                schedule = 'No play info'
            self.stdout.write(f'\n{account.nick}:\n{formatted}')
