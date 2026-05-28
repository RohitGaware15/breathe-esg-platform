"""
python manage.py seed_demo

Creates a demo tenant, demo analyst user, and ingests all three
sample data files so the app has content on first launch.

Run after migrate + createsuperuser.
"""

import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token

from apps.tenants.models import Tenant
from apps.ingestion.models import IngestionBatch, RawRecord
from apps.ingestion.parsers.sap import parse_sap_file
from apps.ingestion.parsers.utility import parse_utility_file
from apps.ingestion.parsers.travel import parse_travel_file
from apps.normalization.normalizer import normalize_records

SAMPLE_DIR = Path(__file__).resolve().parents[5] / 'sample_data'

PARSERS = {
    'sap': (parse_sap_file, 'sap_export.csv'),
    'utility': (parse_utility_file, 'utility_export.csv'),
    'travel': (parse_travel_file, 'travel_concur.csv'),
}


class Command(BaseCommand):
    help = 'Seed demo tenant and ingest all sample data files'

    def handle(self, *args, **options):
        # Create tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='acme-corp',
            defaults={'name': 'Acme Corp (Demo)'}
        )
        self.stdout.write(f"{'Created' if created else 'Found'} tenant: {tenant.name}")

        # Create demo analyst user
        user, created = User.objects.get_or_create(
            username='analyst',
            defaults={'email': 'analyst@breatheesg.com', 'first_name': 'Demo', 'last_name': 'Analyst'}
        )
        if created:
            user.set_password('breathe123')
            user.save()
            self.stdout.write("Created user: analyst / breathe123")
        token, _ = Token.objects.get_or_create(user=user)

        # Ingest each sample file
        for source_type, (parser_fn, filename) in PARSERS.items():
            file_path = SAMPLE_DIR / filename
            if not file_path.exists():
                self.stdout.write(self.style.WARNING(f"Sample file not found: {file_path}"))
                continue

            file_content = file_path.read_bytes()

            batch = IngestionBatch.objects.create(
                tenant=tenant,
                source_type=source_type,
                uploaded_by=user,
                file_name=filename,
                file=SimpleUploadedFile(filename, file_content),
                status='processing',
            )

            try:
                parsed_rows = parser_fn(file_content)
                raw_records = []
                ok_count = fail_count = 0

                for row in parsed_rows:
                    parse_ok = row.pop('_parse_ok', True)
                    parse_error = row.pop('_parse_error', '')
                    row_index = row.pop('_row_index', 0)
                    raw_data = row.pop('_raw', row)

                    raw_rec = RawRecord(
                        batch=batch,
                        row_index=row_index,
                        raw_data=raw_data,
                        parse_status='ok' if parse_ok else 'failed',
                        parse_error=parse_error,
                    )
                    raw_records.append((raw_rec, row, parse_ok))
                    if parse_ok:
                        ok_count += 1
                    else:
                        fail_count += 1

                created_raws = RawRecord.objects.bulk_create([r[0] for r in raw_records])
                ok_pairs = [(created_raws[i], raw_records[i][1])
                            for i in range(len(raw_records)) if raw_records[i][2]]
                normalize_records(ok_pairs, batch, tenant)

                batch.total_rows = len(parsed_rows)
                batch.parsed_rows = ok_count
                batch.failed_rows = fail_count
                batch.status = 'done'
                batch.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {source_type}: {ok_count} parsed, {fail_count} failed"
                    )
                )
            except Exception as e:
                batch.status = 'failed'
                batch.error_message = str(e)
                batch.save()
                self.stdout.write(self.style.ERROR(f"  {source_type} failed: {e}"))

        self.stdout.write(self.style.SUCCESS('\nDone. Login: analyst / breathe123'))
