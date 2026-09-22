#!/bin/sh

set -e

echo "Checking database connection..."

python manage.py check --database default

echo "Running database migrations..."

python manage.py migrate --noinput

echo "Starting Gunicorn..."

exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}