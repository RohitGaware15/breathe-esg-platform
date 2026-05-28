import uuid
from django.db import models
from django.utils import timezone
from apps.normalization.models import NormalizedRecord


class ReviewAction(models.Model):
    """
    Immutable audit log. One row per analyst action on a NormalizedRecord.
    Never deleted. This is what goes to auditors.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(NormalizedRecord, on_delete=models.CASCADE, related_name='review_actions')
    performed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    action = models.CharField(
        max_length=20,
        choices=[
            ('approved', 'Approved'),
            ('flagged', 'Flagged'),
            ('rejected', 'Rejected'),
            ('edited', 'Edited'),
            ('comment', 'Comment'),
        ]
    )
    comment = models.TextField(blank=True)
    # For edits: store what changed
    field_changed = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} on {self.record_id} by {self.performed_by}"

    class Meta:
        ordering = ['-performed_at']
