from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlerteViewSet

router = DefaultRouter()
router.register(r'alertes', AlerteViewSet, basename='alerte')

urlpatterns = [
    path('', include(router.urls)),
]
