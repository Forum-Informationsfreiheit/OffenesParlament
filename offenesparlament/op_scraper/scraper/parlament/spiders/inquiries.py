# -*- coding: utf-8 -*-
import scrapy
import feedparser

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from urllib import urlencode

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.resources.extractors.inquiry import *
from parlament.resources.util import _clean


from op_scraper.models import Party
from op_scraper.models import State
from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate
from op_scraper.models import LegislativePeriod
from op_scraper.models import Inquiry


class InquiriesSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/JMAB/filter.psp")

    URLOPTIONS = {
        'view':'RSS',
        'jsMode':'RSS',
        'xdocumentUri':'/PAKT/JMAB/index.shtml',
        'NRBR':'NR',
        'anwenden':'Anwenden',
        'GP':'',
        #'ZEIT':'J',
        'JMAB':'J_JPR_M',
        'VHG2':'ALLE',
        'SUCH':'',
        'listeId':'105',
        'FBEZ':'FP_005'
    }
    
    name = "inquiries"
    inquiries_scraped = []

    def __init__(self, **kw):
        super(InquiriesSpider, self).__init__(**kw)

        self.start_urls = self.get_urls()
        self.logger.info(green(u'test'))
        self.cookies_seen = set()
        self.idlist = {}



    def parse(self, response):
        inquiries = INQUIRY.LIST.xt(response)
        #self.logger.info(green(u'test'))
        for i in inquiries:
            parl_id = i['link'].split('/')[-2]
            self.logger.info(u"Created Inquiry {}".format(
                green(u'[{}]'.format(i[parl_id]))))
        return