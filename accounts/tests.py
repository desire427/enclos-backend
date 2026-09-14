from django.test import SimpleTestCase
from django.urls import resolve


class ApiRouteSmokeTests(SimpleTestCase):
    def test_auth_routes_exist_in_api_root(self):
        self.assertIsNotNone(resolve('/api/auth/token/'))
        self.assertIsNotNone(resolve('/api/auth/token/refresh/'))

    def test_plans_and_subscriptions_routes_exist_in_api_root(self):
        self.assertIsNotNone(resolve('/api/plans/'))
        self.assertIsNotNone(resolve('/api/subscriptions/'))
