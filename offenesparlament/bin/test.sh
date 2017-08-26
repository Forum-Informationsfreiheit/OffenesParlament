#!/bin/bash

## Law and Laws
# env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_law
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_law.LawSubscriptionsTestCase.test_process_email_law_subscription
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_law.LawsSubscriptionsTestCase.test_process_email_laws_subscription

## Person and Persons
# env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_person
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_person.PersonSubscriptionsTestCase.test_process_email_person_subscription
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions_person.PersonsSubscriptionsTestCase.test_process_email_persons_subscription

## All tests
# env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests

