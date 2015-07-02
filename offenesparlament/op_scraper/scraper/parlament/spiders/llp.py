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
from parlament.resources.extractors.llp import *

from parlament.resources.util import _clean


from op_scraper.models import LegislativePeriod


class LegislativePeriodSpider(BaseScraper):
    BASE_URL = "{}/{}".format(BASE_HOST, "/WWER/PARL/")

    name = "llp"

    def __init__(self, **kw):
        super(LegislativePeriodSpider, self).__init__(**kw)

        self.start_urls = [self.BASE_URL]

        self.cookies_seen = set()
        self.idlist = {}

    def parse(self, response):

        llps = LLP.xt(response)

        for llp in llps:
            llp_item, created_llp = LegislativePeriod.objects.update_or_create(
                roman_numeral=llp['roman_numeral'],
                defaults=llp
            )
            llp_item.save()

            if created_llp:
                self.logger.info(u"Created Legislative Period {}".format(
                    green(u'[{}]'.format(llp['roman_numeral']))))
            else:
                self.logger.info(u"Updated Legislative Period {}".format(
                    green(u"[{}]".format(llp['roman_numeral']))
                ))
