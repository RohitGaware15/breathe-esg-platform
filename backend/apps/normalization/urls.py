from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NormalizedRecordViewSet

router = DefaultRouter()
router.register(r'records', NormalizedRecordViewSet, basename='normalized-record')

urlpatterns = [path('', include(router.urls))]
