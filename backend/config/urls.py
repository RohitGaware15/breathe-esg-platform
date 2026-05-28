from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/tenants/', include('apps.tenants.urls')),
    path('api/ingestion/', include('apps.ingestion.urls')),
    path('api/normalization/', include('apps.normalization.urls')),
    path('api/review/', include('apps.review.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
