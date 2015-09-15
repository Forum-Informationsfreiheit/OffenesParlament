import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class INQUIRY:

    class LIST(SingleExtractor):
        XPATH = '//table/tr'

        @classmethod
        def xt(cls, response):
            inquiries = []
            raw_inquiries = response.xpath(cls.XPATH).extract()
            for raw_inquiry in raw_inquiries:
                last_update = Selector(text=raw_inquiry).xpath(
                    '//td[1]/text()').extract()[0].strip()
                inquiry_type = Selector(text=raw_inquiry).xpath(
                    '//td[2]/span/text()').extract()[0].strip()
                link = Selector(text=raw_inquiry).xpath(
                    '//td[3]/a/@href').extract()[0].strip()
                subject = Selector(text=raw_inquiry).xpath(
                    '//td[3]/a/text()[2]').extract()[0].strip()
                number = Selector(text=raw_inquiry).xpath(
                    '//td[4]/a/text()[2]').extract()[0].strip()
                status = Selector(text=raw_person).xpath(
                    '//td[5]/img/@alt').extract()[0].strip()

                self.logger.info(u"test".format(green(u'[{}]')))

                inquiries.append({
                    'last_update': last_update,
                    'inquiry_type': inquiry_type,
                    'link': link,
                    'subject': subject,
                    'number' : number,
                    'status' :status,
                })

            return inquiries
