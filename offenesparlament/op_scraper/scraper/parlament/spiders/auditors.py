# -*- coding: utf-8 -*-
import scrapy

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from urllib import urlencode

from parlament.settings import BASE_HOST
from parlament.spiders.administrations import AdministrationsSpider
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.resources.extractors.auditors import *

from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate
from op_scraper.models import Administration


class AuditorsSpider(AdministrationsSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/RH/filter.psp")
    URLOPTIONS_ADMIN = {
        'jsMode': '',
        'xdocumentUri': '/WWER/RH/index.shtml',
        'FBEZ': 'FW_009',
    }

    LLP = []

    name = "auditors"
    title = "RechnungshofpräsidentInnen Spider"
    persons_scraped = []

    def __init__(self, **kw):
        super(AuditorsSpider, self).__init__(**kw)
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

        self.print_debug()

    def parse(self, response):
        persons = AUDITORS.LIST.xt(response)
        callback_requests = []

        self.logger.info(
            "Scraping {} persons".format(len(persons)))

        # Iterate all persons
        for p in persons:
            # Extract basic data
            parl_id = p['source_link'].split('/')[-2]
            p['source_link'] = "{}{}".format(BASE_HOST, p['source_link'])

            # Create or update simple person's item
            person_data = {
                'reversed_name': p['reversed_name']
            }
            person_item, created_person = Person.objects.update_or_create(
                source_link=p['source_link'],
                parl_id=parl_id,
                defaults=person_data
            )
            if created_person:
                self.logger.debug(u"Created Person {}".format(
                    green(u'[{}]'.format(p['reversed_name']))))
            else:
                self.logger.debug(u"Updated Person {}".format(
                    green(u"[{}]".format(p['reversed_name']))
                ))

            mandate = p['mandate']

            function_item, f_created = Function.objects.get_or_create(
                short=mandate['short'],
                title=mandate['title'])

            if f_created:
                self.logger.debug(u"Created function {}".format(
                    green(u'[{}]'.format(function_item.short))))

            # Create and append mandate
            try:
                mandate_item, m_created = Mandate.objects.update_or_create(
                    person=person_item,
                    function=function_item,
                    start_date=mandate['start_date'],
                    end_date=mandate['end_date'])
            except:
                self.logger.warning(
                    red("Error saving Mandate {} ({} - {})".format(function_item, start_date, end_date)))
                import ipdb
                ipdb.set_trace()

            person_item.save()

            # First time we encounter a person, we scan her detail page too
            if not parl_id in self.persons_scraped:

                # Create Detail Page request
                req = scrapy.Request(p['source_link'],
                                     callback=self.parse_person_detail)
                req.meta['person'] = {
                    'reversed_name': p['reversed_name'],
                    'source_link': p['source_link'],
                    'parl_id': parl_id
                }
                callback_requests.append(req)
                self.persons_scraped.append(parl_id)
        return callback_requests
