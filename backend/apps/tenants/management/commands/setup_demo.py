from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.tenants.models import Tenant


class Command(BaseCommand):
    help = 'Create demo superuser and tenant for quick setup'

    def handle(self, *args, **kwargs):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@breatheesg.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin123'))
        else:
            self.stdout.write('Superuser already exists')

        tenant, created = Tenant.objects.get_or_create(
            slug='acme-corp',
            defaults={'name': 'Acme Corp'}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created tenant: {tenant.name} (id: {tenant.id})'))
        else:
            self.stdout.write(f'Tenant already exists: {tenant.name}')

        self.stdout.write(self.style.SUCCESS('\nSetup complete. Login: admin / admin123'))
