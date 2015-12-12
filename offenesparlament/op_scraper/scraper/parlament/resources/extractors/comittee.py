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
            splitted_url = url.split('/')
            if len(splitted_url) > 3:
                llp = splitted_url[-4]
                raw_parl_id = splitted_url[-2]
                if len(raw_parl_id) > 1:
                    raw_parl_id = raw_parl_id.split('_')
                    parl_id_type = raw_parl_id[0]
                    parl_id_number = int(raw_parl_id[1])
                    parl_id = u'({}/{})'.format(parl_id_number, parl_id_type)
                    return llp, parl_id

        return u'', u''

    class LLP(SingleExtractor):

        XPATH = '//*[@id="content"]/div[1]/p/a[4]/text()'

        @classmethod
        def xt(cls, response):
            raw_llp = response.xpath(cls.XPATH).extract()

            if len(raw_llp) > 0 and u'Nationalrat' in raw_llp[0]:
                llp_list = raw_llp[0].split("-")
                if len(llp_list) > 1:
                    llp = llp_list[1][:-4]
                    llp = llp.lstrip()
                    return llp

            return None

    class NAME(SingleExtractor):

        XPATH = '//*[@id="inhalt"]/text()'
        XPATH_TITLE = '/html/head/title/text()'

        @classmethod
        def xt(cls, response):
            title = response.xpath(cls.XPATH_TITLE).extract()[0]
            name = response.xpath(cls.XPATH).extract()[0]

            if title == name:
                return name
            else:
                full_name = u'{}: {}'.format(title, name)
                return full_name

    class DESCRIPTION(SingleExtractor):

        # XPATH_TXT = '//*[@id="content"]/div[3]/div[2]/p/text()'
        XPATH = '//*[@id="content"]/div[3]/div[2]/p'

        @classmethod
        def xt(cls, response):
            raw = response.xpath(cls.XPATH).extract()
            if len(raw) > 0:
                html_desc = raw[0][3:-4]
                return html_desc
            else:
                return u''
            # raw = response.xpath(cls.XPATH_TXT).extract()
            # txt = "".join(raw)
            # return txt

    class MEETINGS(SingleExtractor):

        XPATH = '//*[@id="tab-Sitzungsueberblick"]/following-sibling::table/tbody'

        @classmethod
        def xt(cls, response):
            raw_meetings = response.xpath(cls.XPATH)

            meetings = []

            for raw_meeting in raw_meetings:
                raw_header_row = raw_meeting.xpath('tr[@class="historyHeader"]')
                raw_date = raw_header_row.xpath('td[1]/text()').extract()

                if len(raw_date) > 0:
                    raw_date = _clean(raw_date[0])
                    if raw_date is not u'':
                        raw_date = time.strptime(raw_date, '%d.%m.%Y')
                        meeting_date = datetime.datetime.fromtimestamp(time.mktime(raw_date))
                    else:
                        meeting_date = None
                else:
                    meeting_date = None

                raw_number = raw_header_row.xpath('td[2]/em/a/text()').extract()
                if len(raw_number) > 0 and u'Sitzung' in raw_number[0]:
                    meeting_number = raw_number[0].split()[0][:-1]
                else:
                    continue  # not a meeting

                raw_document_urls = raw_header_row.xpath('td[2]/a/@href').extract()

                html_link, pdf_link = u"", u""
                for url in raw_document_urls:
                    if url.endswith('.pdf'):
                        pdf_link = url
                        if not pdf_link.startswith(BASE_HOST):
                            pdf_link = "{}/{}".format(BASE_HOST, pdf_link)
                    elif url.endswith('.html'):
                        html_link = url
                        if not html_link.startswith(BASE_HOST):
                            html_link = "{}/{}".format(BASE_HOST, html_link)
                title = u'Tagesordnung der {}. Sitzung des {} am {}'\
                    .format(meeting_number, COMITTEE.NAME.xt(response), str(meeting_date.date()))

                if html_link != u'' or pdf_link != u'':
                    meeting_document = {
                        'title': title,
                        'html_link': html_link,
                        'pdf_link': pdf_link
                    }
                else:
                    meeting_document = None

                raw_rows = raw_header_row.xpath('following-sibling::tr')

                meeting_topics = []

                for raw_row in raw_rows:
                    raw_topic_number = raw_row.xpath('td[1]/text()').extract()

                    if len(raw_topic_number) > 0:
                        topic_number_list = _clean(raw_topic_number[0]).split()
                        if len(topic_number_list) == 2 and topic_number_list[0] == u'TOP':
                            topic_number = int(topic_number_list[1])
                        else:
                            topic_number = 0
                    else:
                        topic_number = 0

                    if topic_number == 0:
                        continue  # not a TOP -> ignore row

                    raw_topic_text = raw_row.xpath('td[2]/text()').extract()

                    if len(raw_topic_text) > 0:
                        topic_text = _clean(raw_topic_text[0])
                        if topic_text.endswith('('):
                            topic_text = topic_text[:-1].rstrip()
                    else:
                        topic_text = u''

                    if len(raw_topic_text) > 1:
                        topic_comment = _clean(raw_topic_text[1])
                        if topic_comment.startswith(')'):
                            topic_comment = topic_comment[:-1].lstrip()
                    else:
                        topic_comment = u''

                    raw_topic_law_id = raw_row.xpath('td[2]/a/text()').extract()

                    if len(raw_topic_law_id) > 0:
                        topic_law_id = u'({})'.format(raw_topic_law_id[0])
                    else:
                        topic_law_id = u''

                    raw_topic_law_link = raw_row.xpath('td[2]/a/@href').extract()

                    if len(raw_topic_law_link) > 0:
                        raw_topic_law_link_splitted = raw_topic_law_link[0].split('/')
                        if len(raw_topic_law_link_splitted) > 3:
                            topic_law_llp = raw_topic_law_link_splitted[3]
                        else:
                            topic_law_llp = u''
                    else:
                        topic_law_llp = u''

                    if topic_law_id != u'':
                        topic_law = {
                            'parl_id': topic_law_id,
                            'llp': topic_law_llp
                        }
                    else:
                        topic_law = None

                    topic = {
                        'number': topic_number,
                        'text': topic_text,
                        'comment': topic_comment,
                        'law': topic_law
                    }

                    meeting_topics.append(topic)

                meeting = {
                    'number': meeting_number,
                    'date': meeting_date,
                    'agenda': meeting_document,
                    'topics': meeting_topics,
                }

                meetings.append(meeting)

            return meetings

    class LAWS(SingleExtractor):

        # Verhandlungsgegenstaende
        XPATH_LAWS = '//*[@id="tab-Verhandlungsgegenstaende"]/following-sibling::div/ul/li/a'
        # Veroeffentlichungen
        XPATH_REPORTS = '//*[@id="tab-VeroeffentlichungenBerichte"]/following-sibling::div/ul/li/a'

        @classmethod
        def xt(cls, response):
            raw_laws = response.xpath(cls.XPATH_LAWS)
            raw_reports = response.xpath(cls.XPATH_REPORTS)

            raw_laws = raw_laws + raw_reports

            laws = []

            for raw_law in raw_laws:
                raw_title = raw_law.xpath('text()').extract()

                if len(raw_title) > 0:
                    law_title = _clean(raw_title[0])
                else:
                    law_title = u''

                raw_link = raw_law.xpath('@href').extract()

                if len(raw_link) > 0:
                    law_link = raw_link[0]
                    law_llp, law_parl_id = COMITTEE.url_to_parlid(law_link)

                    law_link = "{}/{}".format(BASE_HOST, law_link)
                else:
                    # without a link we can't get the necessary info
                    continue
                if law_llp != u'' and law_parl_id != u'':
                    law = {
                        'title': law_title,
                        'source_link': law_link,
                        'parl_id': law_parl_id,
                        'llp': law_llp,
                    }

                    laws.append(law)

            return laws

    class MEMBERSHIP(SingleExtractor):

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
                        # TODO: standardization of functions should be done on model level
                        last_function = function
                    else:
                        function = last_function

                    raw_comittee_link = row_sel.xpath('//td[@class="biogr_am_ausschuss"]/a/@href').extract()
                    if raw_comittee_link:
                        comittee_link = raw_comittee_link[0]
                        comittee_link = "{}/{}".format(BASE_HOST, comittee_link)
                    else:
                        comittee_link = u''

                    _,comittee_parl_id = COMITTEE.url_to_parlid(comittee_link)

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
