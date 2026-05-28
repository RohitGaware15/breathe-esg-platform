#!/bin/bash

python manage.py migrate

python manage.py shell <<EOF
from django.contrib.auth import get_user_model

U = get_user_model()

if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser(
        'admin',
        'admin@example.com',
        'admin123'
    )
EOF

gunicorn config.wsgi:application
