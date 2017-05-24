# -*- coding: utf-8 -*-
import scrapy
import feedparser

from django.core.urlresolvers import reverse

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue
from ansicolor import yellow


from urllib import urlencode

from parlament.settings import BASE_HOST
from parlament.spiders import BaseSpider
from parlament.resources.extractors import *
from parlament.resources.extractors.law import *
from parlament.resources.extractors.prelaw import *
from parlament.resources.extractors.person import *
from parlament.resources.extractors.opinion import *
from parlament.resources.extractors.comittee import *

from parlament.resources.util import _clean


from op_scraper.models import Party
from op_scraper.models import State
from op_scraper.models import Person
from op_scraper.models import Function
from op_scraper.models import Mandate
from op_scraper.models import LegislativePeriod
from op_scraper.models import Comittee
from op_scraper.models import ComitteeMembership

import pytz

import re


class PersonsSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/PARL/filter.psp")

    ALLOWED_LLPS = []

    RSS_TO_FUNCTION = {
        'NR': 'Abgeordnete(r) zum Nationalrat',
        'BR': 'Abgeordnete(r) zum Bundesrat'
    }

    URLOPTIONS_NR = {
        'xdocumentUri': '/WWER/PARL/index.shtml',
        'PR': '',
        'R_BW': 'BL',
        'anwenden': 'Anwenden',
        'GP': '',
        'BL': 'ALLE',
        'STEP': ' ',
        'FR': 'ALLE',
        'M': 'M',
        'NRBR': '',
        'FBEZ': 'FW_008',
        'view': '',
        'WK': 'ALLE',
        'jsMode': '',
        'LISTE': '',
        'W': 'W',
        'letter': '',
        'WP': 'ALLE',
        'listeId': '8',
        'R_WF': 'FR'
    }
    name = "persons"
    title = "Persons Spider"
    persons_scraped = []

    def __init__(self, **kw):
        super(PersonsSpider, self).__init__(**kw)

        if 'llp' in kw:
            try:
                self.ALLOWED_LLPS = [int(kw['llp'])]
            except:
                pass

        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def get_urls(self):
        """
        Overwritten from BaseSpider for non-LLP-based retrieval
        """
        urls = []
        if self.ALLOWED_LLPS:
            llps = LegislativePeriod.objects.filter(
                number__in=self.ALLOWED_LLPS).all()
        else:
            llps = LegislativePeriod.objects.all()
        for llp in llps:
            for nrbr in ['NR', 'BR']:
                urloptions = self.URLOPTIONS_NR.copy()
                urloptions['GP'] = llp.roman_numeral
                urloptions['NRBR'] = nrbr
                url_options = urlencode(urloptions)
                url = "{}?{}".format(self.BASE_URL, url_options)
                urls.append(url)
            self.LLP.append(llp.number)

        return urls

    def parse(self, response):

        # rss = feedparser.parse(response.url)

        persons = PERSON.LIST.xt(response)

        callback_requests = []

        # which llp are we in?
        urloptions = response.url.split('?')[1]

        llp_roman = [opt.split('=')[1]
                     for opt in urloptions.split('&') if opt.split('=')[0] == 'GP']
        llp_item = LegislativePeriod.objects.get(roman_numeral=llp_roman[0])

        # function string
        function = [opt.split('=')[1]
                    for opt in urloptions.split('&') if opt.split('=')[0] == 'NRBR']
        function_str = self.RSS_TO_FUNCTION[function[0]]
        function_item, f_created = Function.objects.get_or_create(
            title=function_str)

        self.logger.info(
            u"Scraping {} persons for LLP {}".format(len(persons), llp_roman))

        # Iterate all persons
        for p in persons:
            # Extract basic data
            parl_id = p['source_link'].split('/')[-2]
            p['source_link'] = "{}{}".format(BASE_HOST, p['source_link'])

            changed = False
            # Create or update simple person's item
            try:
                person_data = {
                    'reversed_name': p['reversed_name'],
                    'source_link': p['source_link']
                }
                person_item, created_person = Person.objects.update_or_create(
                    parl_id=parl_id,
                    defaults=person_data)
            except Exception as e:
                self.logger.warning("Error saving Person {}: {}".format(
                    green(u'[{}]'.format(p['reversed_name'])),
                    e
                ))
                continue
            if created_person:
                self.logger.info(u"Created Person {}".format(
                    green(u'[{}]'.format(p['reversed_name']))))
            else:
                self.logger.info(u"Updated Person {}".format(
                    green(u"[{}]".format(p['reversed_name']))
                ))
            for mandate in p['mandates']:
                party_item = self.get_party_item(mandate)
                state_item = self.get_state_item(p['electoral_state'])
                # Create and append mandate
                try:
                    mandate_item, m_created = Mandate.objects.update_or_create(
                        function=function_item,
                        legislative_period=llp_item,
                        party=party_item,
                        state=state_item)
                except:
                    self.logger.info(
                        red(u"Error saving Mandate {} ({})".format(function_item, party_item)))
                    import ipdb
                    ipdb.set_trace()
                if mandate_item not in person_item.mandates.all():
                    changed = True
                    person_item.mandates.add(mandate_item)
            if changed:
                # In case we added/modified a mandate now,
                latest_mandate_item = person_item.get_latest_mandate()
                person_item.latest_mandate = latest_mandate_item
                self.logger.info(
                    cyan(u"Latest mandate for {} is now {}".format(person_item, latest_mandate_item)))
                person_item.save()

            # First time we encounter a person, we scan her detail page too
            if not parl_id in self.persons_scraped:
                # Create Detail Page request
                req = scrapy.Request(p['source_link'],
                                     callback=self.parse_person_detail)
                req.meta['person'] = {
                    'reversed_name': p['reversed_name'],
                    'source_link': p['source_link'],
                    'parl_id': parl_id
                }
                callback_requests.append(req)
                self.persons_scraped.append(parl_id)
        return callback_requests

    def get_party_item(self, mandate):
        # Do we have this party already?
        party_item, created = Party.objects.update_or_create(
            short=mandate['short'])
        titles = party_item.titles
        if not titles:
            titles = []
        if mandate['title'] not in titles:
            titles.append(mandate['title'])
            party_item.titles = titles
            party_item.save()

        if created:
            self.logger.info(u"Created party {}".format(
                green(u'[{}]: {}'.format(party_item.short, party_item.titles))))

        return party_item

    def get_state_item(self, state):
        # Do we have this state already?
        state_item, created = State.objects.update_or_create(
            name=state['short'],
            title=state['long'])

        if created:
            state_item.save()

            self.logger.info(u"Created state {}: '{}'".format(
                green(u'[{}]'.format(state_item.name)),
                state_item.title))

        return state_item

    def has_changes(self, parl_id, source_link, ts):
        if not Person.objects.filter(
            parl_id=parl_id,
            source_link=source_link
        ).exists():
            return True

        ts = ts.replace(tzinfo=pytz.utc)
        if Person.objects.get(
                parl_id=parl_id,
                source_link=source_link).ts != ts:
            return True
        return False

    def parse_person_detail(self, response):
        """
        Parse a persons detail page
        """
        person = response.meta['person']
        full_name = PERSON.DETAIL.FULL_NAME.xt(response)

        ts = GENERIC.TIMESTAMP.xt(response)
        if not self.IGNORE_TIMESTAMP and not self.has_changes(person['parl_id'], person['source_link'], ts):
            self.logger.info(
                green(u"Skipping Person Detail, no changes: {}".format(
                    full_name)))
            return

        self.logger.info(u"Updating Person Detail {}".format(
            green(u"[{}]".format(person['reversed_name']))
        ))

        bio_data = PERSON.DETAIL.BIO.xt(response)
        profile_photo_url = PERSON.DETAIL.PHOTO_URL.xt(response)
        profile_photo_copyright = PERSON.DETAIL.PHOTO_COPYRIGHT.xt(response)

        try:
            person_data = {
                'ts': ts,
                'photo_link': "{}{}".format(BASE_HOST, profile_photo_url),
                'photo_copyright': profile_photo_copyright,
                'full_name': full_name,
                'reversed_name': person['reversed_name'],
                'birthdate': bio_data['birthdate'],
                'birthplace': bio_data['birthplace'],
                'deathdate': bio_data['deathdate'],
                'deathplace': bio_data['deathplace'],
                'occupation': bio_data['occupation']}

            person_item, created_person = Person.objects.update_or_create(
                source_link=person['source_link'],
                parl_id=person['parl_id'],
                defaults=person_data
            )

            mandates_detail = PERSON.DETAIL.MANDATES.xt(response)
            for mandate in mandates_detail:
                if Party.objects.filter(short=mandate['party']):
                    party = Party.objects.filter(
                        short=mandate['party']).first()
                elif Party.objects.filter(titles__contains=[mandate['party']]):
                    party = Party.objects.filter(
                        titles__contains=[mandate['party']]).first()
                else:
                    self.logger.warning(u"Can't find party {} for mandate".format(
                        yellow(u"[{}]".format(mandate['party']))
                    ))
                    continue
                mq = person_item.mandates.filter(party=party)

                # try to extract LLP from function string
                if "GP)" in mandate['function']:
                    try:
                        m_llp_roman = re.match(
                            '^.*\((.*)\. GP\).*$', mandate['function']).group(1)
                        m_llp = LegislativePeriod.objects.get(
                            roman_numeral=m_llp_roman)
                        mq = mq.filter(legislative_period=m_llp)
                    except:
                        self.logger.warning(u"Can't find llp in function string {}".format(
                            yellow(u"[{}]".format(mandate['function']))
                        ))

                # try to find existing mandate to add in dates
                if mq.count() == 1:
                    md = mq.first()
                    md.start_date = mandate['start_date']
                    if mandate['end_date']:
                        md.end_date = mandate['end_date']
                    md.save()
                    self.logger.info(u"Augmented mandate {} with start-/end-dates: {} - {} ".format(
                        green(u"{}".format(md)),
                        md.start_date,
                        md.end_date
                    ))
            person_item.latest_mandate = person_item.get_latest_mandate()

            person_item.save()
            # Instatiate slug
            person_item.slug

        except Exception as error:
            self.logger.info(
                red(u"Error saving Person {}: \n\t{}".format(full_name, error)))
            #import ipdb
            # ipdb.set_trace()
            return

        try:
            # Parse the Comittee (Ausschuss) memberships for this person
            memberships = COMITTEE.MEMBERSHIP.xt(response)

            for m in memberships:
                comittee = m['comittee']
                if comittee['nrbr'] == u'Nationalrat':
                    if comittee['legislative_period'] is not None:
                        llp = LegislativePeriod.objects.get(
                            roman_numeral=comittee['legislative_period'])
                        comittee['legislative_period'] = llp

                    try:
                        comittee_item, created_comittee = Comittee.objects.update_or_create(
                            parl_id=comittee['parl_id'],
                            nrbr=comittee['nrbr'],
                            legislative_period=comittee['legislative_period'],
                            # source_link=comittee['source_link'],
                            active=comittee[
                                'active'] if 'active' in comittee else True,
                            defaults=comittee)
                        if created_comittee:
                            self.logger.info(u"Created comittee {}".format(
                                green(u"[{}]".format(comittee_item))
                            ))

                        function_data = {
                            'title': m['function'],
                            'short': m['function']
                        }

                        function_item, created_function = Function.objects.get_or_create(
                            **function_data)
                        if created_function:
                            self.logger.info(u"Created function {}".format(
                                green(u"[{}]".format(function_item))
                            ))

                        membership_data = {
                            'date_from': m['date_from'],
                            'comittee': comittee_item,
                            'person': person_item,
                            'function': function_item
                        }

                        membership_item, created_membership = ComitteeMembership.objects.update_or_create(
                            defaults={
                                'date_to': m['date_to']
                            },
                            **membership_data
                        )

                        if created_membership:
                            self.logger.info(u"Created membership {}".format(
                                green(u"[{}]".format(membership_item))
                            ))
                    except Exception as error:
                        self.logger.info(
                            red(u"Error adding Person's comittee membership {} {}: \n\t{}\n\t{}\n".format(full_name, person['source_link'], error, repr(comittee)))
                            )


        except Exception as error:
            self.logger.info(
                red(u"Error adding Person's comittee memberships {}: \n\t{}".format(full_name, error)))
            #import ipdb
            #ipdb.set_trace()
            return
