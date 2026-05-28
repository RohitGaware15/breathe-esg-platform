from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReviewActionViewSet, RecordReviewView

router = DefaultRouter()
router.register(r'actions', ReviewActionViewSet, basename='review-action')
router.register(r'records', RecordReviewView, basename='record-review')

urlpatterns = [path('', include(router.urls))]
