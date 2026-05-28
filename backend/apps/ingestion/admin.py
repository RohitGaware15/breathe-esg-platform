from django.contrib import admin
from .models import IngestionBatch, RawRecord

@admin.register(IngestionBatch)
class IngestionBatchAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'source_type', 'tenant', 'status', 'total_rows', 'parsed_rows', 'failed_rows', 'uploaded_at']
    list_filter = ['source_type', 'status', 'tenant']
    readonly_fields = ['id', 'uploaded_at']

@admin.register(RawRecord)
class RawRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'batch', 'row_index', 'parse_status', 'created_at']
    list_filter = ['parse_status']
    readonly_fields = ['id', 'created_at']
