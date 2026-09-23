"""
ASGI config for enclos project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enclos.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

django_application = get_asgi_application()

from alertes.middleware import JWTAuthMiddleware
from alertes.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
	'http': django_application,
	'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
