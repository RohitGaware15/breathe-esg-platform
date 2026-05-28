#!/bin/bash

python manage.py migrate

python manage.py shell <<EOF
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

U = get_user_model()

# Create admin user
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser(
        'admin',
        'admin@example.com',
        'admin123'
    )

# Create demo tenant
if not Tenant.objects.filter(slug='demo-company').exists():
    Tenant.objects.create(
        name='Demo Company',
        slug='demo-company',
        is_active=True
    )

EOF

gunicorn config.wsgi:application
