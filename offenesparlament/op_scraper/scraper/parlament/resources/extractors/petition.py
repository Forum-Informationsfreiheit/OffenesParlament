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


class PETITION:

    class OPINIONS(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/h4[1]/following-sibling::ul[1]/li'

        @classmethod
        def xt(cls, response):
            ops = []
            raw_ops = response.xpath(cls.XPATH).extract()
            for raw_op in raw_ops:
                op_sel = Selector(text=raw_op)

                url = op_sel.xpath('//a/@href').extract()[0]
                parl_id = op_sel.xpath('//span/text()').extract()[0]

                # TODO: check what title should be
                # title = op_sel.xpath('//td[3]/text()').extract()[0]
                # if title:
                #    title = _clean(title).replace("*", ", ")
                # else:
                #    title = None

                email = op_sel.xpath('//a[@class="mail"]/@href').extract()
                if email:
                    email = email[0].replace('mailto:', '')
                    # title = op_sel.xpath('//td[3]/a/text()').extract()[0]
                else:
                    email = None
                ops.append({
                    'date': '',  # date,
                    'url': url,
                    'email': email,
                    'title': '',  # title,
                    'parl_id': parl_id
                })

            return ops

