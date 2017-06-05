# -*- coding: UTF-8 -*-
import datetime
 
from op_scraper.models import *
from op_scraper.subscriptions import JsonDiffer, PersonDiffer, LawDiffer, DebateDiffer, SearchDiffer
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
            'subscription_url': '/personen/search?llps=XXV&type=Personen&party=%C3%96VP',
            'search_ui_url': '/personen/search?llps=XXV&type=Personen&party=%C3%96VP',
            'subscription_title': u'Personen in Periode XXV: ÖVP',
            'email': self.EMAIL
        }

class JsonDifferPersonEqualTestCase(BasePersonSubscriptionsTestCase):
    def test_json_differ_equal(self):
        subscription_item = self._prep_person_subscription()
        differ = JsonDiffer(subscription_item.content)
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
              
        changed_mandate = person.mandates.first()
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
