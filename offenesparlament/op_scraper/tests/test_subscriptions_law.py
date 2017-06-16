# -*- coding: UTF-8 -*-
import datetime

from op_scraper.models import *
from op_scraper.subscriptions import JsonDiffer, LawDiffer, SearchDiffer, check_subscriptions
from op_scraper.tests import BaseSubscriptionTestCase
from offenesparlament.views import subscriptions as views

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, TestCase, RequestFactory
from django.core.management import call_command
from django.core import mail
from django.http.response import HttpResponseRedirect

from django.db import transaction
from django.db.models import Q

class BaseLawSubscriptionsTestCase(BaseSubscriptionTestCase):

    def _prep_law_subscription(self):
        law = Law.objects.first()
        post_vars = self._get_law_subscription_post_vars(law)
        return self._prep_subscription(post_vars)

    def _prep_laws_subscription(self):
        post_vars = self._get_laws_subscription_post_vars()
        return self._prep_subscription(post_vars)

    def _get_law_subscription_post_vars(self,law):
        return {
            'subscription_url': '/gesetze/search?llp_numeric={}&parl_id={}'.format(
                law.legislative_period.number,
                law.parl_id
                ),
            'search_ui_url': law.slug,
            'subscription_title': law.title,
            'category': 'law',
            'email': self.EMAIL
        }

    def _get_laws_subscription_post_vars(self):
        return {
            'subscription_url': '/gesetze/search?llps=XXV&type=Gesetze&q=Gesetz',
            'search_ui_url': '/gesetze/search?llps=XXV&type=Gesetze&q=Gesetz',
            'subscription_title': 'Gesetze in Periode XXV: Gesetz',
            'email': self.EMAIL
        }

class LawSubscriptionsTestCase(BaseLawSubscriptionsTestCase):

    def test_list_law_subscriptions(self):
        subscription_item = self._prep_law_subscription()

        user = subscription_item.user
        key = user.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/abos')
        request.user = AnonymousUser()
        response = views.list(request,self.EMAIL,key)

        assert '/unsubscribe/{}/{}'.format(self.EMAIL,subscription_item.verification.verification_hash) in response.content

    def test_process_email_empty_law_subscription(self):
        subscription_item = self._prep_law_subscription()
        # Test no changes
        check_subscriptions()
        assert len(mail.outbox) == 0

        # Test changes, but no messages (fields not watched)
        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        law = Law.objects.get(parl_id=parl_id)

        new_category = [cat for cat in Category.objects.all()[:5] if cat != law.category][0]
        law.category = new_category

        law.save()
        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()
        assert len(mail.outbox) == 0


    def test_process_email_law_subscription(self):
        subscription_item = self._prep_law_subscription()

        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        law = Law.objects.get(parl_id=parl_id)
        # Let's test some changes on the primary items

        changes = {
            'title': "Novelle zur Novelle der Begutachtung des Hohen Hauses",
            'description': "Ein ganz tolles neues Gesetz! Frohlocket!",
        }
        for attr in changes:
            law.__setattr__(attr, changes[attr])

        new_keywords = Keyword.objects.all()[:5]
        law.keywords = new_keywords

        new_opinions = [op for op in Opinion.objects.all() if op.prelaw != law][:5]
        law.opinions = new_opinions

        new_steps = []
        [new_steps.append(ph.step_set.first()) for ph in Phase.objects.all()[:5]]
        law.steps = new_steps

        law.save()
        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        alts = email.alternatives
        assert len(alts) == 1
        assert alts[0][1] == u'text/html'

        html_text = alts[0][0]

        assert "Es gibt Neuigkeiten" in html_text
        assert "Gesetze</h2>" in html_text

        assert changes['title'] in html_text
        assert changes['description'] in html_text

        assert u"hat 5 neue Schlagworte:" in html_text
        assert u"hat 5 neue Stellungnahmen:" in html_text
        assert u"hat 5 Statusänderungen im parl. Verfahren:" in html_text

    def test_delete_law_subscription(self):
        subscription_item = self._prep_law_subscription()

        user = subscription_item.user
        key = subscription_item.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/unsubscribe')
        request.user = AnonymousUser()
        response = views.unsubscribe(request,self.EMAIL,key)

        assert response.__class__ == HttpResponseRedirect

    def test_create_law_subscription(self):
        """
        Tests the creation of a single law subscription step-by-step,
        including verification
        """
        law = Law.objects.first()
        post_vars = self._get_law_subscription_post_vars(law)

        # Create an instance of a subscribe POST request.
        request = self.factory.post('/susbcribe')
        request.user = AnonymousUser()
        request.POST.update(post_vars)

        # Call subscribe view
        response = views.subscribe(request)

        # Verify Email was sent
        assert response.content == "Ein Best\xc3\xa4tigungslink wurde soeben an '{}' gesendet.".format(self.EMAIL)
        assert len(mail.outbox) == 1

        # Extract verification urls, key from email body
        email = mail.outbox.pop()
        key = self._extract_verify_url(email)

        # Find Subscription item
        sub_qs = Subscription.objects.filter(
            user__email=self.EMAIL,
            verification__verification_hash=key)

        assert sub_qs.exists() == True
        assert sub_qs.count() == 1

        # Assert subscription item isn't verified yet
        subscription_item = sub_qs.first()
        assert subscription_item.verification.verified == False

        # Create an instance of a verify POST request.
        request = self.factory.post('/verify')
        response = views.verify(request, self.EMAIL, key)

        assert 'Ihr Abo ist somit best\xc3\xa4tigt und aktiv' in response.content

        subscription_item.verification.refresh_from_db()

        assert subscription_item.verification.verified == True

        # verify that the archive ES is the same as the current content (we have no changes)
        assert subscription_item.content.get_content() == subscription_item.content.retrieve_latest_content()
        assert len(subscription_item.content.get_content()) == 1

