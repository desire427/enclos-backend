from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from fermes.models import Ferme
from historique.models import HistoriqueEvenement
from moncheptel.models import Animal
from sante.models import SuiviSante

# Create your tests here.

class HistoriquePesageTest(TestCase):
	def setUp(self):
		user = get_user_model().objects.create_user(username='pesage', password='pass12345')
		self.ferme = Ferme.objects.create(nom='Ferme pesage', proprietaire=user)
		self.animal = Animal.objects.create(
			ferme=self.ferme, nom='Alice', espece='bovin', sexe='femelle', poids_actuel=Decimal('100'),
		)

	def test_changement_du_poids_de_la_fiche_est_historise_avec_les_deux_valeurs(self):
		self.animal.poids_actuel = Decimal('125.5')
		self.animal.save(update_fields=['poids_actuel'])

		evenement = HistoriqueEvenement.objects.get(animal=self.animal, type_evenement='Pesage')

		self.assertEqual(evenement.titre, 'Changement de poids')
		self.assertIn('Ancien poids : 100 kg', evenement.description)
		self.assertIn('Nouveau poids : 125.5 kg', evenement.description)
		self.assertIsNotNone(evenement.date_evenement)

	def test_poids_saisi_dans_un_suivi_est_historise_a_la_date_de_pesee(self):
		weighing_date = date(2026, 9, 20)
		SuiviSante.objects.create(
			ferme=self.ferme, animal=self.animal, statut='Malade', date_debut=weighing_date,
			poids_kg=Decimal('108.4'), note='Suivi avec pesée.',
		)

		evenement = HistoriqueEvenement.objects.get(animal=self.animal, type_evenement='Pesage')

		self.assertEqual(evenement.date_evenement.date(), weighing_date)
		self.assertIn('108.4 kg', evenement.description)
