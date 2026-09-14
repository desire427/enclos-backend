from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import FermeViewSet

router = DefaultRouter()
router.register(r'fermes', FermeViewSet, basename='ferme')

urlpatterns = [
    path('', include(router.urls)),
]
