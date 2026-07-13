#!/bin/bash
# Production entrypoint for Railway (or any prod host). Unlike
# entrypoint.sh (dev, uses `runserver`), this runs gunicorn and does
# NOT wait-loop for Postgres — Railway starts the DB service before
# the app and handles ordering itself; a hard fail-fast is preferable
# in prod so a bad deploy shows up immediately in logs/health checks.
set -e

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating default admin user (if needed)..."
python manage.py create_default_admin

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting gunicorn..."
exec gunicorn crm.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --access-logfile - \
    --error-logfile -
