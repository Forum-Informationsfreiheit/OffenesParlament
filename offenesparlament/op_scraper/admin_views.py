from django.shortcuts import redirect
from django.contrib import messages

from op_scraper.tasks import scrape
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


def trigger_llp_scrape(request, spider_name):
    messages.success(
        request, 'Scraping of {} triggered. Awesomeness ensues.'.format(spider_name))
    scrape.delay(SPIDERS[spider_name])

    return redirect('/admin/')
