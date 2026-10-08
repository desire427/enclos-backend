import json
from io import BytesIO
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from alertes.models import Alerte
from fermes.models import Ferme
from historique.models import HistoriqueEvenement
from ia_prediction.predictor import (
    _alerte_variation_poids,
    _est_vrai,
    _normaliser_reponse_n8n,
    run_prediction,
)
from moncheptel.models import Animal
from rest_framework.test import APIClient
from ia_prediction.models import PreDiagnostic


RESULTAT_FAUX = {
    'est_malade': False,
    'probabilite': 0.16,
    'shap_values': {},
    'features_used': {'poids_kg': 31.4},
    'comparaison_historique': {'disponible': False},
}


class N8nReponseTest(TestCase):
    def test_creer_alerte_accepte_la_chaine_true(self):
        self.assertTrue(_est_vrai('true'))
        self.assertTrue(_est_vrai('Oui'))
        self.assertFalse(_est_vrai('false'))

    def test_reponse_n8n_en_liste_est_depliee(self):
        data = _normaliser_reponse_n8n([{'creer_alerte': True, 'message_alerte': 'x'}])
        self.assertEqual(data['message_alerte'], 'x')


class AlertePoidsTest(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='eleveur', password='pass12345')
        self.ferme = Ferme.objects.create(nom='Ferme test', proprietaire=user)
        self.animal = Animal.objects.create(
            ferme=self.ferme,
            nom='Alice',
            espece='bovin',
            sexe='femelle',
            poids_naissance=16.9,
        )

    def test_saut_de_poids_cree_une_alerte(self):
        self.animal._poids_avant = 16.90
        self.animal.poids_naissance = 31.40
        _alerte_variation_poids(self.animal)

        alerte = Alerte.objects.get(animal=self.animal, statut='non_lue')
        self.assertEqual(alerte.type_alerte, 'Avertissement')
        self.assertIn('16.90', alerte.message)
        self.assertIn('31.40', alerte.message)

    @patch('ia_prediction.predictor.predict', return_value=RESULTAT_FAUX)
    @patch('ia_prediction.predictor.requests.post')
    @override_settings(N8N_WEBHOOK_URL='http://n8n.test/webhook')
    def test_n8n_creer_alerte_en_texte_est_pris_en_compte(self, mock_post, _mock_predict):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {
            'explication_llm': 'Analyse ok',
            'creer_alerte': 'true',
            'message_alerte': 'Vérifiez Alice.',
            'niveau_alerte': 'Avertissement',
        }
        mock_post.return_value = resp

        run_prediction(self.animal, declencheur='manuel')

        self.assertTrue(Alerte.objects.filter(animal=self.animal, message='Vérifiez Alice.').exists())
        self.assertTrue(
            HistoriqueEvenement.objects.filter(animal=self.animal, source_ia=True).exists()
        )


class PreDiagnosticObservationTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='diagnostic', password='pass12345')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def photo(self):
        image_data = BytesIO()
        Image.new('RGB', (2, 2), color='white').save(image_data, format='PNG')
        return SimpleUploadedFile('animal.png', image_data.getvalue(), content_type='image/png')

    @staticmethod
    def image_check(species, matches=True, reason=''):
        response = MagicMock()
        response.json.return_value = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'espece_image': species,
            'correspondance': matches,
            'raison': reason,
        })}]}}]}
        return response

    @staticmethod
    def scope_check(in_domain=True, concerns_animal=True, compatible_sex=True):
        response = MagicMock()
        response.json.return_value = {'candidates': [{'content': {'parts': [{'text': json.dumps({
            'dans_domaine_sante_animale': in_domain,
            'concerne_cet_animal': concerns_animal,
            'compatible_sexe': compatible_sex,
        })}]}}]}
        return response

    @override_settings(GEMINI_API_KEY='test-key', OPENROUTER_API_KEY='test-key')
    def test_observation_de_moins_de_trois_mots_est_refusee(self):
        response = self.client.post(
            '/api/ia/pre-diagnostic/', {'description': 'toux forte', 'photo': self.photo()}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['detail'], 'L’observation initiale doit contenir au moins 3 mots.')

    @patch('ia_prediction.views.requests.post')
    @override_settings(
        GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test',
        OPENROUTER_API_KEY='test-key', OPENROUTER_VISION_MODEL='test-model',
    )
    def test_photo_et_observation_coherentes_sont_analysees(self, mock_post):
        response_from_openrouter = MagicMock()
        response_from_openrouter.json.return_value = {
            'choices': [{'message': {'content': json.dumps({
                'message': 'Quel comportement observez-vous ?',
                'suggestions': [],
                'recommandations': [],
                'urgence': 'faible',
                'limites': 'Observation générale.',
            })}}]
        }
        mock_post.side_effect = [self.image_check('ovin'), self.scope_check(), response_from_openrouter]

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'description': 'Mon mouton tousse souvent', 'photo': self.photo()}, format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        diagnostic = PreDiagnostic.objects.get(id=response.data['id'])
        self.assertIsNone(diagnostic.animal_id)
        self.assertTrue(diagnostic.photo)
        self.assertEqual(response.data['validation_image']['espece'], 'ovin')
        self.assertEqual(mock_post.call_count, 3)

    @patch('ia_prediction.views.requests.post')
    @override_settings(
        GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test',
        OPENROUTER_API_KEY='test-key', OPENROUTER_VISION_MODEL='test-model',
    )
    def test_le_deuxieme_message_reprend_le_fil_et_est_enregistre_dans_l_historique(self, mock_post):
        ferme = Ferme.objects.create(nom='Ferme diagnostic', proprietaire=self.user)
        animal = Animal.objects.create(ferme=ferme, nom='Alice', espece='ovin', sexe='femelle')
        first_answer = MagicMock()
        first_answer.json.return_value = {'choices': [{'message': {'content': json.dumps({
            'message': 'Quel comportement observez-vous ?',
            'suggestions': [], 'recommandations': [], 'urgence': 'modérée',
            'limites': 'Une observation à compléter.',
        })}}]}
        second_answer = MagicMock()
        second_answer.json.return_value = {'choices': [{'message': {'content': json.dumps({
            'message': 'La salivation et la baisse d’appétit sont importantes à surveiller.',
            'suggestions': [], 'recommandations': ['Contactez un vétérinaire rapidement.'],
            'urgence': 'élevée', 'limites': 'Un examen vétérinaire est nécessaire.',
        })}}]}
        mock_post.side_effect = [
            self.image_check('ovin'), self.scope_check(), first_answer,
            self.scope_check(), second_answer,
        ]

        first_response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'animal_id': animal.id, 'description': 'Mon mouton est malade', 'photo': self.photo()},
            format='multipart',
        )
        second_response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {
                'animal_id': animal.id,
                'diagnostic_id': first_response.data['id'],
                'description': 'Il bave et mange peu',
            },
            format='multipart',
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 201)
        self.assertEqual(second_response.data['id'], first_response.data['id'])
        self.assertEqual(len(second_response.data['conversation']), 4)
        second_prompt_messages = mock_post.call_args_list[4].kwargs['json']['messages']
        self.assertIn('Mon mouton est malade', str(second_prompt_messages))
        self.assertIn('Quel comportement observez-vous ?', str(second_prompt_messages))
        self.assertEqual(PreDiagnostic.objects.count(), 1)
        self.assertEqual(HistoriqueEvenement.objects.filter(animal=animal, type_evenement='Pré-diagnostic IA').count(), 1)
        event = HistoriqueEvenement.objects.get(animal=animal, type_evenement='Pré-diagnostic IA')
        self.assertIn('Mon mouton est malade', event.description)
        self.assertIn('Il bave et mange peu', event.description)
        self.assertIn('La salivation et la baisse d’appétit', event.description)

    @patch('ia_prediction.views.requests.post')
    @override_settings(
        GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test',
        OPENROUTER_API_KEY='test-key', OPENROUTER_VISION_MODEL='test-model',
    )
    def test_photo_de_bovin_associee_a_sa_fiche_est_acceptee(self, mock_post):
        ferme = Ferme.objects.create(nom='Ferme bovins', proprietaire=self.user)
        animal = Animal.objects.create(ferme=ferme, nom='Ange', espece='bovin', sexe='femelle')
        response_from_openrouter = MagicMock()
        response_from_openrouter.json.return_value = {'choices': [{'message': {'content': json.dumps({
            'message': 'Depuis quand Ange présente-t-il ces symptômes ?',
            'suggestions': [], 'recommandations': [], 'urgence': 'modérée',
            'limites': 'Échange à poursuivre avec un vétérinaire.',
        })}}]}
        mock_post.side_effect = [self.image_check('bovin'), self.scope_check(), response_from_openrouter]

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'animal_id': animal.id, 'description': 'Mon bovin semble malade', 'photo': self.photo()},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['validation_image']['espece'], 'bovin')
        self.assertEqual(response.data['message'], 'Depuis quand Ange présente-t-il ces symptômes ?')

    @patch('ia_prediction.views.requests.post')
    @override_settings(
        GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test',
        OPENROUTER_API_KEY='test-key', OPENROUTER_VISION_MODEL='test-model',
    )
    def test_question_hors_domaine_est_refusee_sans_appeler_le_modele_medical(self, mock_post):
        mock_post.side_effect = [
            self.image_check('ovin', matches=False, reason='Le texte ne décrit pas le mouton photographié.'),
            self.scope_check(in_domain=False, concerns_animal=False),
        ]

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'description': 'Quelle est la capitale du Sénégal ?', 'photo': self.photo()}, format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('uniquement aux questions de santé', response.data['message'])
        self.assertEqual(len(response.data['conversation']), 2)
        self.assertEqual(mock_post.call_count, 2)

    @patch('ia_prediction.views.requests.post')
    @override_settings(
        GEMINI_API_KEY='test-key', GEMINI_VISION_MODEL='gemini-test',
        OPENROUTER_API_KEY='test-key', OPENROUTER_VISION_MODEL='test-model',
    )
    def test_question_de_gestation_est_refusee_pour_un_male(self, mock_post):
        ferme = Ferme.objects.create(nom='Ferme mâles', proprietaire=self.user)
        animal = Animal.objects.create(ferme=ferme, nom='Bouc', espece='caprin', sexe='male')
        mock_post.side_effect = [
            self.image_check('caprin'),
            self.scope_check(in_domain=True, concerns_animal=True, compatible_sex=False),
        ]

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'animal_id': animal.id, 'description': 'Mon animal peut-il être en gestation ?', 'photo': self.photo()},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertIn('ne s’applique pas au sexe', response.data['message'])
        self.assertIn('Sexe : Mâle', mock_post.call_args_list[1].kwargs['json']['contents'][0]['parts'][0]['text'])
        self.assertEqual(mock_post.call_count, 2)

    @patch('ia_prediction.views.requests.post')
    @override_settings(GEMINI_API_KEY='test-key', OPENROUTER_API_KEY='test-key')
    def test_espece_non_prise_en_charge_est_refusee_avant_le_diagnostic(self, mock_post):
        mock_post.return_value = self.image_check('autre')

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'description': 'Mon bovin tousse souvent', 'photo': self.photo()}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('seules prises en charge', response.data['detail'])
        self.assertEqual(mock_post.call_count, 1)

    @patch('ia_prediction.views.requests.post')
    @override_settings(GEMINI_API_KEY='test-key', OPENROUTER_API_KEY='test-key')
    def test_description_sans_lien_avec_la_photo_est_refusee(self, mock_post):
        mock_post.side_effect = [
            self.image_check('ovin', matches=False, reason='La description parle d’un porc.'),
            self.scope_check(),
        ]

        response = self.client.post(
            '/api/ia/pre-diagnostic/',
            {'description': 'Mon porc refuse de manger', 'photo': self.photo()}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('ne semblent pas correspondre', response.data['detail'])
        self.assertEqual(mock_post.call_count, 2)

    def test_photo_est_obligatoire(self):
        response = self.client.post(
            '/api/ia/pre-diagnostic/', {'description': 'Mon mouton tousse souvent'}, format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('photo est obligatoire', response.data['detail'])
