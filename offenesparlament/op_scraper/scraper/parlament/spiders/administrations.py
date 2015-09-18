# -*- coding: utf-8 -*-
import scrapy

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from urllib import urlencode

from parlament.settings import BASE_HOST
from parlament.spiders.persons import PersonsSpider
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.resources.extractors.administration import *

from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate
from op_scraper.models import Administration


class AdministrationsSpider(PersonsSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/BREG/REG/filter.psp")

    URLOPTIONS_ADMIN = {
        'jsMode': '',
        'xdocumentUri': '/WWER/BREG/REG/index.shtml',
        'REG': '0',
        'anwenden': 'Anwenden',
        'FUNK': 'ALLE',
        'RESS': 'ALLE',
        'SUCH': '',
        'listeId': '16',
        'FBEZ': 'FW_016',
        'pageNumber': '',
    }

    name = "administration"
    persons_scraped = []

    def __init__(self, **kw):
        super(AdministrationsSpider, self).__init__(**kw)
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Overwritten from BaseSpider for non-LLP-based retrieval
        """
        urls = []
        url_options = urlencode(self.URLOPTIONS_ADMIN)
        url = "{}?{}".format(self.BASE_URL, url_options)
        urls.append(url)

        return urls

    def parse(self, response):
        persons = ADMINISTRATION.LIST.xt(response)
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
                self.logger.info(u"Created Person {}".format(
                    green(u'[{}]'.format(p['reversed_name']))))
            else:
                self.logger.info(u"Updated Person {}".format(
                    green(u"[{}]".format(p['reversed_name']))
                ))

            mandate = p['mandate']
            administration_item = self.get_administration_item(mandate)

            function_item, f_created = Function.objects.get_or_create(
                short=mandate['short'],
                title=mandate['title'])

            if f_created:
                self.logger.info(u"Created function {}".format(
                    green(u'[{}]'.format(function_item.short))))

            # Create and append mandate
            try:
                mandate_item, m_created = Mandate.objects.update_or_create(
                    function=function_item,
                    administration=administration_item)
            except:
                self.logger.info(
                    red("Error saving Mandate {} ({})".format(function_item, administration_item)))
                import ipdb
                ipdb.set_trace()

            person_item.mandates.add(mandate_item)
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

    def get_administration_item(self, mandate):
        # Do we have this administration already?
        admin_data = {
            'start_date': mandate['administration']['start_date'],
            'end_date': mandate['administration']['end_date']
        }
        admin_item, created = Administration.objects.update_or_create(
            title=mandate['administration']['title'],
            defaults=admin_data)

        if created:
            admin_item.save()
            self.logger.info(u"Created administration {}".format(
                green(u'[{}]'.format(admin_item.title))))

        return admin_item
