from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PredictionResultatViewSet, predire, pre_diagnostic

router = DefaultRouter()
router.register(r'predictions', PredictionResultatViewSet, basename='prediction')

urlpatterns = [
    path('predire/', predire, name='ia-predire'),
    path('pre-diagnostic/', pre_diagnostic, name='ia-pre-diagnostic'),
    path('', include(router.urls)),
]
