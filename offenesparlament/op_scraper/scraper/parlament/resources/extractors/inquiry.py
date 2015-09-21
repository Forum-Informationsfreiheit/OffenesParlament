import datetime
from django.utils.html import remove_tags
from scrapy import Selector
import re

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class INQUIRY:

    """ OLD EXTRACTOR, WILL BE DELETED AS SOON AS ITS OBSOLENCE IS CONFIRMED
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
            """

    class KEYWORDS(MultiExtractor):
        XPATH = '//*[@id="schlagwortBox"]/ul//li/a/text()'

    class DOCS(MultiExtractor):
        LI_XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/div/ul/li'

        @classmethod
        def xt(cls, response):
            docs = []
            raw_docs = response.xpath(cls.LI_XPATH)
            for raw_doc in raw_docs:
                html_url, pdf_url = "", ""
                urls = raw_doc.css('a').xpath('@href').extract()
                for url in urls:
                    if url.endswith('.pdf'):
                        pdf_url = url
                    elif url.endswith('.html'):
                        html_url = url
                title = Selector(text=raw_doc.extract()).xpath(
                    '//a[1]/text()').extract()[0]
                title = title[:title.index('/')].strip()
                docs.append({
                    'title': title,
                    'html_url': html_url,
                    'pdf_url': pdf_url
                })
            return docs

    class SUBJECT(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/text()'

    class PARL_ID(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/span/text()'

    class DESCRIPTION(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[1]'

        @classmethod
        def xt(cls, response):
            description = response.xpath(cls.XPATH).extract()
            if description:
                description = description[0]
            else:
                description = u""
            description_nowhitespace = re.sub('\s+',' ',description)
            return remove_tags(description_nowhitespace, 'p').strip()

    class SENDER(SingleExtractor):
        XPATH = '//*[@class="c_2"]/p[2]/a/@href'

        @classmethod
        def xt(cls, response):
            sender_link = response.xpath(cls.XPATH).extract()
            return sender_link[0].split('/')[-2]

    class RECEIVER(SingleExtractor):
        XPATH = '//*[@class="c_2"]/p[3]/a/@href'

        @classmethod
        def xt(cls, response):
            receiver_link = response.xpath(cls.XPATH).extract()
            return receiver_link[0].split('/')[-2]