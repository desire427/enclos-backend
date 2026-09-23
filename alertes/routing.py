from django.urls import re_path

from .consumers import AlerteConsumer


websocket_urlpatterns = [
    re_path(r'^ws/alertes/(?P<ferme_id>\d+)/$', AlerteConsumer.as_asgi()),
]