class LawsSubscriptionsTestCase(BaseLawSubscriptionsTestCase):

    def test_list_laws_subscriptions(self):
        subscription_item = self._prep_laws_subscription()

        user = subscription_item.user
        key = user.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/abos')
        request.user = AnonymousUser()
        response = views.list(request,self.EMAIL,key)

        assert '/unsubscribe/{}/{}'.format(self.EMAIL,subscription_item.verification.verification_hash) in response.content

    def test_delete_laws_subscription(self):
        subscription_item = self._prep_laws_subscription()

        user = subscription_item.user
        key = subscription_item.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/unsubscribe')
        request.user = AnonymousUser()
        response = views.unsubscribe(request,self.EMAIL,key)

        assert response.__class__ == HttpResponseRedirect

    def test_process_email_empty_laws_subscription(self):
        subscription_item = self._prep_laws_subscription()

        # Test no changes
        check_subscriptions()
        assert len(mail.outbox) == 0

    def test_process_emails_laws_subscription(self):
        subscription_item = self._prep_laws_subscription()
        parl_ids = [l['parl_id'] for l in subscription_item.content.get_content()]
        for parl_id in parl_ids[:2]:
            law = Law.objects.get(parl_id=parl_id)
            law.pk = None
            law.title = u"{}2".format(law.title)
            law.parl_id = u"{}2".format(law.parl_id)
            law.references = None
            law.save()

        law = Law.objects.get(parl_id=parl_ids[-1])
        law.title = u"{}2".format(law.title)
        law.save()

        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        alts = email.alternatives
        assert len(alts) == 1
        assert alts[0][1] == u'text/html'

        html_text = alts[0][0]

        assert "2 neue Ergebnisse</li>" in html_text
        assert "ndertes Ergebnis</li>" in html_text

    def test_create_laws_search_subscription(self):
        """
        Tests the creation of a single law subscription step-by-step,
        including verification
        """
        post_vars = self._get_laws_subscription_post_vars()

        # Create an instance of a subscribe POST request.
        request = self.factory.post('/susbcribe')
        request.user = AnonymousUser()
        request.POST.update(post_vars)

        # Call subscribe view
        response = views.subscribe(request)

        # Verify Email was sent
        assert response.content == "Ein Best\xc3\xa4tigungslink wurde soeben an '{}' gesendet.".format(self.EMAIL)
        assert len(mail.outbox) == 1

        # Extract verification urls, key from email body
        email = mail.outbox.pop()
        key = self._extract_verify_url(email)

        # Find Subscription item
        sub_qs = Subscription.objects.filter(
            user__email=self.EMAIL,
            verification__verification_hash=key)

        assert sub_qs.exists() == True
        assert sub_qs.count() == 1

        # Assert subscription item isn't verified yet
        subscription_item = sub_qs.first()
        assert subscription_item.verification.verified == False

        # Create an instance of a verify POST request.
        request = self.factory.post('/verify')
        response = views.verify(request, self.EMAIL, key)

        assert 'Ihr Abo ist somit best\xc3\xa4tigt und aktiv' in response.content

        subscription_item.verification.refresh_from_db()

        assert subscription_item.verification.verified == True

        # verify that the archive ES is the same as the current content (we have no changes)
        for i in subscription_item.content.get_content():
            assert i in subscription_item.content.retrieve_latest_content()

