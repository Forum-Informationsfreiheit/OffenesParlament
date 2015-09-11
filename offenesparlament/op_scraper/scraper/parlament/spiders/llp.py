# -*- coding: utf-8 -*-
from ansicolor import green

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
from parlament.resources.extractors.llp import *

from op_scraper.models import LegislativePeriod


class LegislativePeriodSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "/WWER/PARL/")

    name = "llp"

    def __init__(self, **kw):
        super(LegislativePeriodSpider, self).__init__(**kw)

        self.start_urls = [self.BASE_URL]

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
