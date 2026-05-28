import uuid
from django.db import models
from apps.tenants.models import Tenant


class SourceType(models.TextChoices):
    SAP = 'sap', 'SAP (Fuel & Procurement)'
    UTILITY = 'utility', 'Utility (Electricity)'
    TRAVEL = 'travel', 'Corporate Travel'


class IngestionBatch(models.Model):
    """
    One upload event. A user uploads a file → one batch.
    Tracks the source file, when it came in, who uploaded it, and final status.
    Source-of-truth: every NormalizedRecord links back here so we always know
    which upload produced it and when.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='batches')
    source_type = models.CharField(max_length=20, choices=SourceType.choices)
    uploaded_by = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, related_name='batches'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    total_rows = models.IntegerField(default=0)
    parsed_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('done', 'Done'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.source_type} batch {self.id} — {self.tenant.name}"

    class Meta:
        ordering = ['-uploaded_at']


class RawRecord(models.Model):
    """
    Exactly what came in from the file, stored as-is.
    Never mutated after insert. This is the audit trail for the raw source.
    If normalization logic changes, we can re-derive from this.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(IngestionBatch, on_delete=models.CASCADE, related_name='raw_records')
    row_index = models.IntegerField()  # original row number in file
    raw_data = models.JSONField()      # entire row as dict, column names preserved
    parse_status = models.CharField(
        max_length=20,
        choices=[
            ('ok', 'Parsed OK'),
            ('failed', 'Parse Failed'),
            ('skipped', 'Skipped'),
        ],
        default='ok'
    )
    parse_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Row {self.row_index} of batch {self.batch_id}"

    class Meta:
        ordering = ['batch', 'row_index']
        unique_together = [['batch', 'row_index']]
