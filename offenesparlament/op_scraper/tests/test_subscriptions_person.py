# -*- coding: UTF-8 -*-
import datetime

from op_scraper.models import *
from op_scraper.subscriptions import JsonDiffer, PersonDiffer, check_subscriptions
from op_scraper.tests import BaseSubscriptionTestCase
from offenesparlament.views import subscriptions as views

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, TestCase, RequestFactory
from django.core.management import call_command
from django.core import mail
from django.http.response import HttpResponseRedirect

from django.db import transaction
from django.db.models import Q

class BasePersonSubscriptionsTestCase(BaseSubscriptionTestCase):

    def _prep_person_subscription(self):
        person = Person.objects.first()
        post_vars = self._get_person_subscription_post_vars(person)
        return self._prep_subscription(post_vars)

    def _prep_persons_subscription(self):
        post_vars = self._get_persons_subscription_post_vars()
        return self._prep_subscription(post_vars)

    def _get_person_subscription_post_vars(self,person):
        return {
            'subscription_url': '/personen/search?parl_id={}'.format(
                person.parl_id
                ),
            'search_ui_url': person.slug,
            'subscription_title': person.full_name,
            'category': 'person',
            'email': self.EMAIL
        }

    def _get_persons_subscription_post_vars(self):
        return {
            'subscription_url': '/personen/search?llps=XXV&type=Personen',
            'search_ui_url': '/suche/personen?llps=XXV',
            'subscription_title': u'Personen in Periode XXV',
            'email': self.EMAIL
        }

class PersonSubscriptionsTestCase(BasePersonSubscriptionsTestCase):

    def test_list_person_subscriptions(self):
        subscription_item = self._prep_person_subscription()

        user = subscription_item.user
        key = user.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/abos')
        request.user = AnonymousUser()
        response = views.list(request,self.EMAIL,key)

        assert '/unsubscribe/{}/{}'.format(self.EMAIL,subscription_item.verification.verification_hash) in response.content

    def test_delete_person_subscription(self):
        subscription_item = self._prep_person_subscription()

        user = subscription_item.user
        key = subscription_item.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/unsubscribe')
        request.user = AnonymousUser()
        response = views.unsubscribe(request,self.EMAIL,key)

        assert response.__class__ == HttpResponseRedirect

    def test_process_email_empty_person_subscription(self):
        subscription_item = self._prep_person_subscription()
        # Test no changes
        check_subscriptions()
        assert len(mail.outbox) == 0

        # Test changes, but no messages (fields not watched)
        parl_id = [p['parl_id'] for p in subscription_item.content.get_content()][0]
        person = Person.objects.get(parl_id=parl_id)

        # Let's test some changes on the primary items

        changes = {
            'reversed_name': "arabraB dnasiertS",
        }
        for attr in changes:
            person.__setattr__(attr, changes[attr])

        person.save()

        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()
        assert len(mail.outbox) == 0

    def test_process_email_person_subscription(self):
        subscription_item = self._prep_person_subscription()

        parl_id = [p['parl_id'] for p in subscription_item.content.get_content()][0]
        person = Person.objects.get(parl_id=parl_id)

        changes = {
            'birthdate': datetime.date(1959,6,20),
            'deathdate': datetime.date(2000,6,20),
            'full_name': "Barbara Streisand",
            'reversed_name': "Streisand, Barbara",
            'birthplace': "Buxtehude",
            'deathplace': "Wien",
            'occupation': "Rechte Reckin",
        }
        for attr in changes:
            person.__setattr__(attr, changes[attr])

        changed_mandate = person.mandate_set.all().first()
        changed_mandate.end_date = datetime.date(2026,1,1)
        changed_mandate.start_date = datetime.date(2000,1,1)
        changed_mandate.save()
        new_mandate = Mandate.objects.filter(~Q(party__short = person.party.short)).all()[0]
        person.mandates = [new_mandate, changed_mandate]
        person.latest_mandates = new_mandate
        person.save()

        new_statement = DebateStatement.objects.filter(~Q(person_id = person.pk)).first()
        new_statement.person = person
        new_statement.save()

        new_inq_sent = [i for i in Inquiry.objects.all() if person not in i.sender.all()][0]
        new_inq_sent.sender = [person]
        new_inq_sent.save()

        new_inq_rec = [i for i in Inquiry.objects.all() if person != i.receiver][0]
        new_inq_rec.receiver = person
        new_inq_rec.save()

        new_inq_resp = [i for i in InquiryResponse.objects.all() if person != i.sender][0]
        new_inq_resp.sender = person
        new_inq_resp.save()

        # TODO commitee memberships

        call_command('rebuild_index', verbosity=0, interactive=False)
        check_subscriptions()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        alts = email.alternatives
        assert len(alts) == 1
        assert alts[0][1] == u'text/html'

        html_text = alts[0][0]

        assert "Es gibt Neuigkeiten" in html_text
        assert "Personen</h2>" in html_text

        assert "Barbara Streisand</a>" in html_text

        assert u"hat einen neuen Redeeintr" in html_text
        assert u"ist verstorben am: 20. 06. 2000</li>" in html_text
        assert u"hat eine neue parlamentarische Anfrage erhalten</li>" in html_text
        assert u"hat ein neues und ein ge" in html_text
        assert u"hat eine neue parlamentarische Anfrage beantwortet</li>" in html_text
        assert u"hat eine neue parlamentarische Anfrage gestellt</li>" in html_text
        assert u"hat einen neuen Beruf angegeben: Rechte Reckin</li>" in html_text

    def test_create_person_subscription(self):
        """
        Tests the creation of a single law subscription step-by-step,
        including verification
        """
        person = Person.objects.first()
        post_vars = self._get_person_subscription_post_vars(person)

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

