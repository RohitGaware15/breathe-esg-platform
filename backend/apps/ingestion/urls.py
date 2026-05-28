from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadView, IngestionBatchViewSet, RawRecordViewSet

router = DefaultRouter()
router.register(r'batches', IngestionBatchViewSet, basename='batch')
router.register(r'raw-records', RawRecordViewSet, basename='rawrecord')

urlpatterns = [
    path('upload/', UploadView.as_view(), name='upload'),
    path('', include(router.urls)),
]
