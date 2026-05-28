from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Count, Sum, Q

from apps.normalization.models import NormalizedRecord
from .models import ReviewAction
from .serializers import ReviewActionSerializer, ReviewSummarySerializer


class ReviewActionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReviewActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReviewAction.objects.select_related('record', 'performed_by').all()


class RecordReviewView(viewsets.ViewSet):
    """
    Analyst actions on NormalizedRecord instances.
    """
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        record = NormalizedRecord.objects.get(pk=pk)
        comment = request.data.get('comment', '')

        record.review_status = 'approved'
        record.locked_at = timezone.now()
        record.save(update_fields=['review_status', 'locked_at', 'updated_at'])

        ReviewAction.objects.create(
            record=record,
            performed_by=request.user,
            action='approved',
            comment=comment,
        )
        return Response({'status': 'approved', 'id': str(record.id)})

    @action(detail=True, methods=['post'], url_path='flag')
    def flag(self, request, pk=None):
        record = NormalizedRecord.objects.get(pk=pk)
        comment = request.data.get('comment', '')

        record.review_status = 'flagged'
        record.save(update_fields=['review_status', 'updated_at'])

        ReviewAction.objects.create(
            record=record,
            performed_by=request.user,
            action='flagged',
            comment=comment,
        )
        return Response({'status': 'flagged', 'id': str(record.id)})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        record = NormalizedRecord.objects.get(pk=pk)
        comment = request.data.get('comment', '')

        record.review_status = 'rejected'
        record.save(update_fields=['review_status', 'updated_at'])

        ReviewAction.objects.create(
            record=record,
            performed_by=request.user,
            action='rejected',
            comment=comment,
        )
        return Response({'status': 'rejected', 'id': str(record.id)})

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Dashboard summary stats for analyst.
        """
        tenant_id = request.query_params.get('tenant_id')
        qs = NormalizedRecord.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)

        stats = qs.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(review_status='pending')),
            approved=Count('id', filter=Q(review_status='approved')),
            flagged=Count('id', filter=Q(review_status='flagged')),
            rejected=Count('id', filter=Q(review_status='rejected')),
            suspicious=Count('id', filter=Q(is_suspicious=True)),
            total_co2e=Sum('co2e_kg'),
        )

        scope_breakdown = list(
            qs.values('scope').annotate(
                count=Count('id'),
                co2e=Sum('co2e_kg'),
            ).order_by('scope')
        )

        source_breakdown = list(
            qs.values('source_type').annotate(
                count=Count('id'),
                co2e=Sum('co2e_kg'),
            ).order_by('source_type')
        )

        return Response({
            'stats': stats,
            'scope_breakdown': scope_breakdown,
            'source_breakdown': source_breakdown,
        })