class PersonsSubscriptionsTestCase(BasePersonSubscriptionsTestCase):

    def test_list_persons_subscriptions(self):
        subscription_item = self._prep_persons_subscription()

        user = subscription_item.user
        key = user.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/abos')
        request.user = AnonymousUser()
        response = views.list(request,self.EMAIL,key)

        assert '/unsubscribe/{}/{}'.format(self.EMAIL,subscription_item.verification.verification_hash) in response.content

    def test_delete_persons_subscription(self):
        subscription_item = self._prep_persons_subscription()

        user = subscription_item.user
        key = subscription_item.verification.verification_hash

        # Create an instance of a list GET request.
        request = self.factory.get('/unsubscribe')
        request.user = AnonymousUser()
        response = views.unsubscribe(request,self.EMAIL,key)

        assert response.__class__ == HttpResponseRedirect

    def test_process_email_empty_persons_subscription(self):
        subscription_item = self._prep_persons_subscription()

        # Test no changes
        check_subscriptions()
        assert len(mail.outbox) == 0

    def test_process_email_persons_subscription(self):
        subscription_item = self._prep_persons_subscription()
        parl_ids = [p['parl_id'] for p in subscription_item.content.get_content()]

        for parl_id in parl_ids[:2]:
            person = Person.objects.get(parl_id=parl_id)
            person.full_name = u"{}2".format(person.full_name)
            person.parl_id = u"{}2".format(person.parl_id)
            person.save()
            person.mandates = Person.objects.get(parl_id=parl_id).mandate_set.all()
            person.save()

        person = Person.objects.get(parl_id=parl_ids[-1])
        person.full_name = u"{}2".format(person.full_name)
        person.save()

        call_command('rebuild_index', verbosity=0, interactive=False)

        check_subscriptions()

        assert len(mail.outbox) == 1
        email = mail.outbox[0]
        alts = email.alternatives
        assert len(alts) == 1
        assert alts[0][1] == u'text/html'

        html_text = alts[0][0]

        assert "2 neue Ergebnisse</li>" in html_text
        assert "nderte Ergebnisse</li>" in html_text

    def test_create_persons_search_subscription(self):
        """
        Tests the creation of a single law subscription step-by-step,
        including verification
        """
        post_vars = self._get_persons_subscription_post_vars()

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

class JsonDifferPersonEqualTestCase(BasePersonSubscriptionsTestCase):
    def test_json_differ_equal(self):
        subscription_item = self._prep_person_subscription()
        differ = PersonDiffer(subscription_item.content)
        assert differ.collect_changesets() == {}

