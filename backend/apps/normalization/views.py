from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import NormalizedRecord
from .serializers import NormalizedRecordSerializer


class NormalizedRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NormalizedRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['scope', 'source_type', 'review_status', 'is_suspicious', 'batch', 'tenant', 'category']
    search_fields = ['description', 'facility', 'category']
    ordering_fields = ['activity_date', 'quantity', 'co2e_kg', 'created_at']
    ordering = ['-activity_date']

    def get_queryset(self):
        return NormalizedRecord.objects.select_related(
            'batch', 'raw_record', 'tenant'
        ).all()
