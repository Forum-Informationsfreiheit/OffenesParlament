from django.shortcuts import redirect
from django.contrib import messages

from op_scraper.tasks import scrape, update_elastic
from op_scraper.scraper.parlament.spiders.llp import LegislativePeriodSpider
from op_scraper.scraper.parlament.spiders.administrations import AdministrationsSpider
from op_scraper.scraper.parlament.spiders.laws_initiatives import LawsInitiativesSpider
from op_scraper.scraper.parlament.spiders.pre_laws import PreLawsSpider
from op_scraper.scraper.parlament.spiders.persons import PersonsSpider

SPIDERS = {
    'llp': LegislativePeriodSpider,
    'administrations': AdministrationsSpider,
    'persons': PersonsSpider,
    'pre_laws': PreLawsSpider,
    'laws': LawsInitiativesSpider
}


def trigger_scrape(request, spider_name):
    messages.success(
        request, 'Scraping of {} triggered. Awesomeness ensues.'.format(spider_name))
    scrape.delay(SPIDERS[spider_name])

    return redirect('/admin/')

def trigger_reindex(request):
    """
    Triggers an index update for ElasticSearch
    """
    messages.success(
        request, 'Updating ElasticSearch Index triggered! Awesomeness ensues.')
    update_elastic.delay()
    return redirect('/admin/')

