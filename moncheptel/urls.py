from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnimalViewSet, RaceViewSet

router = DefaultRouter()
router.register(r'animaux', AnimalViewSet, basename='animal')
router.register(r'races',   RaceViewSet,   basename='race')

urlpatterns = [
    path('', include(router.urls)),
]
