from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from accounts.models import UserProfile


class Command(BaseCommand):
    help = 'Create a system admin superuser with full user management permissions'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True)
        parser.add_argument('--password', required=True)
        parser.add_argument('--email', default='')

    def handle(self, *args, **options):
        username = options['username']

        if User.objects.filter(username=username).exists():
            self.stderr.write(f'User "{username}" already exists.')
            return

        user = User.objects.create_superuser(
            username=username,
            password=options['password'],
            email=options['email'],
        )
        UserProfile.objects.create(user=user, is_system_admin=True)
        self.stdout.write(self.style.SUCCESS(f'System admin "{username}" created successfully.'))
