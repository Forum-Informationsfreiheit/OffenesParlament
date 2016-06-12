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
from scrapy import log
from ansicolor import green

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

    class RESPONSEDOCS(MultiExtractor):
        LI_XPATH = '//*[@id="content"]/div[3]/div[2]/div/div/ul/li'

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
                if '/' in title: # xpath also matches schlagworte sometimes
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

    class PHASES(MultiExtractor):

        XPATH = "//tr[contains(concat(' ', normalize-space(@class), ' '), ' historyHeader ')]/.."

        @classmethod
        def xt(cls, response):
            phases = []
            raw_phases = response.xpath(cls.XPATH)
            for index, raw_phase in enumerate(raw_phases, start=1):
                raw_phase_selector = Selector(text=raw_phase.extract())
                phase_index = str(index).zfill(2)
                title = INQUIRY.PHASES.TITLE.xt(raw_phase_selector)
                steps = INQUIRY.PHASES.STEPS.xt(phase_index, raw_phase_selector)
                phase = {
                    'title': title,
                    'steps': steps
                }
                phases.append(phase)
            return phases

        class TITLE(SingleExtractor):

            XPATH = "//tr[contains(concat(' ', normalize-space(@class), ' '), ' historyHeader ')]//a/text()"

        class STEPS(MultiExtractor):

            XPATH = "/html/body/tbody/tr[not(contains(@class, 'close')) and not(contains(@class, 'historyHeader'))]"

            @classmethod
            def xt(cls, phase_index, selector):
                steps = []
                raw_steps = selector.xpath(cls.XPATH)
                for index, raw_step in enumerate(raw_steps, start=1):
                    step_sortkey = "{}#{}".format(
                        phase_index,
                        str(index).zfill(3))
                    step_selector = Selector(text=raw_step.extract())

                    title = INQUIRY.PHASES.STEPS.TITLE.xt(step_selector)
                    date_str = INQUIRY.PHASES.STEPS.DATE.xt(step_selector)
                    date = datetime.datetime.strptime(
                        date_str, "%d.%m.%Y").date()
                    protocol_url = INQUIRY.PHASES.STEPS.PROTOCOL.xt(step_selector)
                    if protocol_url:
                        protocol_url = "{}{}".format(
                            BASE_HOST,
                            protocol_url
                        )
                    step = {
                        'sortkey': step_sortkey,
                        'title': title,
                        'date': date,
                        'protocol_url': protocol_url
                    }
                    steps.append(step)
                return steps

            class DATE(SingleExtractor):
                XPATH = "//td[1]/text()"

            class TITLE(SingleExtractor):
                XPATH = "//td[2]"
                XP_P_LINK = '//td[2]/a/@href'
                XP_P_NAME = '//td[2]/a/text()'
                XP_T_TYPE = '//td[3]/text()'
                XP_PROT_LINK = '//td[4]/a/@href'
                XP_PROT_TEXT = '//td[4]'

                @classmethod
                def xt(cls, step_selector):
                    title_selector = step_selector.xpath('//td[2]')[0]

                    # we have wortmeldungen!
                    if title_selector.xpath('//table'):
                        table_selector = title_selector.xpath('//table')[0]
                        raw_rows = [
                            Selector(text=raw_row)
                            for raw_row
                            in table_selector.xpath('//tbody//tr').extract()]
                        statements = []
                        # Extract statements data
                        for index, row_selector in enumerate(raw_rows):
                            if(row_selector.xpath(cls.XP_P_LINK).extract()):
                                person_source_link = row_selector.xpath(
                                    cls.XP_P_LINK).extract()[0]
                            else:
                                continue

                            person_name = row_selector.xpath(
                                cls.XP_P_NAME).extract()
                            if(row_selector.xpath(cls.XP_T_TYPE).extract()):
                                statement_type = _clean(
                                    row_selector.xpath(cls.XP_T_TYPE).extract()[0])
                            else:
                                continue
                            protocol_link = row_selector.xpath(
                                cls.XP_PROT_LINK).extract()
                            if(row_selector.xpath(
                                        cls.XP_PROT_TEXT).extract()):
                                protocol_text = _clean(
                                    remove_tags(
                                        row_selector.xpath(
                                            cls.XP_PROT_TEXT).extract()[0],
                                        'td a'))
                            else:
                                protocol_text = []
                            statements.append({
                                'index': index,
                                'person_source_link': person_source_link,
                                'person_name': person_name,
                                'statement_type': statement_type,
                                'protocol_link': protocol_link,
                                'protocol_text': protocol_text,
                            })
                        title = {
                            'text': u'Wortmeldungen in der Debatte',
                            'statements': statements
                        }                    
                    else:
                        text = _clean(
                            remove_tags(
                                step_selector.xpath(
                                    cls.XPATH).extract()[0],
                                'td')).replace('<a href="', '<a href="{}'.format(BASE_HOST))
                        title = {'text': text}
                    return title

            class PROTOCOL(SingleExtractor):
                XPATH = "//td[3]//a/@href"

    class STEPS(MultiExtractor):
        XPATH = '//*[@class="contentBlock"]/*[@class="reiterBlock"]/table/tbody/tr'

        @classmethod
        def xt(cls, response):
            steps = []
            raw_steps = response.xpath(cls.XPATH)
            for index, step in enumerate(raw_steps, start=1):
                step_selector = Selector(text=step.extract())
                title = INQUIRY.STEPS.TITLE.xt(step_selector)
                date_str = INQUIRY.STEPS.DATE.xt(step_selector).strip()
                date = datetime.datetime.strptime(
                    date_str, "%d.%m.%Y").date()
                protocol_url = INQUIRY.STEPS.PROTOCOL.xt(step_selector)
                if protocol_url:
                    protocol_url = "{}{}".format(
                        BASE_HOST,
                        protocol_url
                    )
                steps.append({
                    'title': title,
                    'date': date,
                    'sortkey': str(index).zfill(3),
                    'protocol_url': protocol_url,
                })
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
                #full_title = re.sub('<[^>]*>', '', title_selector).strip()
                full_title = title_selector.strip()
                return full_title


        class PROTOCOL(SingleExtractor):
            XPATH = "//td[3]/a/@href"

    class RESPONSE_LINK(SingleExtractor):
        XPATH = '//*[@class="contentBlock"]/*[@class="reiterBlock"]/table/tbody/tr/*[text()[contains(.,"Schriftliche Beantwortung")]]'

        @classmethod
        def xt(cls, response):
            response_link = response.xpath('//*[@class="contentBlock"]/*[@class="reiterBlock"]/table/tbody/tr/*[text()[contains(.,"Schriftliche Beantwortung")]]/a/@href').extract()
            if not response_link:
                return 0
            else:
                return response_link[0]

    class RESPONSESENDER(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]//p[contains(text(),"Beantwortet durch:")]//a/@href'

        @classmethod
        def xt(cls, response):
            responsesender_link = response.xpath(cls.XPATH).extract()
            return responsesender_link[0].split('/')[-2]

    class RESPONSEDESCRIPTION(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div/p[1]'
        
        @classmethod
        def xt(cls, response):
            description = response.xpath(cls.XPATH).extract()
            if description:
                description = description[0]
            else:
                description = u""
            description_nowhitespace = re.sub('\s+',' ',description)
            return remove_tags(description_nowhitespace, 'p').strip()
