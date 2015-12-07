import datetime
from django.utils.html import remove_tags
from scrapy import Selector
import re

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean
from parlament.settings import BASE_HOST

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class INQUIRY:

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

    class TITLE(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/text()'

    class CATEGORY(SingleExtractor):
        XPATH = '//*[@id="content"]//h3/text()'

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
        XPATH = '//*[@class="c_2"]/p[contains(text(), "Eingebracht von")]/a/@href'

        @classmethod
        def xt(cls, response):
            sender_links = response.xpath(cls.XPATH).extract()
            return [sender_link.split('/')[-2] for sender_link in sender_links]

    class RECEIVER(SingleExtractor):
        XPATH = '//*[@class="c_2"]/p[last()]/a/@href'

        @classmethod
        def xt(cls, response):
            receiver_link = response.xpath(cls.XPATH).extract()
            return receiver_link[0].split('/')[-2]

    class STEPS(MultiExtractor):
        XPATH = '//*[@class="contentBlock"]/*[@class="reiterBlock"]/table/tbody/tr'

        @classmethod
        def xt(cls, response):
            steps = []
            raw_steps = response.xpath(cls.XPATH)
            for raw_step in raw_steps:
                step_selector = Selector(text=raw_step.extract())
                title = INQUIRY.STEPS.TITLE.xt(step_selector)
                title_link = INQUIRY.STEPS.TITLE_LINK.xt(step_selector)
                if title_link:
                    title_link = "{}{}".format(
                        BASE_HOST,
                        title_link
                    )
                date_str = INQUIRY.STEPS.DATE.xt(step_selector).strip()
                date = datetime.datetime.strptime(
                    date_str, "%d.%m.%Y").date()
                protocol_url = INQUIRY.STEPS.PROTOCOL.xt(step_selector)
                if protocol_url:
                    protocol_url = "{}{}".format(
                        BASE_HOST,
                        protocol_url
                    )
                step = {
                    'title': title,
                    'date': date,
                    'protocol_url': protocol_url,
                    'title_link': title_link

                }

                steps.append(step)
            return steps


        class DATE(SingleExtractor):
            XPATH = "//td[1]/text()"
        
        class TITLE(SingleExtractor):
            XPATH = "//td[2]/text()"
            XPATH_LINK_TEXT = "//td[2]/a/text()"
            XPATH_LINK = "//td[2]/a/@href"

            @classmethod
            def xt(cls, step_selector):
                title_selector = step_selector.xpath('//td[2]')[0].extract()
                full_title = re.sub('<[^>]*>', '', title_selector).strip()
                return full_title

        class TITLE_LINK(SingleExtractor):
            XPATH = "//td[2]/a/@href"

        class PROTOCOL(SingleExtractor):
            XPATH = "//td[3]/a/@href"

    