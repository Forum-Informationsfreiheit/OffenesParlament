# -*- coding: utf-8 -*-
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

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
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
from op_scraper.models import Statement


class InquiriesSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/JMAB/filter.psp")

    URLOPTIONS = {
        'view':'RSS',
        'jsMode':'RSS',
        'xdocumentUri':'/PAKT/JMAB/index.shtml',
        'NRBR':'NR',
        'anwenden':'Anwenden',
        'JMAB':'J_JPR_M',
        'VHG2':'ALLE',
        'SUCH':'',
        'listeId':'105',
        'FBEZ':'FP_005'
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
        urls = ["https://www.parlament.gv.at/PAKT/VHG/XXV/JPR/JPR_00019/index.shtml","https://www.parlament.gv.at/PAKT/VHG/XXV/JPR/JPR_00016/index.shtml","https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06954/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/M/M_00178/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/JEU/JEU_00003/index.shtml", "https://www.parlament.gv.at/PAKT/VHG/XXV/J/J_06758/index.shtml"]
        
        """
        if self.LLP:
            for i in self.LLP:
                for nrbr in ['NR']:
                    roman_numeral = roman.toRoman(i)
                    options = self.URLOPTIONS.copy()
                    options['GP'] = roman_numeral
                    options['NRBR'] = nrbr
                    url_options = urlencode(options)
                    url_llp = "{}?{}".format(self.BASE_URL, url_options)
                    rss = feedparser.parse(url_llp)

                    print "GP {}: {} inquiries from {}".format(
                        roman_numeral, len(rss['entries']), nrbr)
                    urls = urls + [entry['link'] for entry in rss['entries']]
        """

        return urls


    def parse(self, response):
        source_link = response.url
        LLP = LegislativePeriod.objects.get(
            roman_numeral=response.url.split('/')[-4])

        parl_id = response.url.split('/')[-2]
        title = INQUIRY.TITLE.xt(response)
        description = INQUIRY.DESCRIPTION.xt(response)
        sender_objects  = []
        for sender_object in INQUIRY.SENDER.xt(response):
            sender_objects.append(Person.objects.get(
                parl_id=sender_object))
        receiver_object = Person.objects.get(
            parl_id=INQUIRY.RECEIVER.xt(response))
        category = INQUIRY.CATEGORY.xt(response)
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        #self.logger.info(u"Inquiry {}/{}: {}".format(green(u'{}'.format(parl_id)), cyan(u'{}'.format(LLP.roman_numeral)), title))
        inquiry_data = {
            'parl_id': parl_id
        }
        
        inquiry_item, inquiry_created = Inquiry.objects.update_or_create(
            parl_id=parl_id,
            defaults=inquiry_data,
            legislative_period=LLP,
            title=title,
            source_link=source_link,
            description=description,
            receiver=receiver_object
            )

        #Attach foreign keys
        inquiry_item.keywords = self.parse_keywords(response)
        inquiry_item.documents = self.parse_docs(response)
        inquiry_item.category = cat
        inquiry_item.sender = sender_objects
        
        response.meta['inquiry_item'] = inquiry_item

        if any("Dringliche" in '{}'.format(s) for s in inquiry_item.keywords.all()):
            if response.xpath('//h2[@id="tab-ParlamentarischesVerfahren"]'):
                self.parse_parliament_steps(response)
        else:    
            step_num = self.parse_steps(response)
            
        inquiry_item.save()
        if inquiry_created:
            logtext = u"Created Inquiry {} with ID {}, LLP {} @ {}"
        else: 
            logtext = u"Updated Inquiry {} with ID {}, LLP {} @ {}"
            
        logtext = logtext.format(
            red(title),
            cyan(u"{}".format(parl_id)),
            green(str(LLP)),
            blue(response.url),
            green(u"{}".format(inquiry_item.keywords))
        )
        log.msg(logtext, level=log.INFO)

        return

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
        inquiry_item = response.meta['inquiry_item']

        phase_item, created = Phase.objects.get_or_create(
            title='default_inqu')
        if created:
            log.msg(u"Created Phase {}".format(
                green(u'[{}]'.format(phase_item.title))))

        steps = INQUIRY.STEPS.xt(response)

        for step in steps:
            step_item, created = Step.objects.update_or_create(
                title = step['title'],
                sortkey = step['sortkey'],
                date = step['date'],
                protocol_url = step['protocol_url'],
                inquiry = inquiry_item,
                phase=phase_item,
                source_link = response.url
                )
            step_item.save()
        return len(steps)

    def parse_parliament_steps(self, response):
        """
        Callback function to parse the additional 'Parlamentarisches Verfahren'
        page
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
