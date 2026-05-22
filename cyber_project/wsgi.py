"""
WSGI config for cyber_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyber_project.settings')

application = get_wsgi_application()

if os.environ.get('RUN_STARTUP_TASKS', 'True').lower() == 'true':
    call_command('migrate', interactive=False, verbosity=0)
    call_command('ensure_demo_user', verbosity=0)
