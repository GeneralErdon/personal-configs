#!/bin/bash
echo "Creating migrations..."
python manage.py makemigrations
echo =============================================

echo "Starting migration to the database..."
python  manage.py migrate
echo =============================================

echo "Collecting static files from Django..."
python  manage.py collectstatic --noinput
echo =============================================

echo "Starting server..."
python -m gunicorn core.wsgi:application -c config/gunicorn.conf.py
