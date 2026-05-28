#!/bin/bash
set -e

echo "========================================"
echo "BREATHE ESG - Django Backend Startup"
echo "========================================"

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z postgres 5432; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done
echo "PostgreSQL is up!"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput
echo "Migrations completed!"

# Create demo data and superuser if it doesn't exist
echo "Setting up demo data..."
python manage.py setup_demo
echo "Demo data setup completed!"

echo "========================================"
echo "Starting Gunicorn server..."
echo "========================================"

# Start Gunicorn
exec gunicorn \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --timeout 120 \
  --access-logfile - \
  --error-logfile - \
  config.wsgi:application
