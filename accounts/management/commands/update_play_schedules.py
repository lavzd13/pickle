from django.core.management.base import BaseCommand
from accounts.models import AccountDetail
from accounts.web_views import calculate_play_info


class Command(BaseCommand):
    help = 'Regenerate weekly play schedule for all accounts'

    def handle(self, *args, **options):
        accounts = AccountDetail.objects.filter(is_active=True)
        total = accounts.count()
        for account in accounts:
            calculate_play_info(account)
            self.stdout.write(f'Updated: {account.nick}')
        self.stdout.write(self.style.SUCCESS(f'Done. Updated {total} accounts.'))
