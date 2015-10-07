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
from parlament.resources.extractors.petition import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.opinion import *

from parlament.settings import BASE_HOST
from parlament.resources.util import _clean

from op_scraper.models import LegislativePeriod
from op_scraper.models import Petition
from op_scraper.models import Law
from op_scraper.models import Category
from op_scraper.models import Phase
from op_scraper.models import Opinion
from op_scraper.models import Keyword
from op_scraper.models import Document
from op_scraper.models import Entity
from op_scraper.models import Step


class PetitionsSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/BB/filter.psp")

    #http://www.parlament.gv.at/PAKT/BB/filter.psp?xdocumentUri=%2FPAKT%2FBB%2Findex.shtml&NRBR=NR&anwenden=Anwenden&GP=XXV&BBET=ALLE&SUCH=&listeId=104&FBEZ=FP_004&pageNumber=

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/BB/index.shtml',
        'NRBR': '',
        'anwenden': 'Anwenden',
        'BBET': '',
        'SUCH': '',
        'listeId': '104',
        'FBEZ': 'FP_004',
    }

    name = "petitions"

    def __init__(self, **kw):
        super(PetitionsSpider, self).__init__(**kw)

        if 'llp' in kw:
            try:
                self.LLP = [int(kw['llp'])]
            except:
                pass

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        #import ipdb
        #ipdb.set_trace()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Returns a list of URLs to scrape
        """
        urls = []
        if self.LLP:
            for i in self.LLP:
                for nrbr in ['NR', 'BR']:
                    for bbet in ['BI', 'PET', 'VOLKBG']:
                        roman_numeral = roman.toRoman(i)
                        options = self.URLOPTIONS.copy()
                        options['GP'] = roman_numeral
                        options['NRBR'] = nrbr
                        options['BBET'] = bbet
                        url_options = urlencode(options)
                        url_llp = "{}?{}".format(self.BASE_URL, url_options)
                        rss = feedparser.parse(url_llp)

                        print "GP {}: {}: {} {}".format(
                            roman_numeral, nrbr, len(rss['entries']), bbet)
                        urls = urls + [entry['link'] for entry in rss['entries']]

        # urls = ['http://www.parlament.gv.at/PAKT/VHG/XXIV/PET/PET_00030/index.shtml']
        return urls

    def parse(self, response):
        # Extract fields
        title = LAW.TITLE.xt(response)
        parl_id = LAW.PARL_ID.xt(response)
        LLP = LegislativePeriod.objects.get(
            roman_numeral=response.url.split('/')[-4])

        # save ids and stuff for internals
        if LLP not in self.idlist:
            self.idlist[LLP] = {}
        self.idlist[LLP][response.url] = [parl_id, LLP]

        # Extract foreign keys
        category = self.parse_category(response)
        description = LAW.DESCRIPTION.xt(response)

        # Log our progress
        logtext = u"Scraping {} with id {}, LLP {} @ {}".format(
            red(title),
            magenta(u"[{}]".format(parl_id)),
            green(str(LLP)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        # Create and save Law
        law_item, created = Law.objects.get_or_create(
            title=title,
            parl_id=parl_id,
            source_link=response.url,
            description=description,
            legislative_period=LLP)

        if not created:
            law_item.save()

        # Attach foreign keys
        law_item.keywords = self.parse_keywords(response)
        law_item.category = category
        law_item.documents = self.parse_docs(response)

        law_item.save()

        signing_url, signable = PETITION.SIGNING.xt(response)

        # Create and save Petition
        petition_item, petition_item_created = Petition.objects.get_or_create(
            law=law_item,
            signable=signable,
            signing_url=signing_url,
        )

        if not petition_item_created:
            petition_item.save()

        # Parse opinions
        opinions = PETITION.OPINIONS.xt(response)

        callback_requests = []

        # is the tab 'Parlamentarisches Verfahren available?'
        if opinions:
            for op in opinions:
                if Opinion.objects.filter(parl_id=op['parl_id']).exists():
                    continue
                post_req = scrapy.Request("{}/{}".format(BASE_HOST, op['url']),
                                          callback=self.parse_opinion,
                                          dont_filter=True)
                post_req.meta['law_item'] = law_item
                post_req.meta['op_data'] = op

                callback_requests.append(post_req)

        log.msg(green("Open Callback requests: {}".format(
            len(callback_requests))), level=log.INFO)

        return callback_requests

    def parse_keywords(self, response):
        """
        Parse this pre-law's keywords
        """

        keywords = LAW.KEYWORDS.xt(response)

        # Create all keywords we don't yet have in the DB
        keyword_items = []
        for keyword in keywords:
            kw, created = Keyword.objects.get_or_create(title=keyword)
            if created:
                log.msg(u"Created keyword {}".format(
                    green(u'[{}]'.format(keyword))))
            keyword_items.append(kw)

        return keyword_items

    def parse_docs(self, response):
        """
        Parse the documents attached to this pre-law
        """

        docs = LAW.DOCS.xt(response)

        # Create all docs we don't yet have in the DB
        doc_items = []
        for document in docs:
            doc, created = Document.objects.get_or_create(
                title=document['title'],
                html_link=document['html_url'],
                pdf_link=document['pdf_url'],
                stripped_html=None
            )
            doc_items.append(doc)
        return doc_items

    def parse_category(self, response):
        category = LAW.CATEGORY.xt(response)

        # Create category if we don't have it yet
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        return cat

    def parse_opinion(self, response):
        """
        Parse one pre-law opinion
        """
        op_data = response.meta['op_data']

        parl_id = LAW.PARL_ID.xt(response)

        description = LAW.DESCRIPTION.xt(response)
        docs = self.parse_docs(response)
        category = self.parse_category(response)
        keywords = self.parse_keywords(response)
        entity = OPINION.ENTITY.xt(response)
        entity['title'] = op_data['title'] or entity['title_detail']
        entity['title_detail'] = entity['title_detail']
        entity['email'] = entity['email'] or op_data['email']

        entity_item, created = Entity.objects.get_or_create(
            title=entity['title'],
            title_detail=entity['title_detail']
        )

        if entity['phone'] and not entity_item.phone:
            entity_item.phone = entity['phone']
        if entity['email'] and not entity_item.email:
            entity_item.email = entity['email']

        opinion_item, created = Opinion.objects.get_or_create(
            parl_id=parl_id,
            defaults={
                'description': description,
                'source_link': response.url,
                'entity': entity_item,
                'prelaw': response.meta['law_item'],
                'category': category
            }
        )

        # Foreign Keys
        opinion_item.documents = docs
        opinion_item.keywords = keywords

        response.meta['opinion'] = opinion_item
        step_num = self.parse_op_steps(response)

        entity_str = u"{} / {} / {} [{}]".format(
            green(entity_item.title_detail),
            entity_item.phone,
            entity_item.email,
            'new' if created else 'updated')

        log.msg(
            u"Opinion: {} by {}".format(
                magenta(opinion_item.parl_id),
                entity_str
            ))

    def parse_steps(self, response):
        """
        Parse the Pre-Law's steps
        """
        law_item = response.meta['law_item']

        # Create phase if we don't have it yet
        phase_item, created = Phase.objects.get_or_create(
            title='default')
        if created:
            log.msg(u"Created Phase {}".format(
                green(u'[{}]'.format(phase_item.title))))

        steps = PRELAW.STEPS.xt(response)
        if steps:
            log.msg(u"Creating {} steps".format(
                cyan(u'[{}]'.format(len(steps)))))

        # Create steps
        for step in steps:
            step_item, created = Step.objects.update_or_create(
                title=step['title'],
                sortkey=step['sortkey'],
                date=step['date'],
                protocol_url=step['protocol_url'],
                law=law_item,
                phase=phase_item,
                source_link=response.url
            )
            step_item.save()

    def parse_op_steps(self, response):
        """
        Parse the Opinions's steps
        """

        opinion = response.meta['opinion']

        # Create phase if we don't have it yet
        phase_item, created = Phase.objects.get_or_create(
            title='default_op')
        if created:
            log.msg(u"Created Phase {}".format(
                green(u'[{}]'.format(phase_item.title))))

        steps = OPINION.STEPS.xt(response)

        # Create steps
        for step in steps:
            step_item, created = Step.objects.update_or_create(
                title=step['title'],
                sortkey=step['sortkey'],
                date=step['date'],
                protocol_url=step['protocol_url'],
                opinion=opinion,
                phase=phase_item,
                source_link=response.url
            )
            step_item.save()

        return len(steps)
