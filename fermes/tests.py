from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.serializers import RegisterSerializer
from fermes.models import Ferme


class RegisterCreatesFarmTest(TestCase):
    def test_register_serializer_creates_account_and_first_farm(self):
        payload = {
            'username': 'eleveur1',
            'email': 'eleveur1@example.com',
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
            'first_name': 'Alphonse',
            'last_name': 'Desire',
            'telephone': '770000000',
            'nom_ferme': 'Ferme du Baobab',
            'localisation': 'Thiès, Sénégal',
            'superficie': Decimal('10.5'),
            'coordonnees_gps': '14.7922,-16.9523',
            'description': 'Ferme d’élevage bovin',
        }

        serializer = RegisterSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(Ferme.objects.filter(proprietaire=user, nom='Ferme du Baobab').exists())
