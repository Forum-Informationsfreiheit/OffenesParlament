import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean
from parlament.settings import BASE_HOST

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

import roman


class LLP(SingleExtractor):

    XPATH = '//select[@id = "FW_008_GP"]/option'

    @classmethod
    def xt(cls, response):
        llps = []
        raw_llps = [Selector(text=llp.extract())
                    for llp in response.xpath(cls.XPATH)]
        for raw_llp in raw_llps:
            llp_roman = raw_llp.xpath('//option/@value').extract()[0]

            if llp_roman == u'ALLE':
                continue

            try:
                llp_number = roman.fromRoman(llp_roman)
            except:
                llp_number = -1

            llp_title = raw_llp.xpath('//option/text()').extract()[0]
            dates = []
            for t_sub in llp_title.split(' '):
                try:
                    date = datetime.datetime.strptime(
                        t_sub.replace(':', ''), "%d.%m.%Y").date()
                    dates.append(date)
                except:
                    pass

            if not dates:
                continue

            LLP = {
                'number': llp_number,
                'roman_numeral': llp_roman,
                'start_date': dates[0]
            }

            if len(dates) > 1:
                LLP['end_date'] = dates[1]
            llps.append(LLP)

        return llps