class JsonDifferLawEqualTestCase(BaseLawSubscriptionsTestCase):
    def test_json_differ_equal(self):
        subscription_item = self._prep_laws_subscription()
        differ = LawDiffer(subscription_item.content)
        assert differ.collect_changesets() == {}

class JsonDifferLawTestCase(BaseLawSubscriptionsTestCase):
    def test_json_differ_changes(self):
        subscription_item = self._prep_law_subscription()
        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        law = Law.objects.get(parl_id=parl_id)
        # Let's test some changes on the primary items

        changes = {
            'title': "Novelle zur Novelle der Begutachtung des Hohen Hauses",
            'description': "Ein ganz tolles neues Gesetz! Frohlocket!",
        }
        for attr in changes:
            law.__setattr__(attr, changes[attr])

        law.save()

        call_command('rebuild_index', verbosity=0, interactive=False)
        differ = LawDiffer(subscription_item.content)

        differ.print_changesets()
        cs = differ.collect_changesets()

        cs = cs[parl_id]

        # Assert all our changes were reflected in the changeset
        for attr in changes:
            assert attr in cs
            assert cs[attr]['new'] == changes[attr]

        # Test the generated message snippets
        snippets = differ.render_snippets()

        assert u"<li>hat eine neue Beschreibung: Ein ganz tolles neues Gesetz! Frohlocket!</li>" in snippets
        assert u"<li>hat einen neuen Titel: Novelle zur Novelle der Begutachtung des Hohen Hauses</li>" in snippets

    def test_json_differ_json_changes(self):
        subscription_item = self._prep_law_subscription()
        parl_id = [l['parl_id'] for l in subscription_item.content.get_content()][0]
        law = Law.objects.get(parl_id=parl_id)

        new_keywords = Keyword.objects.all()[:5]
        law.keywords = new_keywords

        new_opinions = [op for op in Opinion.objects.all() if op.prelaw != law][:5]
        law.opinions = new_opinions

        new_steps = []
        [new_steps.append(ph.step_set.first()) for ph in Phase.objects.all()[:5]]
        law.steps = new_steps

        law.save()

        call_command('rebuild_index', verbosity=0, interactive=False)
        differ = LawDiffer(subscription_item.content)

        cs = differ.collect_changesets()

        assert law.parl_id in cs
        cs = cs[parl_id]

        assert len(cs['keywords']['N']) == 5
        assert len(cs['opinions']['N']) == 5
        assert len(cs['steps']['N']) == 5

        # Test the generated message snippets
        snippets = differ.render_snippets()

        assert law.title in snippets

        assert u"<li>hat 5 neue Schlagworte:" in snippets
        assert u"<li>hat 5 neue Stellungnahmen:" in snippets
        assert u"<li>hat 5 Statusänderungen im parl. Verfahren:" in snippets

class JsonDifferLawsEqualTestCase(BaseLawSubscriptionsTestCase):
    def test_json_differ_equal(self):
        subscription_item = self._prep_laws_subscription()
        differ = LawDiffer(subscription_item.content)
        assert differ.collect_changesets() == {}

class JsonDifferLawsTestCase(BaseLawSubscriptionsTestCase):
    def test_json_differ_changes(self):
        subscription_item = self._prep_laws_subscription()
        parl_ids = [l['parl_id'] for l in subscription_item.content.get_content()]
        for parl_id in parl_ids[:2]:
            law = Law.objects.get(parl_id=parl_id)
            law.pk = None
            law.title = u"{}2".format(law.title)
            law.parl_id = u"{}2".format(law.parl_id)
            law.references = None
            law.save()

        law = Law.objects.get(parl_id=parl_ids[-1])
        law.title = u"{}2".format(law.title)
        law.save()

        call_command('rebuild_index', verbosity=0, interactive=False)

        differ = SearchDiffer(subscription_item.content)

        cs = differ.collect_changesets()
        assert parl_ids[-1] in cs
        assert 'title' in cs[parl_ids[-1]]
        assert cs[parl_ids[-1]]['title']['new'][-1] == '2'

        new = differ.collect_new()
        deleted = differ.collect_deleted()

        assert len(deleted) == 0
        assert len(new) == 2

