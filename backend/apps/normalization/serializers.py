from rest_framework import serializers
from .models import NormalizedRecord


class NormalizedRecordSerializer(serializers.ModelSerializer):
    batch_source_type = serializers.CharField(source='batch.source_type', read_only=True)
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)

    class Meta:
        model = NormalizedRecord
        fields = [
            'id', 'tenant', 'batch', 'batch_source_type', 'raw_record',
            'scope', 'scope_display', 'source_type', 'category',
            'activity_date', 'quantity', 'unit', 'co2e_kg',
            'facility', 'cost_center', 'description', 'extra_data',
            'review_status', 'is_suspicious', 'suspicion_reasons',
            'created_at', 'updated_at', 'is_manually_edited', 'locked_at',
        ]
        read_only_fields = [
            'id', 'tenant', 'batch', 'batch_source_type', 'raw_record',
            'source_type', 'scope_display', 'created_at', 'updated_at', 'locked_at',
        ]
