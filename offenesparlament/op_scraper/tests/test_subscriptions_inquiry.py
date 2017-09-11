# -*- coding: UTF-8 -*-
import datetime

from op_scraper.models import *
from op_scraper.subscriptions import LawDiffer, SearchDiffer, check_subscriptions
from op_scraper.tests import BaseSubscriptionTestCase
from offenesparlament.views import subscriptions as views

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, TestCase, RequestFactory
from django.core.management import call_command
from django.core import mail
from django.http.response import HttpResponseRedirect

from django.db import transaction
from django.db.models import Q

class BaseInquirySubscriptionsTestCase(BaseSubscriptionTestCase):

    def _prep_inquiry_subscription(self):
        inquiry = Inquiry.objects.exclude(status='response_received').exclude(parl_id__startswith='M').first()
        post_vars = self._get_inquiry_subscription_post_vars(inquiry)
        return self._prep_subscription(post_vars)

    def _get_inquiry_subscription_post_vars(self,inquiry):
        return {
            'subscription_url': '/gesetze/search?llp_numeric={}&parl_id={}'.format(
                inquiry.legislative_period.number,
                inquiry.parl_id
                ),
            'search_ui_url': inquiry.slug,
            'subscription_title': inquiry.title,
            'category': 'inquiry',
            'email': self.EMAIL
        }


class InquirySubscriptionsTestCase(BaseInquirySubscriptionsTestCase):

    def test_process_email_empty_inquiry_subscription(self):
        subscription_item = self._prep_inquiry_subscription()
        # Test no changes
        check_subscriptions()
        assert len(mail.outbox) == 0

        # Test changes, but no messages (fields not watched)
        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        inquiry = Inquiry.objects.get(parl_id=parl_id)


        inquiry.save()
        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()
        assert len(mail.outbox) == 0


    def test_process_email_inquiry_subscription(self):
        subscription_item = self._prep_inquiry_subscription()

        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        inquiry = Inquiry.objects.get(parl_id=parl_id)
        # Let's test some changes on the primary items

        changes = {
            'response': InquiryResponse.objects.first()
        }
        for attr in changes:
            inquiry.__setattr__(attr, changes[attr])

        new_steps = []
        [new_steps.append(ph.step_set.first()) for ph in Phase.objects.all()[:5]]
        inquiry.steps = new_steps
        inquiry.save()
        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        alts = email.alternatives
        assert len(alts) == 1
        assert alts[0][1] == u'text/html'

        html_text = alts[0][0]

        assert "Es gibt Neuigkeiten" in html_text
        assert "Anfragen</h2>" in html_text

        assert u"hat eine neue Antwort" in html_text


