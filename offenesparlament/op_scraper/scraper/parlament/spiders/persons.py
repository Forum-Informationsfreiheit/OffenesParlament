# -*- coding: utf-8 -*-
import scrapy
import feedparser

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from urllib import urlencode

from parlament.settings import BASE_HOST
from parlament.spiders import BaseScraper
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *

from parlament.resources.util import _clean


from op_scraper.models import Party
from op_scraper.models import State
from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate
from op_scraper.models import LegislativePeriod


class PersonsSpider(BaseScraper):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/PARL/filter.psp")

    # URLOPTIONS = {
    #     'view': 'RSS',
    #     'jsMode': 'RSS',
    #     'xdocumentUri': '/WWER/SUCHE/index.shtml',
    #     'NAME_TYP_ID': '1201',
    #     'NAME': '',
    #     'R_ZEIT': 'ALLE',
    #     'listeId': '1',
    #     'LISTE': 'Suchen',
    #     'FBEZ': 'FW_001',
    # }

    RSS_TO_FUNCTION = {
        'NR': 'Abgeordnete(r) zum Nationalrat',
        'BR': 'Abgeordnete(r) zum Bundesrat'
    }

    # URLOPTIONS_NR = {
    # 'view': 'RSS',
    # 'jsMode': 'RSS',
    #     'xdocumentUri': '/WWER/PARL/index.shtml',
    #     'NRBR': 'NR',
    #     'anwenden': 'Anwenden',
    #     'GP': '',
    #     'R_WF': 'WP',
    #     'FR': 'ALLE',
    #     'W': 'W',
    #     'M': 'M',
    #     'listeId': '8',
    #     'FBEZ': 'FW_008'
    # }
    URLOPTIONS_NR = {
        'xdocumentUri': '/WWER/PARL/index.shtml',
        'PR': '',
        'R_BW': 'BL',
        'anwenden': 'Anwenden',
        'GP': '',
        'BL': 'ALLE',
        'STEP': ' ',
        'FR': 'ALLE',
        'M': 'M',
        'NRBR': 'NR',
        'FBEZ': 'FW_008',
        'view': '',
        'WK': 'ALLE',
        'jsMode': '',
        'LISTE': '',
        'W': 'W',
        'letter': '',
        'WP': 'ALLE',
        'listeId': '8',
        'R_WF': 'WP'
    }

    name = "persons"
    persons_scraped = []

    def __init__(self, **kw):
        super(PersonsSpider, self).__init__(**kw)

        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Overwritten from BaseSpider for non-LLP-based retrieval
        """
        urls = []
        for llp in LegislativePeriod.objects.all():
            urloptions = self.URLOPTIONS_NR.copy()
            urloptions['GP'] = llp.roman_numeral
            url_options = urlencode(urloptions)
            url = "{}?{}".format(self.BASE_URL, url_options)
            urls.append(url)

        return urls

    def parse(self, response):

        # rss = feedparser.parse(response.url)

        persons = PERSON.LIST.xt(response)

        callback_requests = []

        # which llp are we in?
        urloptions = response.url.split('?')[1]

        llp_roman = [opt.split('=')[1]
                     for opt in urloptions.split('&') if opt.split('=')[0] == 'GP']
        llp_item = LegislativePeriod.objects.get(roman_numeral=llp_roman[0])

        # function string
        function = [opt.split('=')[1]
                    for opt in urloptions.split('&') if opt.split('=')[0] == 'NRBR']
        function_str = self.RSS_TO_FUNCTION[function[0]]
        function_item, f_created = Function.objects.get_or_create(
            title=function_str)

        self.logger.info(
            "Scraping {} persons for LLP {}".format(len([persons]), llp_roman))

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

            for mandate in p['mandates']:
                party_item = self.get_party_item(mandate)
                state_item = self.get_state_item(p['electoral_state'])
                # Create and append mandate
                try:
                    mandate_item, m_created = Mandate.objects.update_or_create(
                        function=function_item,
                        legislative_period=llp_item,
                        party=party_item,
                        state=state_item)
                except:
                    self.logger.info(
                        red("Error saving Mandate {} ({})".format(function_item, party_item)))
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

    def get_party_item(self, mandate):
        # Do we have this party already?
        party_item, created = Party.objects.update_or_create(
            short=mandate['short'])

        titles = party_item.titles
        if mandate['title'] not in titles:
            titles.append(mandate['title'])
            party_item.titles = titles
            party_item.save()

        if created:
            self.logger.info(u"Created party {}".format(
                green(u'[{}]'.format(party_item.short))))

        return party_item

    def get_state_item(self, state):
        # Do we have this party already?
        state_item, created = State.objects.update_or_create(
            name=state['short'],
            title=state['long'])

        if created:
            state_item.save()

            self.logger.info(u"Created state {}: '{}'".format(
                green(u'[{}]'.format(state_item.name)),
                state_item.title))

        return state_item

    def parse_person_detail(self, response):
        """
        Parse a persons detail page before creating the person object
        """
        person = response.meta['person']
        self.logger.info(u"Updating Person Detail {}".format(
            green(u"[{}]".format(person['reversed_name']))
        ))

        full_name = PERSON.DETAIL.FULL_NAME.xt(response)
        bio_data = PERSON.DETAIL.BIO.xt(response)

        profile_photo_url = PERSON.DETAIL.PHOTO_URL.xt(response)
        profile_photo_copyright = PERSON.DETAIL.PHOTO_COPYRIGHT.xt(response)
        try:
            person_data = {
                'photo_link': "{}{}".format(BASE_HOST, profile_photo_url),
                'photo_copyright': profile_photo_copyright,
                'full_name': full_name,
                'reversed_name': person['reversed_name'],
                'birthdate': bio_data['birthdate'],
                'birthplace': bio_data['birthplace'],
                'deathdate': bio_data['deathdate'],
                'deathplace': bio_data['deathplace'],
                'occupation': bio_data['occupation']}

            person_item, created_person = Person.objects.update_or_create(
                source_link=person['source_link'],
                parl_id=person['parl_id'],
                defaults=person_data
            )
            person_item.save()
        except:
            self.logger.info(red("Error saving Person {}".format(full_name)))
            import ipdb
            ipdb.set_trace()
            return
