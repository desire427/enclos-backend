from django.test import SimpleTestCase

from sante.models import SuiviSante


class SuiviSanteSchemaRegressionTest(SimpleTestCase):
    def test_date_debut_and_next_consultation_can_be_optional_in_model(self):
        debut = SuiviSante._meta.get_field('date_debut')
        prochaine = SuiviSante._meta.get_field('date_prochaine_consultation')

        self.assertTrue(debut.null)
        self.assertTrue(debut.blank)
        self.assertTrue(prochaine.null)
        self.assertTrue(prochaine.blank)
