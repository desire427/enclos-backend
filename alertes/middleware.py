from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth import get_user_model


@database_sync_to_async
def get_user(token):
    try:
        access = AccessToken(token)
        return get_user_model().objects.get(id=access['user_id'])
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        token = parse_qs(query_string).get('token', [None])[0]
        scope['user'] = await get_user(token) if token else AnonymousUser()
        return await self.app(scope, receive, send)