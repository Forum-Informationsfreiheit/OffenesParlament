# -*- coding: utf-8 -*-
import scrapy
import feedparser

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from urllib import urlencode

from scrapy import log

from parlament.settings import BASE_HOST
from parlament.spiders import BaseScraper
from parlament.resources.extractors import *
from parlament.resources.util import _clean


from op_scraper.models import Party
from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate


class PersonsSpider(BaseScraper):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/SUCHE/filter.psp")

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/WWER/SUCHE/index.shtml',
        'NAME_TYP_ID': '1201',
        'NAME': '',
        'R_ZEIT': 'ALLE',
        'listeId': '1',
        'LISTE': 'Suchen',
        'FBEZ': 'FW_001',
    }

    name = "persons"

    def __init__(self, **kw):
        super(PersonsSpider, self).__init__(**kw)

        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Overwritten from BaseSpider for non-LLP-based retrieval
        """
        url_options = urlencode(self.URLOPTIONS)
        urls = ["{}?{}".format(self.BASE_URL, url_options)]

        return urls

    def parse(self, response):
        rss = feedparser.parse(response.url)

        callback_requests = []

        log.msg("Scraping {} persons".format(len(rss.entries)))

        # Iterate all persons
        for entry in rss.entries:
            # Extract basic data
            reversed_name = entry['title']
            source_link = entry['link']
            parl_id = source_link.split('/')[-2]
            functions = _clean(
                entry['summary'].split('<br />')[1], to_remove=['Funktion:'])

            # Extract current Party
            raw_parties = _clean(
                entry['summary'].split('<br />')[2], to_remove=['Fraktion:'])
            parties = PERSON.PARTY.xt(Selector(text=raw_parties))
            # Supposedly, last entry in parties list is current one
            party = parties[-1]

            party_item, created = Party.objects.get_or_create(
                short=party[0])
            if created:
                log.msg(u"Created party {}".format(
                    green(u'[{}]'.format(party_item.short))))
            titles = party_item.titles
            if party[1] not in titles:
                titles.append(party[1])
                party_item.titles = titles
            party_item.save()

            # Create Detail Page request
            req = scrapy.Request(source_link,
                                 callback=self.parse_person_detail)
            req.meta['person'] = {
                'reversed_name': reversed_name,
                'source_link': source_link,
                'parl_id': parl_id,
                'party': party_item
            }
            callback_requests.append(req)

        return callback_requests

    def parse_person_detail(self, response):
        """
        Parse a persons detail page before creating the person object
        """
        person = response.meta['person']

        full_name = PERSON.DETAIL.FULL_NAME.xt(response)
        bio_data = PERSON.DETAIL.BIO.xt(response)
        mandates = PERSON.DETAIL.MANDATES.xt(response)
        profile_photo_url = PERSON.DETAIL.PHOTO_URL.xt(response)
        try:
            person_item, created = Person.objects.update_or_create(
                source_link=person['source_link'],
                photo_link=profile_photo_url,
                parl_id=person['parl_id'],
                full_name=full_name,
                reversed_name=person['reversed_name'],
                birthdate=bio_data['birthdate'],
                birthplace=bio_data['birthplace'],
                deathdate=bio_data['deathdate'],
                deathplace=bio_data['deathplace'],
                occupation=bio_data['occupation'],
                party=person['party']
            )
            person_item.save()
        except:
            log.msg(red("Error saving Person {}".format(full_name)))
            import ipdb
            ipdb.set_trace()
            return

        mandate_items = []
        for mandate in mandates:
            function_item, f_created = Function.objects.get_or_create(
                title=mandate['function'])
            try:
                fun_party = Party.objects.get(short=mandate['party'])
            except:
                fun_party = None
            try:
                mandate_item, m_created = Mandate.objects.update_or_create(
                    function=function_item,
                    party=fun_party,
                    start_date=mandate['start_date'],
                    end_date=mandate['end_date']
                )
            except:
                log.msg(
                    red("Error saving Mandate {}".format(mandate['function'])))
                import ipdb
                ipdb.set_trace()
            mandate_items.append(mandate_item)

        person_item.mandates = mandate_items
        person_item.save()

        log.msg(u"Created Person {}".format(
            green(u"[{}]".format(full_name))
        ))
