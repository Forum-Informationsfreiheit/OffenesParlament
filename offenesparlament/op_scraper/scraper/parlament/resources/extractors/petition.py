import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import MultiExtractor

import re

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PETITION:

    class SIGNATURE_COUNT(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[4]/p[2]/span'

        @classmethod
        def xt(cls, response):
            raw_signature_count=response.xpath(cls.XPATH).extract()
            if len(raw_signature_count) > 0:
                # sometimes there can be signatures also in the next llp, find all numbers in text
                signature_count_list = [int(number) for number in re.findall(r'\d+', raw_signature_count[0])]
                return sum(signature_count_list)

            return 0


    class CREATORS(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[starts-with(text(),"{}")]'

        @classmethod
        def xt(cls, response):
            XPATH_BI_creator = cls.XPATH.format("Erstunterzeichner")
            XPATH_PET_creator = cls.XPATH.format("eine Petition")

            creators = []

            #TODO: diffentiate between members of parliament and other persons
            raw_creators_list = response.xpath(XPATH_PET_creator).extract()
            if len(raw_creators_list) > 0:
                #started by members of parliament
                raw_creators_list = raw_creators_list[0]
            else:
                raw_creators_list = response.xpath(XPATH_BI_creator).extract()

            return raw_creators_list

    class SIGNING(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/ul/li/a'

        @classmethod
        def xt(cls, response):
            raw_url_list = response.xpath(cls.XPATH).extract()
            if len(raw_url_list) > 0:
                raw_url = raw_url_list[0]
                url_sel = Selector(text=raw_url)
                text = url_sel.xpath('//text()').extract()
                if text[0] == u'Hier k\xf6nnen Sie zustimmen':
                    signing_url = url_sel.xpath('//@href').extract()
                    return signing_url, True
            return '', False

    class OPINIONS(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/h4[text()="Stellungnahmen"]/following-sibling::ul[1]/li'

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

