#!/bin/bash
rm -f /tmp/db.sqlite3
python manage.py migrate --noinput
python manage.py create_default_users
exec gunicorn buildstock_project.wsgi:application
