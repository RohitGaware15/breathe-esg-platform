#!/bin/bash
set -e

echo "========================================"
echo "BREATHE ESG - Django Backend Startup"
echo "========================================"

echo "Waiting for PostgreSQL to be ready..."
DB_HOST="${DB_HOST:-postgres}"
while ! nc -z "$DB_HOST" 5432; do
  echo "PostgreSQL ($DB_HOST:5432) is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up!"

echo "Running database migrations..."
python manage.py migrate --noinput
echo "Migrations completed!"

echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Static files collected!"

echo "Setting up demo data..."
python manage.py setup_demo
echo "Demo data setup completed!"

echo "========================================"
echo "Starting Gunicorn server..."
echo "========================================"

exec gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
