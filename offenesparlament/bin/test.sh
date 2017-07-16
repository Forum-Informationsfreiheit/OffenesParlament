#!/bin/bash
#env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_law.LawsSubscriptionsTestCase.test_process_email_laws_subscription
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_person.PersonsSubscriptionsTestCase.test_process_email_persons_subscription

# env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests

# env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_person