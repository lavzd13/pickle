from django.core.management.base import BaseCommand
from accounts.models import PlayInfo


class Command(BaseCommand):
    help = 'Delete PlayInfo for all accounts (or a specific one)'

    def add_arguments(self, parser):
        parser.add_argument('--nick', type=str, help='Delete only for account with this nick')

    def handle(self, *args, **options):
        nick = options.get('nick')
        if nick:
            deleted, _ = PlayInfo.objects.filter(account__nick=nick).delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted PlayInfo for nick: {nick} ({deleted} row(s))'))
        else:
            deleted, _ = PlayInfo.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted all PlayInfo records ({deleted} row(s))'))
