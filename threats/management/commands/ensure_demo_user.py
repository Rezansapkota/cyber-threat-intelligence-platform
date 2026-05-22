import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update the demo user used for project demonstrations.'

    def handle(self, *args, **options):
        username = os.environ.get('DEMO_USERNAME', 'rejan')
        password = os.environ.get('DEMO_PASSWORD', 'rejan')

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': os.environ.get('DEMO_EMAIL', 'demo@example.com'),
                'is_staff': True,
                'is_superuser': True,
            },
        )
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(self.style.SUCCESS(f'{action} demo user: {username}'))
