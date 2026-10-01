from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SuiviSanteViewSet, OrdonnanceViewSet

router = DefaultRouter()
router.register(r'sante', SuiviSanteViewSet, basename='sante')
router.register(r'ordonnances', OrdonnanceViewSet, basename='ordonnance')

urlpatterns = [
    path('', include(router.urls)),
]
