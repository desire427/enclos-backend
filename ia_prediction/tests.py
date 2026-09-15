from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

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
