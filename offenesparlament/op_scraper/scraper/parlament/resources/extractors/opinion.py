import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources import SingleExtractor
from parlament.resources import MultiExtractor
from parlament.resources.util import _clean

from parlament.resources.extractors.law import LAW

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class OPINION:

    class ENTITY:
        XPATH = '//p[contains(text(),"Stellungnehmende(r):")]/text()'
        XPATH_EMAIL = '//p[contains(text(),"Stellungnehmende(r):")]/a/@href'

        @classmethod
        def xt(cls, response):
            entity_raw = response.xpath(cls.XPATH).extract()
            if entity_raw:
                entity_text = entity_raw[0].replace(
                    u'Stellungnehmende(r):', '')
            else:
                entity_text = u""
            entries = [entry.strip()
                       for entry in entity_text.split(u'\n')
                       if entry.strip()]
            entity = {
                'title_detail': u'',
                'phone': None,
                'email': None
            }
            for entry in entries:
                if u"Tel.:" in entry:
                    entity['phone'] = entry.replace(u'Tel.:', u'')
                else:
                    entity['title_detail'] = u"{} {}".format(
                        entity['title_detail'], entry)
            entity['title_detail'] = entity['title_detail'].replace("*", ", ")
            emaiL_raw = response.xpath(cls.XPATH_EMAIL).extract()
            if emaiL_raw:
                entity['email'] = emaiL_raw[0].replace(u'mailto:', u'')

            return entity

    class STEPS(MultiExtractor):
        XPATH = '//table'

        @classmethod
        def xt(cls, response):
            steps = []
            raw_table = response.xpath('//table')[0]
            raw_steps = Selector(text=raw_table.extract()).xpath('//tr')
            for index, step in enumerate(raw_steps[1:]):
                step_selector = Selector(text=step.extract())
                title = LAW.PHASES.STEPS.TITLE.xt(step_selector)
                date_str = LAW.PHASES.STEPS.DATE.xt(step_selector)
                try:
                    date = datetime.datetime.strptime(
                        date_str, "%d.%m.%Y").date()
                except:
                    import ipdb
                    ipdb.set_trace()
                protocol_url = LAW.PHASES.STEPS.PROTOCOL.xt(step_selector)
                steps.append({
                    'date': date,
                    'title': title,
                    'sortkey': str(index).zfill(3),
                    'protocol_url': protocol_url
                })
            return steps
