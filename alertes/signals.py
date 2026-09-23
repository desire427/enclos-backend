from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Alerte
from .serializers import AlerteSerializer


@receiver(post_save, sender=Alerte)
def broadcast_new_alerte(sender, instance, created, **kwargs):
    if not created:
        return

    async_to_sync(get_channel_layer().group_send)(
        f'alertes_ferme_{instance.ferme_id}',
        {'type': 'alerte.created', 'alerte': AlerteSerializer(instance).data},
    )