import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from laws.resources import SingleExtractor
from laws.resources import MultiExtractor


class TITLE(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/text()'


class PARL_ID(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/span/text()'


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
        description = response.xpath(cls.XPATH).extract()[0]
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
            title = PHASE_TITLE.xt(raw_phase_selector)
            steps = PHASE_STEPS.xt(phase_index, raw_phase_selector)
            phase = {
                'title': title,
                'steps': steps
            }
            phases.append(phase)
        return phases


class PHASE_TITLE(SingleExtractor):

    XPATH = "//tr[contains(concat(' ', normalize-space(@class), ' '), ' historyHeader ')]//a/text()"


class PHASE_STEPS(MultiExtractor):

    XPATH = "/html/body/tbody/tr[not(contains(@class, 'close')) and not(contains(@class, 'historyHeader'))]"
    STEP_TITLE = "//td[1]/text()"

    @classmethod
    def xt(cls, phase_index, selector):
        steps = []
        raw_steps = selector.xpath(cls.XPATH)
        for index, raw_step in enumerate(raw_steps, start=1):
            step_sortkey = "{}#{}".format(
                phase_index,
                str(index).zfill(3))
            step_selector = Selector(text=raw_step.extract())

            title = STEP_TITLE.xt(step_selector)
            date_str = STEP_DATE.xt(step_selector)
            date = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
            protocol_url = STEP_PROTOCOL.xt(step_selector)
            step = {
                'sortkey': step_sortkey,
                'title': title,
                'date': date,
                'protocol_url': protocol_url
            }
            steps.append(step)
        return steps


class STEP_DATE(SingleExtractor):
    XPATH = "//td[1]/text()"


class STEP_TITLE(SingleExtractor):
    XPATH = "//td[2]/text()"


class STEP_PROTOCOL(SingleExtractor):
    XPATH = "//td[3]/text()"
