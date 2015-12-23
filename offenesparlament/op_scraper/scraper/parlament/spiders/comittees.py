# -*- coding: utf-8 -*-
import scrapy

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue
from ansicolor import magenta

import feedparser
import roman
from urllib import urlencode

from scrapy import log

from parlament.spiders import BaseSpider

from parlament.resources.extractors.comittee import *

from parlament.settings import BASE_HOST

from op_scraper.models import Comittee
from op_scraper.models import ComitteeMeeting
from op_scraper.models import ComitteeAgendaTopic
from op_scraper.models import LegislativePeriod
from op_scraper.models import Document
from op_scraper.models import Law


class ComitteesSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/AUS/filter.psp")

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/AUS/index.shtml',
        'NRBR': '',
        'anwenden': 'Anwenden',
        'BBET': '',
        'SUCH': '',
        'listeId': '109',
        'FBEZ': 'FP_009',
        'UA': 'J',
    }

    name = "comittees"
    title = "Comittees Spider"

    def __init__(self, **kw):
        super(ComitteesSpider, self).__init__(**kw)

        if 'llp' in kw:
            try:
                self.LLP = [int(kw['llp'])]
            except:
                pass

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Returns a list of URLs to scrape
        """
        urls = []
        # NR comittees are LLP based
        if self.LLP:
            for i in self.LLP:
                roman_numeral = roman.toRoman(i)
                options = self.URLOPTIONS.copy()
                options['GP'] = roman_numeral
                options['NRBR'] = 'NR'
                url_options = urlencode(options)
                url_llp = "{}?{}".format(self.BASE_URL, url_options)
                rss = feedparser.parse(url_llp)

                print "GP {}: NR: {} Comittees".format(
                    roman_numeral, len(rss['entries']))
                urls = urls + [entry['link'] for entry in rss['entries']]

        # AKT = aktiv, AUF = aufgeloest
        for aktauf in ['AKT','AUF']:
            options['NRBR'] = 'BR'
            options['R_AKTAUF'] = aktauf
            url_options = urlencode(options)
            url_br = "{}?{}".format(self.BASE_URL, url_options)
            rss = feedparser.parse(url_br)

            print "BR {}: {} Comittees".format(
                aktauf, len(rss['entries']))
            urls = urls + [entry['link'] for entry in rss['entries']]

        return urls

    def parse(self, response):
        # Parse
        parl_id = COMITTEE.url_to_parlid(response.url)[1]
        llp = COMITTEE.LLP.xt(response)
        name = COMITTEE.NAME.xt(response)

        if llp is not None:
            nrbr = 'Nationalrat'
            legislative_period = LegislativePeriod.objects.get(roman_numeral=llp)
            # NR comittees are "active" if they are in the current LLP
            active = (legislative_period == LegislativePeriod.objects.get_current())
        else:
            nrbr = 'Bundesrat'
            legislative_period = None
            # BR comittees are active if they are not "aufgelöst"
            active = COMITTEE.ACTIVE.xt(response)

        # main-comittee parl_id starts with the number 1
        # sub-comittees parl_id start  with the number 2
        if not parl_id.startswith(u'(1/'):
            try:
                parent_parl_id = u'(1/{}'.format(parl_id.split('/')[1])
                parent_comitee = Comittee.objects.get(parl_id=parent_parl_id,legislative_period=legislative_period)
            except Comittee.DoesNotExist:
                parent_comitee = None
        else:
            parent_comitee = None

        # Log our progress
        logtext = u"Scraping {} with id {}, LLP {} @ {}".format(
            red(name),
            magenta(u"[{}]".format(parl_id)),
            green(str(llp)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        description = COMITTEE.DESCRIPTION.xt(response)

        comittee_data = {
            'description': description,
            'name': name,
            'source_link': response.url,
            'parent_comittee': parent_comitee,
            'active': active
        }

        try:
            comittee_item, created_comittee = Comittee.objects.update_or_create(
                parl_id=parl_id,
                legislative_period=legislative_period,
                nrbr=nrbr,
                defaults=comittee_data
            )
        except:
            import ipdb
            ipdb.set_trace()

        meetings = COMITTEE.MEETINGS.xt(response)

        comittee_laws = []

        for meeting in meetings:
            agenda_data = meeting['agenda']
            if agenda_data is not None:
                agenda_item, agenda_created = Document.objects.get_or_create(**agenda_data)
            else:
                agenda_item = None

            meeting_data = {
                'agenda': agenda_item
            }

            # Log our progress
            logtext = u"Scraping meeting no. {} of {} on {}".format(
                red(meeting['number']),
                magenta(name),
                green(str(meeting['date'].date())),
            )
            log.msg(logtext, level=log.INFO)

            meeting_item, meeting_created = ComitteeMeeting.objects.update_or_create(
                number=meeting['number'],
                date=meeting['date'],
                comittee=comittee_item,
                defaults=meeting_data
            )

            for topic in meeting['topics']:
                if topic['law'] is not None:
                    law = topic['law']
                    law_item = self.parse_law(law)
                    if law_item is not None:
                        comittee_laws.append(law_item)
                else:
                    law_item = None

                agenda_topic_data = {
                    'text': topic['text'],
                    'comment': topic['comment'],
                    'law': law_item,
                }

                agenda_topic_item, agenda_topic_created = ComitteeAgendaTopic.objects.update_or_create(
                    number=topic['number'],
                    meeting=meeting_item,
                    defaults=agenda_topic_data,
                )

        # parse Verhandlungsgegenstaende and Veroeffentlichungen
        laws_and_reports = COMITTEE.LAWS.xt(response)

        for law in laws_and_reports:
            # Log our progress
            logtext = u"Adding law with id {}, LLP {} to {}".format(
                magenta(u"[{}]".format(law['parl_id'])),
                green(law['llp']),
                blue(name)
            )
            log.msg(logtext, level=log.INFO)

            law_item = self.parse_law(law)
            if law_item is not None:
                comittee_laws.append(law_item)

        comittee_item.laws.add(*comittee_laws)
        comittee_item.save()

    def parse_law(self, law_dict):
        try:
            law_legislative_period = LegislativePeriod.objects.get(roman_numeral=law_dict['llp'])
        except LegislativePeriod.DoesNotExist:
            law_legislative_period = None

        try:
            law_item = Law.objects.get(legislative_period=law_legislative_period,parl_id=law_dict['parl_id'])
        except Law.DoesNotExist:
            law_item = None

        return law_item
