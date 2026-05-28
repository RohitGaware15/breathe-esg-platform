from django.contrib import admin
from .models import ReviewAction

@admin.register(ReviewAction)
class ReviewActionAdmin(admin.ModelAdmin):
    list_display = ['id', 'record', 'performed_by', 'action', 'performed_at']
    list_filter = ['action']
    readonly_fields = ['id', 'performed_at']
