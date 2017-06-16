# -*- coding: UTF-8 -*-
import datetime

from op_scraper.models import *
from op_scraper.subscriptions import JsonDiffer, PersonDiffer, LawDiffer, SearchDiffer
from offenesparlament.views import subscriptions as views

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, TestCase, RequestFactory
from django.core.management import call_command
from django.core import mail
from django.http.response import HttpResponseRedirect

from django.db import transaction
from django.db.models import Q

class BaseSubscriptionTestCase(TestCase):

    fixtures = ['categories', 'llps', 'persons', 'laws', 'debates']
    EMAIL = 'foo@bar.com'

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()

        call_command('rebuild_index', verbosity=0, interactive=False)

    def _extract_verify_url(self,email):
        urls = re.findall('href="http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email.alternatives[0][0])
        for url in urls:
            if '/verify/'.format(self.EMAIL) in url:
                verify_url = url.replace('href="','')
                break
        key = verify_url[verify_url.rfind('/') + 1:]
        return key

    def _prep_subscription(self, post_vars):
        # Create an instance of a subscribe POST request.
        request = self.factory.post('/susbcribe')
        request.user = AnonymousUser()
        request.POST.update(post_vars)

        # Call subscribe view
        response = views.subscribe(request)

        # Extract verification urls, key from email body
        email = mail.outbox.pop()
        key = self._extract_verify_url(email)

        # Find Subscription item
        sub_qs = Subscription.objects.filter(
            user__email=self.EMAIL,
            verification__verification_hash=key)

        # Assert subscription item isn't verified yet
        subscription_item = sub_qs.first()
        subscription_item.verification.verified = True
        subscription_item.verification.save()
        subscription_item.user.verification.verified = True
        subscription_item.user.verification.save()
        return subscription_item
