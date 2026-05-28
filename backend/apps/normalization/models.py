import uuid
from django.db import models
from apps.tenants.models import Tenant
from apps.ingestion.models import IngestionBatch, RawRecord


class Scope(models.TextChoices):
    SCOPE_1 = '1', 'Scope 1 (Direct)'
    SCOPE_2 = '2', 'Scope 2 (Electricity)'
    SCOPE_3 = '3', 'Scope 3 (Value Chain)'


class NormalizedRecord(models.Model):
    """
    The cleaned, unit-normalized, scope-tagged row ready for analyst review.

    Source-of-truth tracking:
    - batch: which upload event produced this
    - raw_record: exact raw row it came from
    - is_manually_edited: if analyst changed a field, we track that

    All quantities normalized to standard units before storage:
    - Energy: kWh
    - Mass/fuel: litres (liquid fuels) or kg (solid)
    - Travel: km distance + kg CO2e directly

    Scope assignment:
    - SAP fuel → Scope 1
    - Utility electricity → Scope 2
    - Travel → Scope 3 (category 6: business travel)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='normalized_records')
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='normalized_records')
    raw_record = models.OneToOneField(RawRecord, on_delete=models.CASCADE, related_name='normalized')

    # Scope and categorization
    scope = models.CharField(max_length=1, choices=Scope.choices)
    source_type = models.CharField(max_length=20)   # sap | utility | travel
    category = models.CharField(max_length=100, blank=True)  # diesel, electricity, flight, etc.

    # Activity data — normalized
    activity_date = models.DateField(null=True)
    quantity = models.FloatField(null=True)          # normalized quantity
    unit = models.CharField(max_length=20, blank=True) # kwh, litre, km, room_night
    co2e_kg = models.FloatField(null=True)           # estimated CO2e if calculable at ingest

    # Context fields
    facility = models.CharField(max_length=255, blank=True)
    cost_center = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    extra_data = models.JSONField(default=dict)       # source-specific fields that don't fit above

    # Review state
    review_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('flagged', 'Flagged'),
            ('rejected', 'Rejected'),
        ],
        default='pending'
    )

    # Flags for analyst attention
    is_suspicious = models.BooleanField(default=False)
    suspicion_reasons = models.JSONField(default=list)  # list of strings explaining why

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_manually_edited = models.BooleanField(default=False)
    locked_at = models.DateTimeField(null=True, blank=True)  # set when approved for audit

    def __str__(self):
        return f"{self.source_type} | {self.scope} | {self.activity_date} | {self.quantity} {self.unit}"

    class Meta:
        ordering = ['-activity_date', 'source_type']
        indexes = [
            models.Index(fields=['tenant', 'scope']),
            models.Index(fields=['tenant', 'review_status']),
            models.Index(fields=['batch']),
        ]
