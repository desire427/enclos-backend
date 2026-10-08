import json
from io import BytesIO
from datetime import date
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image, ImageDraw
from rest_framework.test import APIClient

from fermes.models import Ferme
from moncheptel.models import Animal
from sante.models import Ordonnance, SuiviSante
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


class ExtractionOrdonnanceTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='ocr', password='pass12345')
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def image(self, color='white'):
        buffer = BytesIO()
        Image.new('RGB', (16, 16), color=color).save(buffer, format='PNG')
        if color == 'white':
            image = Image.new('RGB', (160, 80), color='white')
            ImageDraw.Draw(image).text((8, 8), 'Ordonnance', fill='black')
            buffer = BytesIO()
            image.save(buffer, format='PNG')
        return SimpleUploadedFile('ordonnance.png', buffer.getvalue(), content_type='image/png')

    @patch('sante.views.requests.post')
    @override_settings(GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test')
    def test_ocr_retourne_les_champs_sans_creer_l_ordonnance(self, mock_post):
        response_from_gemini = MagicMock()
        response_from_gemini.json.return_value = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'texte_ordonnance_detecte': True,
            'titre': 'Ordonnance vétérinaire',
            'veterinaire': 'Dr Diallo',
            'date_prescription': '2026-10-08',
            'medicaments': 'Oxytétracycline, 10 mg/kg, pendant 5 jours',
            'instructions': 'Administrer par voie orale.',
        })}]}}]}
        mock_post.return_value = response_from_gemini

        response = self.client.post(
            '/api/ordonnances/extraire/', {'photo': self.image()}, format='multipart'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['veterinaire'], 'Dr Diallo')
        self.assertEqual(response.data['date_prescription'], '2026-10-08')
        self.assertIn('Oxytétracycline', response.data['medicaments'])
        self.assertEqual(Ordonnance.objects.count(), 0)
        mock_post.assert_called_once()

    @patch('sante.views.requests.post')
    @override_settings(GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test')
    def test_photo_toute_noire_est_rejetee_sans_appeler_gemini(self, mock_post):
        response = self.client.post(
            '/api/ordonnances/extraire/', {'photo': self.image(color='black')}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('trop sombre', response.data['detail'])
        mock_post.assert_not_called()

    @patch('sante.views.requests.post')
    @override_settings(GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test')
    def test_ocr_sans_texte_de_prescription_est_refuse(self, mock_post):
        response_from_gemini = MagicMock()
        response_from_gemini.json.return_value = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'texte_ordonnance_detecte': False,
            'titre': '', 'veterinaire': '', 'date_prescription': '', 'medicaments': '', 'instructions': '',
        })}]}}]}
        mock_post.return_value = response_from_gemini

        response = self.client.post(
            '/api/ordonnances/extraire/', {'photo': self.image()}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Aucune écriture', response.data['detail'])
        self.assertEqual(Ordonnance.objects.count(), 0)


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
