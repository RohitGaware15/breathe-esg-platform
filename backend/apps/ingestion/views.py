from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, filters

from apps.tenants.models import Tenant
from .models import IngestionBatch, RawRecord, SourceType
from .serializers import IngestionBatchSerializer, RawRecordSerializer
from .parsers.sap import parse_sap_file
from .parsers.utility import parse_utility_file
from .parsers.travel import parse_travel_file
from apps.normalization.normalizer import normalize_records


def clean_nan(obj):
    """Replace NaN float values with None for safe JSON serialization."""
    if isinstance(obj, float):
        import math
        return None if math.isnan(obj) else obj
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    return obj


PARSERS = {
    'sap': parse_sap_file,
    'utility': parse_utility_file,
    'travel': parse_travel_file,
}


class UploadView(APIView):
    """
    POST /api/ingestion/upload/
    Accepts: multipart/form-data with fields:
      - source_type: sap | utility | travel
      - tenant_id: UUID
      - file: the data file
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        source_type = request.data.get('source_type')
        tenant_id = request.data.get('tenant_id')
        uploaded_file = request.FILES.get('file')

        # Validate inputs
        if source_type not in PARSERS:
            return Response(
                {'error': f'source_type must be one of: {list(PARSERS.keys())}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not uploaded_file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True)

        # Read file content BEFORE saving to model (consumes the file pointer)
        file_content = uploaded_file.read()
        uploaded_file.seek(0)

        # Create batch record
        batch = IngestionBatch.objects.create(
            tenant=tenant,
            source_type=source_type,
            uploaded_by=request.user,
            file_name=uploaded_file.name,
            file=uploaded_file,
            status='processing',
        )

        try:
            parser = PARSERS[source_type]
            parsed_rows = parser(file_content)

            raw_records = []
            ok_count = 0
            fail_count = 0

            for row in parsed_rows:
                parse_ok = row.pop('_parse_ok', True)
                parse_error = row.pop('_parse_error', '')
                row_index = row.pop('_row_index', 0)
                raw_data = clean_nan(row.pop('_raw', row))
                for k, v in row.items():
                    row[k] = clean_nan(v)

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

            # Bulk create raw records
            created_raws = RawRecord.objects.bulk_create(
                [r[0] for r in raw_records]
            )

            # Normalize successfully parsed rows
            ok_pairs = [(created_raws[i], raw_records[i][1])
                        for i in range(len(raw_records))
                        if raw_records[i][2]]
            normalize_records(ok_pairs, batch, tenant)

            batch.total_rows = len(parsed_rows)
            batch.parsed_rows = ok_count
            batch.failed_rows = fail_count
            batch.status = 'done'
            batch.save()

        except Exception as e:
            batch.status = 'failed'
            batch.error_message = str(e)
            batch.save()
            return Response(
                {'error': f'Processing failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(IngestionBatchSerializer(batch).data, status=status.HTTP_201_CREATED)


class IngestionBatchViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IngestionBatchSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['source_type', 'status', 'tenant']
    ordering_fields = ['uploaded_at']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        return IngestionBatch.objects.select_related('tenant', 'uploaded_by').all()


class RawRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RawRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['batch', 'parse_status']

    def get_queryset(self):
        return RawRecord.objects.select_related('batch').all()
