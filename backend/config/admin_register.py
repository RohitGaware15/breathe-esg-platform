from django.contrib import admin
from apps.tenants.models import Tenant
from apps.ingestion.models import IngestionBatch, RawRecord
from apps.normalization.models import NormalizedRecord
from apps.review.models import ReviewAction


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    search_fields = ['name', 'slug']


@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'source_type', 'tenant', 'status', 'total_rows', 'parsed_rows', 'failed_rows', 'uploaded_at']
    list_filter = ['source_type', 'status', 'tenant']
    search_fields = ['file_name']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'batch', 'row_index', 'parse_status', 'created_at']
    list_filter = ['parse_status']
    readonly_fields = ['id', 'created_at']


@admin.register(NormalizedRecord)
class NormalizedRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'tenant', 'source_type', 'scope', 'category', 'activity_date',
                    'quantity', 'unit', 'co2e_kg', 'review_status', 'is_suspicious']
    list_filter = ['scope', 'source_type', 'review_status', 'is_suspicious', 'tenant']
    search_fields = ['description', 'facility', 'category']
    readonly_fields = ['id', 'created_at', 'updated_at', 'locked_at']


@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'performed_by', 'action', 'performed_at']
    list_filter = ['action']
    readonly_fields = ['id', 'performed_at']
