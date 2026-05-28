from rest_framework import serializers
from .models import ReviewAction


class ReviewActionSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = ReviewAction
        fields = [
            'id', 'record', 'performed_by', 'performed_by_name',
            'performed_at', 'action', 'comment',
            'field_changed', 'old_value', 'new_value',
        ]
        read_only_fields = fields


class ReviewSummarySerializer(serializers.Serializer):
    stats = serializers.DictField()
    scope_breakdown = serializers.ListField()
    source_breakdown = serializers.ListField()
