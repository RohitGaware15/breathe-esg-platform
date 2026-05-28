from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # In prod: filter to tenants the user belongs to
        return Tenant.objects.filter(is_active=True)
