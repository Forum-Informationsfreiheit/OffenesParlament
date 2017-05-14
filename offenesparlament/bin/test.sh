#!/bin/bash
env DJANGO_CONFIGURATION=UnitTest python manage.py test op_scraper.tests.test_subscriptions.JsonDifferTestCase