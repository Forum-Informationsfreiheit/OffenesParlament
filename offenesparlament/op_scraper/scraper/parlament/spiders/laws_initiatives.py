# -*- coding: utf-8 -*-

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from roman import fromRoman

from scrapy import log

import pytz

from parlament.spiders import BaseSpider
from parlament.resources.extractors import *
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.settings import BASE_HOST

from op_scraper.models import Phase
from op_scraper.models import Person
from op_scraper.models import Statement
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion
from op_scraper.models import LegislativePeriod


class LawsInitiativesSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/RGES/filter.psp")

    ALLOWED_LLPS = range(20, 26)

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/RGES/index.shtml',
        'anwenden': 'Anwenden',
        'RGES': 'ALLE',
        'SUCH': ' ',
        'listeId': '103',
        'FBEZ': 'FP_003',
    }

    name = "laws_initiatives"
    title = "Laws & Initiatives Spider"

    def __init__(self, **kw):
        super(LawsInitiativesSpider, self).__init__(**kw)

        if 'llp' in kw:
            try:
                self.LLP = [int(kw['llp'])]
            except:
                pass

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.print_debug()

    def parse(self, response):
        self.SCRAPED_COUNTER += 1

        LLP = LegislativePeriod.objects.get(
            roman_numeral=response.url.split('/')[-4])

        # Extract fields
        ts = GENERIC.TIMESTAMP.xt(response)
        title = LAW.TITLE.xt(response)
        parl_id = LAW.PARL_ID.xt(response)
        status = LAW.STATUS.xt(response)

        if not self.IGNORE_TIMESTAMP and not self.has_changes(parl_id, LLP, response.url, ts):
            self.logger.info(
                green(u"[{} of {}] Skipping Law, no changes: {}".format(
                    self.SCRAPED_COUNTER,
                    self.TOTAL_COUNTER,
                    title)))
            return

        # Extract foreign keys
        category = LAW.CATEGORY.xt(response)
        description = LAW.DESCRIPTION.xt(response)

        # Create category if we don't have it yet
        cat, created = Category.objects.get_or_create(title=category)
        if created:
            log.msg(u"Created category {}".format(
                green(u'[{}]'.format(category))))

        # Create and save Law
        law_data = {
            'title': title,
            'status': status,
            'description': description,
            'ts': ts,
            'source_link': response.url,
        }
        law_item, law_created = Law.objects.update_or_create(
            parl_id=parl_id,
            legislative_period=LLP,
            defaults=law_data)

        # Attach foreign keys
        law_item.keywords = self.parse_keywords(response)
        law_item.category = cat
        law_item.documents = self.parse_docs(response)

        law_item.save()

        # Log our progress
        if law_created:
            logtext = u"[{} of {}] Created {} with id {}, LLP {} @ {}"
        else:
            logtext = u"[{} of {}] Updated {} with id {}, LLP {} @ {}"

        logtext = logtext.format(
            self.SCRAPED_COUNTER,
            self.TOTAL_COUNTER,
            red(title),
            cyan(u"[{}]".format(parl_id)),
            green(unicode(LLP)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        response.meta['law_item'] = law_item

        # is the tab 'Parlamentarisches Verfahren available?'
        if response.xpath('//h2[@id="tab-ParlamentarischesVerfahren"]'):
            self.parse_parliament_steps(response)

        if response.xpath('//h2[@id="tab-VorparlamentarischesVerfahren"]'):
            self.parse_pre_parliament_steps(response)

    def has_changes(self, parl_id, legislative_period, source_link, ts):
        if not Law.objects.filter(
            parl_id=parl_id,
            legislative_period=legislative_period,
            source_link=source_link
        ).exists():
            return True

        ts = ts.replace(tzinfo=pytz.utc)
        if Law.objects.get(
                parl_id=parl_id,
                legislative_period=legislative_period,
                source_link=source_link).ts != ts:
            return True
        return False

    def parse_keywords(self, response):

        keywords = LAW.KEYWORDS.xt(response)

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

        docs = LAW.DOCS.xt(response)

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

    def parse_pre_parliament_steps(self, response):
        """
        Callback function to parse the additional
        'Vorparlamentarisches Verfahren' page
        """
        law_item = response.meta['law_item']
        prelaw_id = LAW.PRELAW_ID.xt(response)
        if Law.objects.filter(parl_id=prelaw_id, legislative_period=law_item.legislative_period):
            prelaw = Law.objects.get(
                parl_id=prelaw_id,
                legislative_period=law_item.legislative_period)
            law_item.references = prelaw
            law_item.save()

    def parse_parliament_steps(self, response):
        """
        Callback function to parse the additional 'Parlamentarisches Verfahren'
        page
        """
        law_item = response.meta['law_item']

        phases = LAW.PHASES.xt(response)

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
                    protocol_url=step['protocol_url'][
                        0] if step['protocol_url'] else u'',
                    law=law_item,
                    phase=phase_item,
                    source_link=response.url
                )
                step_item.save()

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
                                'protocol_url': stmnt['protocol_link'][0] if stmnt['protocol_link'] else None
                            }

                            st_item, st_created = Statement.objects.update_or_create(
                                index=stmnt['index'],
                                person=person_item,
                                step=step_item,
                                defaults=st_data)
                            # if st_created:
                            #     log.msg(u"Created Statement by {} on {}".format(
                            #         green(
                            #             u'[{}]'.format(person_item.full_name)),
                            #         step_item.date))
                            # else:
                            #     log.msg(u"Updated Statement by {} on {}".format(
                            #         green(
                            #             u'[{}]'.format(person_item.full_name)),
                            #         step_item.date))
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
