# -*- coding: utf-8 -*-
import sys
import scrapy
import feedparser
import roman
from urllib import urlencode
from scrapy import log

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue
from ansicolor import magenta

import pytz

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
from parlament.resources.extractors import *
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.resources.extractors.inquiry import *
from parlament.resources.util import _clean

from op_scraper.models import Party
from op_scraper.models import Document
from op_scraper.models import State
from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Keyword
from op_scraper.models import Mandate
from op_scraper.models import Step
from op_scraper.models import Phase
from op_scraper.models import Category
from op_scraper.models import LegislativePeriod
from op_scraper.models import Inquiry
from op_scraper.models import InquiryResponse
from op_scraper.models import Statement


class InquiriesSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/JMAB/filter.psp")

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/JMAB/index.shtml',
        'NRBR': 'NR',
        'anwenden': 'Anwenden',
        'JMAB': 'J_JPR_M',
        'VHG2': 'ALLE',
        'SUCH': '',
        'listeId': '105',
        'FBEZ': 'FP_005'
    }

    name = "inquiries"
    inquiries_scraped = []

    def __init__(self, **kw):
        super(InquiriesSpider, self).__init__(**kw)

        self.start_urls = self.get_urls()
        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Returns a list of URLs to scrape
        """
        # This predefined list of URLs is chosen to include all types of
        # inquiries possible in the Austrian parliament in order to provide a
        # suitable testing surface for new functions.
        # urls = ["https://www.parlament.gv.at/PAKT/VHG/XXV/JPR/JPR_00019/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/JPR/JPR_00016/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06954/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/M/M_00178/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/JEU/JEU_00003/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06758/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/BR/J-BR/J-BR_03089/index.shtml",
        #         "https://www.parlament.gv.at/PAKT/VHG/BR/J-BR/J-BR_03091/index.shtml", "http://www.parlament.gv.at/PAKT/VHG/BR/J-BR/J-BR_01155/index.shtml", "http://www.parlament.gv.at/PAKT/VHG/XX/J/J_06110/index.shtml", "http://www.parlament.gv.at/PAKT/VHG/XX/J/J_06651/index.shtml", "http://www.parlament.gv.at/PAKT/VHG/XX/J/J_04024/index.shtml", "http://www.parlament.gv.at/PAKT/VHG/XX/J/J_04025/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XX/M/M_00178/index.shtml"]
        urls = []

        if self.LLP:
            for i in self.LLP:
                for nrbr in ['NR', 'BR']:
                    roman_numeral = roman.toRoman(i)
                    options = self.URLOPTIONS.copy()
                    options['GP'] = roman_numeral
                    options['NRBR'] = nrbr
                    url_options = urlencode(options)
                    url_llp = "{}?{}".format(self.BASE_URL, url_options)
                    rss = feedparser.parse(url_llp)

                    print "GP {}: {} inquiries from {} [{}]".format(
                        roman_numeral, len(rss['entries']), nrbr, url_llp)
                    urls = urls + [entry['link'] for entry in rss['entries']]

        return urls

    def parse(self, response):
        source_link = response.url
        category = INQUIRY.CATEGORY.xt(response)
        parl_id = response.url.split('/')[-2]
        title = INQUIRY.TITLE.xt(response)
        description = INQUIRY.DESCRIPTION.xt(response)
        sender_objects = []
        callback_requests = []
        ts = GENERIC.TIMESTAMP.xt(response)

        # Inquiries from Bundesrat don't have an LLP => set None
        if("BR" in category):
            LLP = None
        else:
            LLP = LegislativePeriod.objects.get(
                roman_numeral=response.url.split('/')[-4])
        if not self.has_changes(parl_id, LLP, response.url, ts):
            self.logger.info(
                green(u"Skipping Inquiry, no changes: {}".format(
                    title)))
            return

        # Get or create Category object for the inquiry and log to screen if new
        # category is created.
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        # An inquiry can have multiple senders, but only a single recipient.
        # Try/catch in case person does not exist in the database.
        try:
            for sender_object in INQUIRY.SENDER.xt(response):
                sender_objects.append(Person.objects.get(
                    parl_id=sender_object))
        except:
            log.msg(red(u'Sender "{}" was not found in database, skipping Inquiry {} in LLP {}'.format(
                INQUIRY.SENDER.xt(response), parl_id, LLP)))
            return
        try:
            receiver_object = Person.objects.get(
                parl_id=INQUIRY.RECEIVER.xt(response))
        except:
            log.msg(red(u'Receiver "{}" was not found in database, skipping Inquiry {} in LLP {}'.format(
                INQUIRY.RECEIVER.xt(response), parl_id, LLP)))
            return

        # Create or update Inquiry item
        inquiry_item, inquiry_created = Inquiry.objects.update_or_create(
            parl_id=parl_id,
            legislative_period=LLP,
            defaults={
                'title': title,
                'source_link': source_link,
                'description': description,
                'receiver': receiver_object,
                'ts': ts
            }
        )

        # Attach foreign keys
        inquiry_item.keywords = self.parse_keywords(response)
        inquiry_item.documents = self.parse_docs(response)
        inquiry_item.category = cat
        inquiry_item.sender = sender_objects

        response.meta['inquiry_item'] = inquiry_item

        # Dringliche / Urgent inquiries have a different structure for steps
        # and history. This case distinction accomodates these different
        # structures.
        if any("Dringliche" in '{}'.format(s) for s in inquiry_item.keywords.all()):
            if response.xpath('//h2[@id="tab-ParlamentarischesVerfahren"]'):
                self.parse_parliament_steps(response)
        else:
            response_link = self.parse_steps(response)
            if response_link:
                post_req = scrapy.Request("{}{}".format(BASE_HOST, response_link),
                                          callback=self.parse_inquiry_response,
                                          dont_filter=True)
                post_req.meta['inquiry_item'] = inquiry_item

                callback_requests.append(post_req)

        # Save Inquiry item and log to terminal if created or updated.
        inquiry_item.save()

        if inquiry_created:
            logtext = u"Created Inquiry {} with ID {}, LLP {} @ {}"
        else:
            logtext = u"Updated Inquiry {} with ID {}, LLP {} @ {}"

        logtext = logtext.format(
            cyan(title),
            cyan(u"{}".format(parl_id)),
            green(str(LLP)),
            blue(response.url),
            green(u"{}".format(inquiry_item.keywords))
        )
        log.msg(logtext, level=log.INFO)

        log.msg(green("Open Callback requests: {}".format(
            len(callback_requests))), level=log.INFO)

        return callback_requests

    def has_changes(self, parl_id, legislative_period, source_link, ts):
        if not Inquiry.objects.filter(
            parl_id=parl_id,
            legislative_period=legislative_period,
            source_link=source_link
        ).exists():
            return True

        ts = ts.replace(tzinfo=pytz.utc)
        if Inquiry.objects.get(
                parl_id=parl_id,
                legislative_period=legislative_period,
                source_link=source_link).ts != ts:
            return True
        return False

    def parse_keywords(self, response):

        keywords = INQUIRY.KEYWORDS.xt(response)

        # Create all keywords we don't yet have in the DB
        keyword_items = []
        for keyword in keywords:
            kw, created = Keyword.objects.get_or_create(title=keyword)
            if created:
                log.msg(u"Created keyword {}".format(
                    green(u'[{}]'.format(keyword))))
            keyword_items.append(kw)

        return keyword_items

    def parse_docs(self, response):

        docs = INQUIRY.DOCS.xt(response)

        # Create all docs we don't yet have in the DB
        doc_items = []
        for document in docs:
            doc, created = Document.objects.get_or_create(
                title=document['title'],
                html_link=document['html_url'],
                pdf_link=document['pdf_url'],
                stripped_html=None
            )
            doc_items.append(doc)
        return doc_items

    def parse_steps(self, response):
        """
            Callback function to parse the single-page history for normal inquiries
        """

        inquiry_item = response.meta['inquiry_item']

        # Get or created a default-phase for inquiries, because there are no phases in
        # simple inquiries.
        phase_item, created = Phase.objects.get_or_create(
            title='default_inqu')
        if created:
            log.msg(u"Created Phase {}".format(
                green(u'[{}]'.format(phase_item.title))))

        steps = INQUIRY.STEPS.xt(response)

        if "Schriftliche Beantwortung" in steps[-1]["title"]:
            response_link = INQUIRY.RESPONSE_LINK.xt(response)
        else:
            response_link = 0

        for step in steps:
            step_item, created = Step.objects.update_or_create(
                title=step['title'],
                sortkey=step['sortkey'],
                date=step['date'],
                protocol_url=step['protocol_url'],
                inquiry=inquiry_item,
                phase=phase_item,
                source_link=response.url
            )
            step_item.save()
        return response_link

    def parse_parliament_steps(self, response):
        """
        Callback function to parse the additional 'Parlamentarisches Verfahren'
        page.
        """
        inquiry_item = response.meta['inquiry_item']

        phases = INQUIRY.PHASES.xt(response)

        for phase in phases:
            # Create phase if we don't have it yet
            phase_item, created = Phase.objects.get_or_create(
                title=phase['title'])
            if created:
                log.msg(u"Created Phase {}".format(
                    green(u'[{}]'.format(phase_item.title))))

            # Create steps
            for step in phase['steps']:
                step_item, created = Step.objects.update_or_create(
                    title=step['title']['text'],
                    sortkey=step['sortkey'],
                    date=step['date'],
                    protocol_url=step['protocol_url'],
                    inquiry=inquiry_item,
                    phase=phase_item,
                    source_link=response.url
                )
                step_item.save()
                if created:
                    log.msg(u"Created Step {}".format(
                        green(u'[{}]'.format(step_item.title))))

                # Save statements for this step, if applicable
                if 'statements' in step['title']:
                    for stmnt in step['title']['statements']:
                        # Find the person
                        pq = Person.objects.filter(
                            source_link__endswith=stmnt['person_source_link'])
                        if pq.exists() and pq.count() == 1:
                            person_item = pq.first()
                            st_data = {
                                'speech_type': stmnt['statement_type'],
                                'protocol_url': stmnt['protocol_link']
                            }
                            st_item, st_created = Statement.objects.update_or_create(
                                index=stmnt['index'],
                                person=person_item,
                                step=step_item,
                                defaults=st_data)
                            if st_created:
                                log.msg(u"Created Statement by {} on {}".format(
                                    green(
                                        u'[{}]'.format(person_item.full_name)),
                                    step_item.date))
                            else:
                                log.msg(u"Updated Statement by {} on {}".format(
                                    green(
                                        u'[{}]'.format(person_item.full_name)),
                                    step_item.date))
                        else:
                            # We can't save statements if we can't find the
                            # Person
                            log.msg(
                                red(u"Skipping Statement by {}: Person with source_link {} does{} exist{}").format(
                                    green(
                                        u'[{}]'.format(stmnt['person_name'])),
                                    blue(
                                        "[{}]".format(stmnt['person_source_link'])),
                                    red("{}").format(
                                        "" if pq.exists() else " not"),
                                    "" if pq.count() > 1 else ", but {} persons matching found!".format(
                                        pq.count())
                                ))
                            continue

    def parse_inquiry_response(self, response):
        """
        Callback function for parsing the inquiry responses
        """
        inquiry_item = response.meta['inquiry_item']
        source_link = response.url
        parl_id = response.url.split('/')[-2]
        title = INQUIRY.TITLE.xt(response)
        description = INQUIRY.RESPONSEDESCRIPTION.xt(response)
        LLP = inquiry_item.legislative_period
        category = INQUIRY.CATEGORY.xt(response)

        # Get or create Category object for the inquiry and log to screen if new
        # category is created.
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        try:
            sender_object = Person.objects.get(
                parl_id=INQUIRY.RESPONSESENDER.xt(response))
        except:
            log.msg(red(u'Receiver was not found in database, skipping Inquiry {} in LLP {}'.format(
                parl_id, LLP)))
            return

        # Create or update Inquiry item
        inquiryresponse_item, inquiryresponse_created = InquiryResponse.objects.update_or_create(
            parl_id=parl_id,
            legislative_period=LLP,
            defaults={
                'title': title,
                'source_link': source_link,
                'description': description,
                'sender': sender_object
            }
        )

        # Attach foreign Keys
        inquiryresponse_item.documents = self.parse_docs(response)
        inquiryresponse_item.category = cat

        # Save InquiryResponse object
        inquiryresponse_item.save()

        if inquiryresponse_created:
            logtext = u"Created InquiryResponse {} with ID {}, LLP {} @ {}"
        else:
            logtext = u"Updated InquiryResponse {} with ID {}, LLP {} @ {}"

        logtext = logtext.format(
            cyan(title),
            cyan(u"{}".format(parl_id)),
            green(str(LLP)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        inquiry_item.response = inquiryresponse_item
        inquiry_item.save()

        return
