from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SuiviSanteViewSet

router = DefaultRouter()
router.register(r'sante', SuiviSanteViewSet, basename='sante')

urlpatterns = [
    path('', include(router.urls)),
]
