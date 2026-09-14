from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionResultatViewSet, predire

router = DefaultRouter()
router.register(r'predictions', PredictionResultatViewSet, basename='prediction')

urlpatterns = [
    path('predire/', predire, name='ia-predire'),
    path('', include(router.urls)),
]
