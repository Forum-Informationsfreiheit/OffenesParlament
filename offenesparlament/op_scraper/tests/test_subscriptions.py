from django.test import TestCase
from op_scraper.models import *

class SubscriptionTestCase(TestCase):

    fixtures = ['categories', 'llps', 'persons', 'laws']

    def setUp(self):
        pass

    def test_create_subscriptions(self):
        """TBD"""
        assert True
        pass