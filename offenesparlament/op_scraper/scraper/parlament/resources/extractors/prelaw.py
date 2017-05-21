import datetime
from django.utils.html import remove_tags
from scrapy import Selector


from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.extractors.law import LAW
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PRELAW:

    class DESCRIPTION(SingleExtractor):
        XPATH = "//div[contains(concat(' ', normalize-space(@class), ' '), ' c_2 ')]/h3/following-sibling::p/text()"

        @classmethod
        def xt(cls, response):
            try:
                description = response.xpath(cls.XPATH)[0].extract()[0]
            except:
                import ipdb
                ipdb.set_trace()
            return remove_tags(description, 'p')

    class STEPS(MultiExtractor):
        XPATH = '//table'

        @classmethod
        def xt(cls, response):
            steps = []
            raw_table = response.xpath('//table')[1]
            raw_steps = Selector(text=raw_table.extract()).xpath('//tr')[1:] # ignore header
            for index, step in enumerate(raw_steps, start=1):
                step_selector = Selector(text=step.extract())
                title = LAW.PHASES.STEPS.TITLE.xt(step_selector)
                date_str = LAW.PHASES.STEPS.DATE.xt(step_selector)
                date = datetime.datetime.strptime(
                    date_str, "%d.%m.%Y").date()
                protocol_url = LAW.PHASES.STEPS.PROTOCOL.xt(step_selector)
                steps.append({
                    'date': date,
                    'title': title['text'],
                    'sortkey': str(index).zfill(3),
                    'protocol_url': protocol_url
                })
            return steps

    class OPINIONS(MultiExtractor):
        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/table//tr'

        @classmethod
        def xt(cls, response):
            ops = []
            raw_ops = response.xpath(cls.XPATH).extract()
            for raw_op in raw_ops[1:]:
                op_sel = Selector(text=raw_op)

                date = op_sel.xpath('//td[1]/text()').extract()
                date = date[0]

                url = op_sel.xpath('//td[2]/a/@href').extract()[0]
                parl_id = u"({})".format(
                    op_sel.xpath('//td[2]/a/text()').extract()[0])

                title = op_sel.xpath('//td[3]/text()').extract()[0]
                if title:
                    title = _clean(title).replace("*", ", ")
                else:
                    title = None

                email = op_sel.xpath('//td[3]/a/@href').extract()
                if email:
                    email = email[0].replace('mailto:', '')
                    title = op_sel.xpath('//td[3]/a/text()').extract()[0]
                else:
                    email = None

                try:
                    date = datetime.datetime.strptime(
                        _clean(date), "%d.%m.%Y").date()
                except:
                    date = None

                ops.append({
                    'date': date,
                    'url': url,
                    'email': email,
                    'title': title,
                    'parl_id': parl_id
                })

            return ops
