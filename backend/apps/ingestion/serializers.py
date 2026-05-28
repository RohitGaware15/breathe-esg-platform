from rest_framework import serializers
from .models import IngestionBatch, RawRecord


class IngestionBatchSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = IngestionBatch
        fields = [
            'id', 'tenant', 'tenant_name', 'source_type', 'uploaded_by',
            'uploaded_by_name', 'uploaded_at', 'file_name', 'total_rows',
            'parsed_rows', 'failed_rows', 'status', 'error_message',
        ]
        read_only_fields = fields


class RawRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawRecord
        fields = ['id', 'batch', 'row_index', 'raw_data', 'parse_status', 'parse_error', 'created_at']
        read_only_fields = fields
