#!/usr/bin/env bash
set -o errexit

python manage.py migrate --noinput
python manage.py ensure_demo_user
gunicorn cyber_project.wsgi:application
