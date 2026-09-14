from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SubscriptionViewSet, paydunya_callback

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('subscriptions/paydunya/callback/', paydunya_callback, name='paydunya-callback'),
]
