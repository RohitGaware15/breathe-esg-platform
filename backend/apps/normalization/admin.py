from django.contrib import admin
from .models import NormalizedRecord

@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'source_type', 'scope', 'category', 'activity_date',
                    'quantity', 'unit', 'co2e_kg', 'review_status', 'is_suspicious']
    list_filter = ['scope', 'source_type', 'review_status', 'is_suspicious', 'tenant']
    search_fields = ['description', 'facility', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at', 'locked_at']
