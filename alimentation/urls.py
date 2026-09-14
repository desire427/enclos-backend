from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlimentationViewSet, TypeAlimentViewSet, FrequenceAlimentationViewSet

router = DefaultRouter()
router.register(r'alimentations',  AlimentationViewSet,         basename='alimentation')
router.register(r'type-aliments',  TypeAlimentViewSet,          basename='type-aliment')
router.register(r'frequences',     FrequenceAlimentationViewSet, basename='frequence')

urlpatterns = [
    path('', include(router.urls)),
]
