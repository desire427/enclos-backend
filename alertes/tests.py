from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from alertes.models import Alerte
from fermes.models import Ferme
from moncheptel.models import Animal
from sante.models import Ordonnance, RappelOrdonnance
from sante.reminders import process_due_reminders


class RappelsOrdonnanceTest(TestCase):
	def setUp(self):
		self.user = get_user_model().objects.create_user(username='rappels', password='pass12345')
		self.ferme = Ferme.objects.create(nom='Ferme test', proprietaire=self.user)
		self.animal = Animal.objects.create(
			ferme=self.ferme,
			nom='bovin-1',
			espece='bovin',
			sexe='femelle',
			etat_sante='malade',
		)
		self.ordonnance = Ordonnance.objects.create(
			ferme=self.ferme,
			animal=self.animal,
			titre='Traitement',
			date_prescription=timezone.localdate(),
			medicaments='Médicament prescrit',
			instructions='',
		)
		self.client = APIClient()
		self.client.force_authenticate(user=self.user)

	def create_reminder(self, intervalle_minutes=60):
		now = timezone.now()
		return RappelOrdonnance.objects.create(
			ordonnance=self.ordonnance,
			instruction='Administrer le traitement',
			date_prochaine_prise=now - timedelta(minutes=1),
			intervalle_minutes=intervalle_minutes,
			date_fin=now + timedelta(days=2) if intervalle_minutes else None,
		)

	def test_due_reminder_repeats_after_five_minutes(self):
		reminder = self.create_reminder()
		now = timezone.now()

		self.assertEqual(process_due_reminders(now), 1)
		self.assertEqual(process_due_reminders(now + timedelta(minutes=4, seconds=59)), 0)
		self.assertEqual(process_due_reminders(now + timedelta(minutes=5)), 1)
		self.assertEqual(Alerte.objects.filter(rappel_ordonnance=reminder).count(), 2)

	def test_confirmation_advances_repeating_reminder_and_clears_notifications(self):
		reminder = self.create_reminder()
		first_alert = Alerte.objects.create(
			ferme=self.ferme, animal=self.animal, rappel_ordonnance=reminder,
			type_alerte='Rappel traitement', message='Prise à confirmer',
		)
		Alerte.objects.create(
			ferme=self.ferme, animal=self.animal, rappel_ordonnance=reminder,
			type_alerte='Rappel traitement', message='Rappel répété',
		)
		due_at = reminder.date_prochaine_prise

		response = self.client.post(f'/api/alertes/{first_alert.id}/confirmer/')

		self.assertEqual(response.status_code, 200)
		reminder.refresh_from_db()
		self.assertEqual(reminder.date_prochaine_prise, due_at + timedelta(minutes=60))
		self.assertIsNone(reminder.dernier_rappel)
		self.assertEqual(
			set(Alerte.objects.filter(rappel_ordonnance=reminder).values_list('statut', flat=True)),
			{'lue'},
		)

	def test_confirmation_cloture_un_rappel_unique(self):
		reminder = self.create_reminder(intervalle_minutes=None)
		alert = Alerte.objects.create(
			ferme=self.ferme, animal=self.animal, rappel_ordonnance=reminder,
			type_alerte='Rappel traitement', message='Prise à confirmer',
		)

		response = self.client.post(f'/api/alertes/{alert.id}/confirmer/')

		self.assertEqual(response.status_code, 200)
		reminder.refresh_from_db()
		self.assertFalse(reminder.actif)
