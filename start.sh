#!/bin/bash
rm -f /tmp/db.sqlite3
python manage.py migrate --noinput
exec gunicorn buildstock_project.wsgi:application
