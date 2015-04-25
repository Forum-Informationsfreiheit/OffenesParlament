# -*- coding: utf-8 -*-
import scrapy


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


class PreLawsSpider(BaseScraper):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/MESN/filter.psp")

    LLP = range(24, 26)

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/MESN/index.shtml',
        'anwenden': 'Anwenden',
        'MESN': 'ME',
        'R_MESN': 'ME',
        'MIN': 'ALLE',
        'SUCH': '',
        'listeId': '102',
        'FBEZ': 'FP_002',
    }

    name = "pre_laws"

    def __init__(self, **kw):
        super(PreLawsSpider, self).__init__(**kw)

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def parse(self, response):
        # Extract fields
        title = LAW.TITLE.xt(response)
        parl_id = LAW.PARL_ID.xt(response)
        LLP = fromRoman(response.url.split('/')[-4])

        # save ids and stuff for internals
        if LLP not in self.idlist:
            self.idlist[LLP] = {}
        self.idlist[LLP][response.url] = [parl_id, LLP]

        # Extract foreign keys
        category = LAW.CATEGORY.xt(response)
        description = PRELAW.DESCRIPTION.xt(response)

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
            description=description,
            legislative_period=LLP)
        law_item.save()

        # Attach foreign keys
        law_item.keywords = self.parse_keywords(response)
        law_item.category = cat
        law_item.documents = self.parse_docs(response)

        law_item.save()

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
