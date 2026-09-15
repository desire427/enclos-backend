from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from fermes.models import Ferme
from moncheptel.models import Animal
from sante.models import SuiviSante
from sante.sync import etat_depuis_statut, est_suivi_ouvert


class SuiviSanteSchemaRegressionTest(TestCase):
    def test_date_debut_and_next_consultation_can_be_optional_in_model(self):
        debut = SuiviSante._meta.get_field('date_debut')
        prochaine = SuiviSante._meta.get_field('date_prochaine_consultation')
        date_fin = SuiviSante._meta.get_field('date_fin')

        self.assertTrue(debut.null)
        self.assertTrue(debut.blank)
        self.assertTrue(prochaine.null)
        self.assertTrue(prochaine.blank)
        self.assertTrue(date_fin.null)
        self.assertTrue(date_fin.blank)


class MappingSanteTest(TestCase):
    def test_statut_suivi_vers_etat_animal(self):
        self.assertEqual(etat_depuis_statut('Malade'), 'malade')
        self.assertEqual(etat_depuis_statut('En traitement'), 'en_traitement')
        self.assertEqual(etat_depuis_statut('Guéri'), 'sain')


class SynchronisationSanteTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='eleveur', password='pass12345')
        self.ferme = Ferme.objects.create(nom='Ferme test', proprietaire=user)
        self.animal = Animal.objects.create(
            ferme=self.ferme,
            nom='bovin-1',
            espece='bovin',
            sexe='femelle',
            etat_sante='malade',
        )
        self.suivi = SuiviSante.objects.create(
            ferme=self.ferme,
            animal=self.animal,
            statut='Malade',
            date_debut=date.today(),
            note='Il ne mange plus et faible.',
        )

    def test_animal_sain_cloture_le_suivi_ouvert(self):
        self.animal.etat_sante = 'sain'
        self.animal.observations = "Il vient d'etre guerie."
        self.animal.save()

        self.suivi.refresh_from_db()
        self.assertEqual(self.suivi.statut, 'Guéri')
        self.assertEqual(self.suivi.date_fin, date.today())
        self.assertEqual(self.suivi.note, "Il vient d'etre guerie.")
        self.assertFalse(est_suivi_ouvert(self.suivi))

    def test_suivi_gueri_met_animal_sain(self):
        self.suivi.statut = 'Guéri'
        self.suivi.note = 'Guérison confirmée.'
        self.suivi.save()

        self.animal.refresh_from_db()
        self.assertEqual(self.animal.etat_sante, 'sain')
        self.assertEqual(self.animal.observations, 'Guérison confirmée.')
        self.suivi.refresh_from_db()
        self.assertEqual(self.suivi.date_fin, date.today())

    def test_suivi_en_traitement_met_animal_en_traitement(self):
        self.suivi.statut = 'En traitement'
        self.suivi.save()

        self.animal.refresh_from_db()
        self.assertEqual(self.animal.etat_sante, 'en_traitement')
        self.suivi.refresh_from_db()
        self.assertIsNone(self.suivi.date_fin)

    def test_nouveau_suivi_malade_met_un_animal_sain_a_malade(self):
        animal = Animal.objects.create(
            ferme=self.ferme,
            nom='bovin-2',
            espece='bovin',
            sexe='femelle',
            etat_sante='sain',
        )
        SuiviSante.objects.create(
            ferme=self.ferme,
            animal=animal,
            statut='Malade',
            date_debut=date.today(),
            note='Il a perdu du poids.',
        )
        animal.refresh_from_db()
        self.assertEqual(animal.etat_sante, 'malade')
        self.assertEqual(animal.observations, 'Il a perdu du poids.')

    def test_realigner_rattrape_un_animal_reste_sain(self):
        from sante.sync import realigner_animaux_depuis_suivis_ouverts

        animal = Animal.objects.create(
            ferme=self.ferme,
            nom='bovin-3',
            espece='bovin',
            sexe='femelle',
            etat_sante='sain',
        )
        suivi = SuiviSante(
            ferme=self.ferme,
            animal=animal,
            statut='Malade',
            date_debut=date.today(),
            note='il mange moins actuellement.',
        )
        suivi._skip_animal_sync = True
        suivi.save()

        animal.refresh_from_db()
        self.assertEqual(animal.etat_sante, 'sain')

        realigner_animaux_depuis_suivis_ouverts()
        animal.refresh_from_db()
        self.assertEqual(animal.etat_sante, 'malade')
