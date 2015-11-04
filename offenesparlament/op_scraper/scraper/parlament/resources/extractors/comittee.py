import datetime
import roman

from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.util import _clean

from parlament.settings import BASE_HOST

import time
import datetime

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class COMITTEE:

    @staticmethod
    def url_to_parlid(url):
        if url is not u'':
            raw_parl_id = url.split('/')[-2]
            if len(raw_parl_id) > 1:
                raw_parl_id = raw_parl_id.split('_')
                parl_id_type = raw_parl_id[0]
                parl_id_number = int(raw_parl_id[1])
                parl_id = u'({}/{})'.format(parl_id_number, parl_id_type)
                return parl_id

        return u''

    class LLP(SingleExtractor):

        XPATH = '//*[@id="content"]/div[1]/p/a[4]/text()'

        @classmethod
        def xt(cls, response):
            raw_llp = response.xpath(cls.XPATH).extract()

            if len(raw_llp) > 0 and u'Nationalrat' in raw_llp[0]:
                list = raw_llp[0].split("-")
                if len(list) > 1:
                    llp = list[1][:-4]
                    return llp

            return None

    class NAME(SingleExtractor):

        XPATH = '//*[@id="inhalt"]/text()'

    class DESCRIPTION(SingleExtractor):

        # XPATH_TXT = '//*[@id="content"]/div[3]/div[2]/p/text()'
        XPATH = '//*[@id="content"]/div[3]/div[2]/p'

        @classmethod
        def xt(cls, response):
            raw = response.xpath(cls.XPATH).extract()
            html_desc = raw[3:-4]
            return html_desc
            # raw = response.xpath(cls.XPATH_TXT).extract()
            # txt = "".join(raw)
            # return txt

    class MEMBERSHIP(SingleExtractor):

        #XPATH = '//*[@id="content"]/div[3]/div[4]/h3'
        XPATH = '//*[@id="tab-Ausschuesse"]/following-sibling::h3'

        @classmethod
        def xt(cls, response):
            raw_memberships = response.xpath(cls.XPATH)

            memberships = []

            for raw_membership in raw_memberships:
                raw_llp = raw_membership.xpath('a[1]/text()').extract()[1]
                nrbr = u'Nationalrat'
                comittee_llp = None
                if nrbr in raw_llp:
                    comittee_llp = raw_llp.split()[-2][:-1]
                else:
                    nrbr = u'Bundesrat'

                tablerows = raw_membership.xpath('following-sibling::div[1]/table[1]/tbody/tr').extract()

                last_function = u''
                for row in tablerows:
                    row_sel = Selector(text=row)

                    raw_function = row_sel.xpath('//td[@class="biogr_am_funktext"]/text()').extract()
                    if len(raw_function) > 0:
                        function = _clean(raw_function[0])
                        # TODO: standardization should be done on model level
                        # position = cls.standardize_position(position)
                        last_function = function
                    else:
                        function = last_function

                    raw_comittee_link = row_sel.xpath('//td[@class="biogr_am_ausschuss"]/a/@href').extract()
                    if raw_comittee_link:
                        comittee_link = raw_comittee_link[0]
                        comittee_link = "{}/{}".format(BASE_HOST, comittee_link)
                    else:
                        comittee_link = u''

                    comittee_parl_id = COMITTEE.url_to_parlid(comittee_link)

                    raw_comitee_name = row_sel.xpath('//td[@class="biogr_am_ausschuss"]/a/text()').extract()
                    if len(raw_comitee_name) > 0:
                        comittee_name = _clean(raw_comitee_name[0])
                    else:
                        raw_comitee_name = row_sel.xpath('//td[@class="biogr_am_ausschuss"]/text()').extract()
                        if len(raw_comitee_name) > 0:
                            comittee_name = _clean(raw_comitee_name[0])
                        else:
                            comittee_name = u''

                    raw_dates = row_sel.xpath('//td[@class="biogr_am_vonbis"]/text()').extract()[0]
                    if raw_dates:
                        raw_dates = _clean(raw_dates)
                        # \u2013 == - (dash)
                        raw_dates = raw_dates.split(u'\u2013')
                        if len(raw_dates) > 0:
                            raw_from = raw_dates[0]
                            if raw_from is not u'':
                                raw_from = time.strptime(raw_from, '%d.%m.%Y')
                                date_from = datetime.datetime.fromtimestamp(time.mktime(raw_from))
                            else:
                                date_from = None
                        else:
                            date_from = None

                        if len(raw_dates) > 1:
                            raw_to = raw_dates[1]
                            if raw_to is not u'':
                                raw_to = time.strptime(raw_to, '%d.%m.%Y')
                                date_to = datetime.datetime.fromtimestamp(time.mktime(raw_to))
                            else:
                                date_to = None
                        else:
                            date_to = None

                    # we cant add the membership if the parl_id of the comitee is empty
                    if comittee_parl_id is not u'':
                        memberships.append({
                            'comittee':
                                {
                                    'name': comittee_name,
                                    'parl_id': comittee_parl_id,
                                    'nrbr': nrbr,
                                    'legislative_period': comittee_llp,
                                    'source_link': comittee_link
                                },
                            'function': function,
                            'date_from': date_from,
                            'date_to': date_to
                        })

            return memberships

        @classmethod
        def standardize_position(cls, position):

            # Mapping between gendered comitee positions (as written on the parliament website)
            # and standardized positions
            comittee_positions = {
                u'Obfrau': u'Obfrau/Obmann',
                u'Obmann': u'Obfrau/Obmann',
                u'Obfraustellvertreterin': u'ObfraustellvertreterIn/ObmannstellverteterIn',
                u'Obmannstellvertreterin': u'ObfraustellvertreterIn/ObmannstellverteterIn',
                u'Obfraustellvertreter': u'ObfraustellvertreterIn/ObmannstellverteterIn',
                u'Obfraustellvertreterin': u'ObfraustellvertreterIn/ObmannstellverteterIn',
                u'Vorsitzende': u'Vorsitzende/Vorsitzender',
                u'Vorsitzender': u'Vorsitzende/Vorsitzender',
                u'Schriftf\xfchrerin': u'Schriftf\xfchrerIn',
                u'Schriftf\xfchrer': u'Schriftf\xfchrerIn',
                u'Stellvertretende Ausschussvorsitzende':
                    u'Stellvertretende Ausschussvorsitzende/Stellvertretender Ausschussvorsitzender',
                u'Stellvertretende Ausschussvorsitzende':
                    u'Stellvertretende Ausschussvorsitzende/Stellvertretender Ausschussvorsitzender'
            }

            if position in comittee_positions:
                return comittee_positions[position]
            else:
                return position
