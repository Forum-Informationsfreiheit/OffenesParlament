# -*- coding: utf-8 -*-
import scrapy


from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from roman import fromRoman

from scrapy import log
import collections


from parlament.resources.extractors import *
from parlament.resources.rss import get_urls


from op_scraper.models import Phase
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion


class PersonsSpider(scrapy.Spider):
    name = "persons"
    allowed_domains = ["parlament.gv.at"]

    start_urls = [
        'http://www.parlament.gv.at/WWER/SUCHE/filter.psp?view=RSS&jsMode=RSS&xdocumentUri=%2FWWER%2FSUCHE%2Findex.shtml&NAME_TYP_ID=1201&NAME=&R_ZEIT=ALLE&listeId=1&LISTE=Suchen&FBEZ=FW_001']

    def __init__(self, **kw):
        super(PersonsSpider, self).__init__(**kw)

        # add at least a default URL for testing
        self.start_urls = get_urls() or self.DEBUG_URLS

        self.cookies_seen = set()
        self.idlist = {}

    def parse(self, response):
        pass
