# -*- coding: utf-8 -*-
import scrapy
import feedparser
import roman
from urllib import urlencode

from ansicolor import green, red

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
from parlament.resources.extractors.statement import *

from op_scraper.models import DebateStatement, Debate
from op_scraper.models import Person, LegislativePeriod

import datetime

import json


class StatementSpider(BaseSpider):

    """
    Spider to scrape debates and debate statements
    ----------------------------------------------

    Start the spider by specifying `llp` and `type` parameters.

    First step is to get urls of debate-transcripts ("stenographische
    protokolle"), for this, the RSS-Feed at
    `http://www.parlament.gv.at/PAKT/STPROT/` is used.

    Parameters are `type` (NR, BR) and `llp` (as roman number) for type of
    debate and llp respectively; and use `snr` to scrape only a single
    debate ("sitzung")::

        ./manage.py scrape crawl statement -a llp=XXIV -a type=NR

    or just for one debate ::

        ./manage.py scrape crawl statement -a llp=XXIV -a type=NR\
        -a snr=171


    """

    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/STPROT/")

    ALLOWED_LLPS = range(20, 26)

    name = "statement"

    def __init__(self, **kw):
        super(StatementSpider, self).__init__(**kw)

        self.DEBATETYPE = kw['type'] if 'type' in kw else 'NR'
        if 'llp' in kw:
            try:
                self.LLP = roman.toRoman(int(kw['llp']))
            except:
                self.LLP = kw['llp']
        else:
            self.LLP = 'XXIII'

        self.SNR = kw['snr'] if 'snr' in kw else None

        self.start_urls = [self.BASE_URL]

    def parse(self, response):
        """
        Starting point from which to parse or statically provide
        debate-list urls (rss feeds)
        """

        callback_requests = []

        params = {'NRBRBV': self.DEBATETYPE,
                  'GP': self.LLP,
                  'view': 'RSS',
                  'jsMode': 'RSS',
                  'xdocumentUri': '/PAKT/STPROT/',
                  'NUR_VORL': 'N',
                  'R_PLSO': 'PL',
                  'FBEZ': 'FP_011',
                  # 'listeId': '',
                  }

        llp = None
        try:
            llp = LegislativePeriod.objects.get(roman_numeral=params['GP'])
        except LegislativePeriod.DoesNotExist:
            self.logger.warning(
                red(u"LLP '{}' not found".format(params['GP'])))
        callback_requests.append(
            scrapy.Request(self.BASE_URL + '?' + urlencode(params),
                           callback=self.parse_debatelist,
                           meta={'llp': llp, 'type': params['NRBRBV']}))

        return callback_requests

    def parse_debatelist(self, response):
        """
        Parse list of debates
        """

        llp = response.meta['llp'] if 'llp' in response.meta else None
        debate_type = response.meta['type'] \
            if 'type' in response.meta else ''
        debates = RSS_DEBATES.xt(response)
        self.logger.info(green(u"{} debates from {}".format(len(debates),
                                                            response.url)))

        # If SNR is set, use only a subset of debates for further parsing
        fetch_debates = filter(lambda r: r['protocol_url'] != "" and
                               (not self.SNR or self.SNR in r['title']),
                               debates)

        for debate in fetch_debates:
            debate['llp'] = llp
            debate['debate_type'] = debate_type
            debate_item = self.store_debate(debate)
            yield scrapy.Request(BASE_HOST + debate['protocol_url'],
                                 callback=self.parse_debate,
                                 meta={'debate': debate_item})

    def parse_debate(self, response):
        """
        Debate-transcript ("Stenografisches Protokoll") parser
        """

        for i, sect in enumerate(DOCSECTIONS.xt(response)):
            # Lookup + add references to the section data
            sect['debate'] = response.meta['debate']
            if 'speaker_id' in sect and sect['speaker_id'] is not None:
                try:
                    sect['speaker'] = Person.objects.get(
                        parl_id=sect['speaker_id'])
                except Person.DoesNotExist:
                    self.logger.warning(
                        red(u"Person '{}' not found".format(sect['speaker_id'])))

            if sect['ref_timestamp'] is not None \
                    and len(sect['ref_timestamp']) == 2:
                sect['date'] = sect['debate'].date.replace(
                    minute=sect['ref_timestamp'][0],
                    second=sect['ref_timestamp'][1])

            self.store_statement(sect, i)

        self.logger.info(
            green(u"Saved {} sections from {}".format(i, response.url)))

    def store_debate(self, data):
        """
        Save (update or insert) debate to ORM
        """
        try:
            debate = Debate.objects.get(llp=data['llp'], nr=data['nr'])
        except Debate.DoesNotExist:
            debate = Debate()
        for (key, value) in data.items():
            setattr(debate, key, value)
        debate.save()
        self.logger.info(green(u"Debate metadata saved {}".format(debate)))
        return debate

    def store_statement(self, data, index=-1):
        """
        Save (update or insert) debate_statement to ORM
        """
        data['index'] = index
        data['debugdump'] = json.dumps([data[k] for k in ['links',
                                                          'ref_timestamp']])
        try:
            debate_statement = DebateStatement.objects.get(
                debate=data['debate'], doc_section=data['doc_section'])
        except DebateStatement.DoesNotExist:
            debate_statement = DebateStatement()
        keys = set(data.keys()) &\
            set([v.name for v in DebateStatement._meta.get_fields()])
        for key in keys:
            setattr(debate_statement, key, data[key])
        debate_statement.save()
