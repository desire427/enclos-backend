import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class AlerteConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        ferme_id = self.scope['url_route']['kwargs']['ferme_id']
        if not user or user.is_anonymous or not await self.owns_ferme(ferme_id, user.id):
            await self.close(code=4003)
            return

        self.group_name = f'alertes_ferme_{ferme_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def alerte_created(self, event):
        await self.send(text_data=json.dumps(event['alerte'], default=str))

    @database_sync_to_async
    def owns_ferme(self, ferme_id, user_id):
        from fermes.models import Ferme
        return Ferme.objects.filter(id=ferme_id, proprietaire_id=user_id).exists()