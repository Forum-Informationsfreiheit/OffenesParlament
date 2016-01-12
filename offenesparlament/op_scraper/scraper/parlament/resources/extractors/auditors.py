# -*- coding: utf-8 -*-
import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class AUDITORS:

    class LIST(SingleExtractor):
        XPATH = '//*[@id="filterListeFW_009"]//table//tr'

        @classmethod
        def xt_pres_date(cls, raw_person):
            # Extract administration
            admin_datestring = Selector(text=raw_person).xpath(
                '//td[2]/text()').extract()[0]
            try:
                if " - " in admin_datestring:
                    start_date = _clean(admin_datestring.split(' - ')[0])
                    end_date = _clean(admin_datestring.split(' - ')[1])

                    start_date = datetime.datetime.strptime(
                        start_date, "%d.%m.%Y").date()
                    end_date = datetime.datetime.strptime(
                        end_date, "%d.%m.%Y").date()
                else:
                    start_date = datetime.datetime.strptime(
                        _clean(admin_datestring.replace(' -','')), "%d.%m.%Y").date()
                    end_date = None
            except:
                logger.error(
                    "Couldn't extract date from datestring {}".format(
                        admin_datestring))
                import ipdb
                ipdb.set_trace()

            return (start_date, end_date)

        @classmethod
        def xt(cls, response):
            persons = []
            raw_persons = response.xpath(cls.XPATH).extract()
            for raw_person in raw_persons:
                person = Selector(text=raw_person)
                if person.xpath('//th'):
                    continue
                source_link = person.xpath(
                    '//td//a/@href').extract()[0]
                reversed_name = _clean(
                    Selector(
                        text=remove_tags(raw_person, 'img')
                    ).xpath('//td//a/text()').extract()[0])

                (pres_start_date, pres_end_date) = cls.xt_pres_date(
                    raw_person)

                mandate = {
                    'title': u'RechnungshofpräsidentIn',
                    'short': u'RH-PräsidentIn',
                    'start_date': pres_start_date,
                    'end_date': pres_end_date
                }
                persons.append({
                    'source_link': source_link,
                    'reversed_name': reversed_name,
                    'mandate': mandate,
                })

            return persons
