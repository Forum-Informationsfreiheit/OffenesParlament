# -*- coding: UTF-8 -*-
from op_scraper.models import *
from offenesparlament.views import subscriptions as views

from django.contrib.auth.models import AnonymousUser, User
from django.test import TransactionTestCase, TestCase, RequestFactory
from django.core.management import call_command
from django.core import mail
from django.http.response import HttpResponseRedirect

from django.db import transaction

class BaseSubscriptionTestCase(TestCase):

    fixtures = ['categories', 'llps', 'persons', 'laws']
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