class JsonDifferPersonTestCase(BasePersonSubscriptionsTestCase):

    def test_json_differ_basic_changes(self):
        subscription_item = self._prep_person_subscription()
        parl_id = [p['parl_id'] for p in subscription_item.content.get_content()][0]
        person = Person.objects.get(parl_id=parl_id)

        # Let's test some changes on the primary items

        changes = {
            'birthdate': datetime.date(1959,6,20),
            'deathdate': datetime.date(2000,6,20),
            'full_name': "Barbara Streisand",
            'reversed_name': "Streisand, Barbara",
            'birthplace': "Buxtehude",
            'deathplace': "Wien",
            'occupation': "Rechte Reckin",
        }
        for attr in changes:
            person.__setattr__(attr, changes[attr])

        person.save()

        call_command('rebuild_index', verbosity=0, interactive=False)
        differ = PersonDiffer(subscription_item.content)

        differ.print_changesets()
        cs = differ.collect_changesets()

        # Assert that the item was flagged as having changes
        assert person.parl_id in cs
        cs = cs[parl_id]

        # Assert all our changes were reflected in the changeset
        for attr in changes:
            assert attr in cs
            if isinstance(changes[attr], datetime.date):
                assert cs[attr]['new'] == changes[attr].strftime(format='%Y-%m-%dT%H:%M:%S')
            else:
                assert cs[attr]['new'] == changes[attr]

        # Test the generated message snippets
        snippets = differ.render_snippets()

        assert u"<li>ist verstorben am: 20. 06. 2000</li>" in snippets
        assert u"<li>hat einen neuen Beruf angegeben: Rechte Reckin</li>"

    def test_json_differ_json_changes(self):
        subscription_item = self._prep_person_subscription()
        parl_id = [p['parl_id'] for p in subscription_item.content.get_content()][0]
        person = Person.objects.get(parl_id=parl_id)

        # Now let's get into the juicy part of secondary, JSON-based views

        changed_mandate = person.mandate_set.first()
        changed_mandate.end_date = datetime.date(2026,1,1)
        changed_mandate.start_date = datetime.date(2000,1,1)
        changed_mandate.save()
        new_mandate = Mandate.objects.filter(~Q(party__short = person.party.short)).all()[0]
        person.mandates = [new_mandate, changed_mandate]
        person.latest_mandates = new_mandate
        person.save()

        new_statement = DebateStatement.objects.filter(~Q(person_id = person.pk)).first()
        new_statement.person = person
        new_statement.save()

        new_inq_sent = [i for i in Inquiry.objects.all() if person not in i.sender.all()][0]
        new_inq_sent.sender = [person]
        new_inq_sent.save()

        new_inq_rec = [i for i in Inquiry.objects.all() if person != i.receiver][0]
        new_inq_rec.receiver = person
        new_inq_rec.save()

        new_inq_resp = [i for i in InquiryResponse.objects.all() if person != i.sender][0]
        new_inq_resp.sender = person
        new_inq_resp.save()

        # TODO commitee memberships

        call_command('rebuild_index', verbosity=0, interactive=False)
        differ = PersonDiffer(subscription_item.content)

        differ.print_changesets()
        cs = differ.collect_changesets()

        # Assert that the item was flagged as having changes
        assert person.parl_id in cs
        cs = cs[parl_id]

        assert 'mandates' in cs
        assert len(cs['mandates']['N']) == 1
        assert len(cs['mandates']['C']) == 1

        assert 'inquiries_sent' in cs
        assert len(cs['inquiries_sent']['N']) == 1
        assert cs['inquiries_sent']['N'][0]['sender_names'] == [person.full_name]

        assert 'inquiries_received' in cs
        assert len(cs['inquiries_received']['N']) == 1
        assert cs['inquiries_received']['N'][0]['receiver_name'] == person.full_name

        assert 'inquiries_answered' in cs
        assert len(cs['inquiries_answered']['N']) == 1
        assert cs['inquiries_answered']['N'][0]['sender_name'] == person.full_name

        assert 'debate_statements' in cs
        assert len(cs['debate_statements']['N']) == 1

        # Test the generated snippets
        snippets = differ.render_snippets()

        assert person.full_name in snippets

        assert u"<li>hat einen neuen Redeeinträg(e)</li>" in snippets
        assert u"<li>hat ein neues und ein geändertes Mandat(e)</li>" in snippets
        assert "<li>hat eine neue parlamentarische Anfrage beantwortet</li>" in snippets
        assert "<li>hat eine neue parlamentarische Anfrage gestellt</li>" in snippets
        assert "<li>hat eine neue parlamentarische Anfrage erhalten</li>" in snippets
