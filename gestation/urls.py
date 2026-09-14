from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GestationViewSet

router = DefaultRouter()
router.register(r'gestations', GestationViewSet, basename='gestation')

urlpatterns = [
    path('', include(router.urls)),
]
