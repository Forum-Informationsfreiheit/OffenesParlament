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


class ADMINISTRATION:

    class LIST(SingleExtractor):
        XPATH = '//*[@id="filterListeFW_016"]//table//tr'

        @classmethod
        def xt_admin_date(cls, raw_person):
            # Extract administration
            admin_datestring = Selector(text=raw_person).xpath(
                '//td[1]/span/@title').extract()[0]
            if ';' in admin_datestring:
                admin_datestring = admin_datestring.split(";")[0]

            if ',' in admin_datestring:
                admin_datestring = admin_datestring.split(",")[0]

            try:
                if " - " in admin_datestring:
                    start_date = _clean(admin_datestring.split(' - ')[0])
                    end_date = _clean(admin_datestring.split(' - ')[1])

                    start_date = datetime.datetime.strptime(
                        start_date, "%d.%m.%Y").date()
                    end_date = datetime.datetime.strptime(
                        end_date, "%d.%m.%Y").date()
                else:
                    start_date = datetime.datetime.strptime(
                        _clean(admin_datestring), "%d.%m.%Y").date()
                    end_date = None
            except:
                logger.error(
                    "Couldn't extract date from datestring {}".format(
                        admin_datestring))
                import ipdb
                ipdb.set_trace()

            return (start_date, end_date)

        @classmethod
        def xt(cls, response):
            persons = []
            raw_persons = response.xpath(cls.XPATH).extract()
            for raw_person in raw_persons:
                person = Selector(text=raw_person)
                if person.xpath('//th'):
                    continue
                source_link = person.xpath(
                    '//td//a/@href').extract()[0]
                reversed_name = _clean(
                    Selector(
                        text=remove_tags(raw_person, 'img')
                    ).xpath('//td//a/text()').extract()[0])
                if ' siehe ' in reversed_name:
                    reversed_name = reversed_name.split(' siehe ')[1]

                admin_title = person.xpath(
                    '//td[1]/span/text()').extract()

                (admin_start_date, admin_end_date) = cls.xt_admin_date(
                    raw_person)

                administration = {
                    'title': admin_title,
                    'start_date': admin_start_date,
                    'end_date': admin_end_date
                }
                # TODO EXTRACT DATE(S) FROM BUNDESMINISTERIUM td
                # TODO ADD EITHER DATE(S) TO FUNCTION
                try:
                    if person.xpath('//tr//td[3]/span/text()'):
                        function_short = person.xpath(
                            '//td[3]/span/text()').extract()[0]
                        function_title = person.xpath(
                            '//td[3]/span/@title').extract()[0]

                    elif person.xpath('//tr//td[3]/text()'):
                        function_short = _clean(person.xpath(
                            '//td[3]/text()').extract()[0])
                        function_title = ''
                except:
                    import ipdb
                    ipdb.set_trace()
                mandate = {
                    'short': function_short,
                    'title': function_title,
                    'administration': administration}

                persons.append({
                    'source_link': source_link,
                    'reversed_name': reversed_name,
                    'mandate': mandate,
                })

            return persons
