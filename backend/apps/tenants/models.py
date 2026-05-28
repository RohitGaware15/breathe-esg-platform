import uuid
from django.db import models


class Tenant(models.Model):
    """
    One row per client company. All data is scoped to a tenant.
    Multi-tenancy via FK, not schema separation — simpler for a prototype,
    sufficient for the scale Breathe ESG operates at now.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
