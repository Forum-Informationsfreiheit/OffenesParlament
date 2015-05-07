# -*- coding: utf-8 -*-

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from roman import fromRoman

from scrapy import log

from parlament.spiders import BaseScraper
from parlament.resources.extractors import *
from parlament.settings import BASE_HOST

from op_scraper.models import Phase
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion


class LawsInitiativesSpider(BaseScraper):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/RGES/filter.psp")

    LLP = range(24, 26)

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/RGES/index.shtml',
        'anwenden': 'Anwenden',
        'RGES': 'ALLE',
        'SUCH': ' ',
        'listeId': '103',
        'FBEZ': 'FP_003',
    }

    name = "laws_initiatives"

    def __init__(self, **kw):
        super(LawsInitiativesSpider, self).__init__(**kw)

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def parse(self, response):
        # Extract fields
        title = LAW.TITLE.xt(response)
        parl_id = LAW.PARL_ID.xt(response)
        status = LAW.STATUS.xt(response)
        LLP = fromRoman(response.url.split('/')[-4])

        # save ids and stuff for internals
        if LLP not in self.idlist:
            self.idlist[LLP] = {}
        self.idlist[LLP][response.url] = [parl_id, LLP]

        # Extract foreign keys
        category = LAW.CATEGORY.xt(response)
        description = LAW.DESCRIPTION.xt(response)

        # Don't re-parse laws we already have
        # FIXME: at some point, we need to be able to update laws, not just
        # skip them if we already have them
        if Law.objects.filter(
                parl_id=parl_id,
                legislative_period=LLP).exists():
            log.msg(
                u"{} with ID {} in LLP {} already exists, skipping import"
                .format(
                    red(title),
                    cyan(u"[{}]".format(parl_id)),
                    LLP),
                level=log.INFO)
            return

        # Log our progress
        logtext = u"Scraping {} with id {}, LLP {} @ {}".format(
            red(title),
            cyan(u"[{}]".format(parl_id)),
            green(str(LLP)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        # Create category if we don't have it yet
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        # Create and save Law
        law_item = Law.objects.create(
            title=title,
            parl_id=parl_id,
            source_link=response.url,
            status=status,
            description=description,
            legislative_period=LLP)
        law_item.save()

        # Attach foreign keys
        law_item.keywords = self.parse_keywords(response)
        law_item.category = cat
        law_item.documents = self.parse_docs(response)

        law_item.save()
        response.meta['law_item'] = law_item

        callback_requests = []

        # is the tab 'Parlamentarisches Verfahren available?'
        if response.xpath('//h2[@id="tab-ParlamentarischesVerfahren"]'):
            self.parse_parliament_steps(response)
            # url_postfix = response.xpath(
            #     '//*[@id="ParlamentarischesVerfahren"]/a/@href').extract()[0]
            # post_req = scrapy.Request(response.url + url_postfix,
            #                           callback=self.parse_parliament_steps,
            #                           dont_filter=True)
            # post_req.meta['law_item'] = law_item
            # callback_requests.append(post_req)

        if response.xpath('//h2[@id="tab-VorparlamentarischesVerfahren"]'):
            self.parse_pre_parliament_steps(response)

            # url_postfix = response.xpath(
            #     '//*[@id="VorparlamentarischesVerfahren"]/a/@href').extract()[0]
            # pre_req = scrapy.Request(response.url + url_postfix,
            #                          callback=self.parse_pre_parliament_steps,
            #                          dont_filter=True)
            # pre_req.meta['law_item'] = law_item
            # callback_requests.append(pre_req)
            # log.msg(green("Pre-Law found: {}".format(pre_req)), level=log.INFO)

        # log.msg(green("Open Callback requests: {}".format(
        #     len(callback_requests))), level=log.INFO)

        # return callback_requests

    def parse_keywords(self, response):

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

    def parse_pre_parliament_steps(self, response):
        """
        Callback function to parse the additional
        'Vorparlamentarisches Verfahren' page
        """
        law_item = response.meta['law_item']
        prelaw_id = LAW.PRELAW_ID.xt(response)
        if Law.objects.filter(parl_id=prelaw_id, legislative_period=law_item.legislative_period):
            prelaw = Law.objects.get(
                parl_id=prelaw_id,
                legislative_period=law_item.legislative_period)
            law_item.references = prelaw
            law_item.save()

    def parse_parliament_steps(self, response):
        """
        Callback function to parse the additional 'Parlamentarisches Verfahren'
        page
        """
        law_item = response.meta['law_item']

        phases = LAW.PHASES.xt(response)

        for phase in phases:
            # Create phase if we don't have it yet
            phase_item, created = Phase.objects.get_or_create(
                title=phase['title'])
            if created:
                log.msg(u"Created Phase {}".format(
                    green(u'[{}]'.format(phase_item.title))))

            # Create steps
            for step in phase['steps']:
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
