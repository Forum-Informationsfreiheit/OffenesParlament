import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources import SingleExtractor
from parlament.resources import MultiExtractor
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class LAW:

    class TITLE(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/text()'

    class PARL_ID(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/span/text()'

    class PRELAW_ID(SingleExtractor):
        XPATH = '//h2[@id="tab-VorparlamentarischesVerfahren"]/..'
        XPATH_ID = "//h3[contains(concat(' ', normalize-space(@class), ' '), ' zeigeContentBlock ')]//span/text()"

        @classmethod
        def xt(cls, response):
            raw_section = Selector(text=response.xpath(cls.XPATH).extract()[0])
            prelaw_id = raw_section.xpath(cls.XPATH_ID).extract()[0]
            return prelaw_id

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

    class STATUS(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div[1]/div[1]/p'

        @classmethod
        def xt(cls, response):
            status = remove_tags(
                response.xpath(cls.XPATH).extract()[0], 'em img p')
            status = status.replace('Status: ', '')
            return status

    class CATEGORY(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/h3/text()'

    class DESCRIPTION(SingleExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[1]'

        @classmethod
        def xt(cls, response):
            description = response.xpath(cls.XPATH).extract()
            if description:
                description = description[0]
            else:
                description = u""
            return remove_tags(description, 'p')

    class PHASES(MultiExtractor):

        XPATH = "//tr[contains(concat(' ', normalize-space(@class), ' '), ' historyHeader ')]/.."

        @classmethod
        def xt(cls, response):
            phases = []
            raw_phases = response.xpath(cls.XPATH)
            for index, raw_phase in enumerate(raw_phases, start=1):
                raw_phase_selector = Selector(text=raw_phase.extract())
                phase_index = str(index).zfill(2)
                title = LAW.PHASES.TITLE.xt(raw_phase_selector)
                steps = LAW.PHASES.STEPS.xt(phase_index, raw_phase_selector)
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

                    title = LAW.PHASES.STEPS.TITLE.xt(step_selector)
                    date_str = LAW.PHASES.STEPS.DATE.xt(step_selector)
                    date = datetime.datetime.strptime(
                        date_str, "%d.%m.%Y").date()
                    protocol_url = LAW.PHASES.STEPS.PROTOCOL.xt(step_selector)
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
                            person_source_link = row_selector.xpath(
                                cls.XP_P_LINK).extract()[0]
                            person_name = row_selector.xpath(
                                cls.XP_P_NAME).extract()
                            statement_type = _clean(
                                row_selector.xpath(cls.XP_T_TYPE).extract()[0])
                            protocol_link = row_selector.xpath(
                                cls.XP_PROT_LINK).extract()
                            protocol_text = _clean(
                                remove_tags(
                                    row_selector.xpath(
                                        cls.XP_PROT_TEXT).extract()[0],
                                    'td a'))
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
                                'td'))
                        title = {'text': text}
                    return title

            class PROTOCOL(SingleExtractor):
                XPATH = "//td[3]/text()"
