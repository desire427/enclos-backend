from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from fermes.models import Ferme
from moncheptel.models import Animal
from rest_framework.test import APIClient


class AnimalQrCodeTest(TestCase):
	def setUp(self):
		user = get_user_model().objects.create_user(username='qr-owner', password='pass12345')
		farm = Ferme.objects.create(nom='Ferme QR', proprietaire=user)
		self.animal = Animal.objects.create(ferme=farm, espece='bovin', sexe='femelle')
		self.client = APIClient()
		self.client.force_authenticate(user=user)

	def test_qr_code_contient_un_identifiant_compact(self):
		response = self.client.get(reverse('animal-qr-code', args=[self.animal.id]))

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['qr_data'], f'ENCLOS1:{self.animal.id}')
		self.assertTrue(response.data['qr_image'].startswith('data:image/png;base64,'))
