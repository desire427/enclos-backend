from rest_framework.test import APITestCase


class PayDunyaCallbackRouteTests(APITestCase):
    def test_paydunya_callback_public_success_message(self):
        response = self.client.get('/api/subscriptions/paydunya/callback/', {'status': 'success'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Paiement validé avec succès', response.json()['message'])

    def test_paydunya_callback_public_cancel_message(self):
        response = self.client.get('/api/subscriptions/paydunya/callback/', {'status': 'cancel'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Paiement annulé', response.json()['message'])
