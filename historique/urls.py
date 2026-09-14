from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HistoriqueEvenementViewSet

router = DefaultRouter()
router.register(r'historiques', HistoriqueEvenementViewSet, basename='historique')

urlpatterns = [
    path('', include(router.urls)),
]
