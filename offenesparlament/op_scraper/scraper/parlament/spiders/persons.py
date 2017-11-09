# -*- coding: utf-8 -*-
import scrapy
import urlparse
import collections

from ansicolor import red
from ansicolor import cyan
from ansicolor import green
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

from django.db.models import Q

import pytz

import re

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PersonsSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "WWER/PARL/filterRearrange.psp")

    ALLOWED_LLPS = []

    RSS_TO_FUNCTION = {
        'NR': 'Abgeordnete(r) zum Nationalrat',
        'BR': 'Abgeordnete(r) zum Bundesrat'
    }

#    URLOPTIONS_NR = {
#        'xdocumentUri': '/WWER/PARL/index.shtml',
#        'PR': '',
#        'R_BW': 'BL',
#        'anwenden': 'Anwenden',
#        'GP': '',
#        'BL': 'ALLE',
#        'FR': 'ALLE',
#        'M': 'M',
#        'NRBR': '',
#        'FBEZ': 'FW_008',
#        'view': '',
#        'WK': 'ALLE',
#        'jsMode': '',
#        'LISTE': '',
#        'W': 'W',
#        'letter': '',
#        'WP': 'ALLE',
#        'listeId': '8',
#        'R_WF': 'FR',
#        'requestId': 'B19D9DFCF0',
# apparently parliaments needs this to be present, maybe even valid
#        'STEP': '2010'
#    }
    name = "persons"
    title = "Persons Spider"
    persons_scraped = []
    start_urls = []

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
        u = ['https://www.parlament.gv.at/WWER/PARL/filter.psp?jsMode=EVAL&xdocumentUri=%2FWWER%2FPARL%2Findex.shtml&NRBR=NR&anwenden=Anwenden&R_WF=FR&FR=ALLE&R_BW=BL&BL=ALLE&W=W&M=M&listeId=8&FBEZ=FW_008', # NR
             'https://www.parlament.gv.at/WWER/PARL/filter.psp?jsMode=EVAL&xdocumentUri=%2FWWER%2FPARL%2Findex.shtml&NRBR=BR&anwenden=Anwenden&R_WF=FR&FR=ALLE&R_BW=BL&BL=ALLE_BL&W=W&M=M&listeId=8&FBEZ=FW_008'] # BR
        urls = []
        if self.ALLOWED_LLPS:
            llps = LegislativePeriod.objects.filter(
                number__in=self.ALLOWED_LLPS).all()
        else:
            llps = LegislativePeriod.objects.all()
        for llp in llps:
            for up in u:
            #    for nrbr in ['NR', 'BR']:
                #urloptions = self.URLOPTIONS_NR.copy()
                #urloptions['GP'] = llp.roman_numeral
            #        urloptions['NRBR'] = nrbr
                #url_options = urlencode(urloptions)
                #url = "{}?{}".format(self.BASE_URL, url_options)
                urls.append(up+'&GP='+llp.roman_numeral)
                if not llp.number in self.LLP:
                    self.LLP.append(llp.number)

        logger.info(u"parsing urls: {}".format(
            ','.join(urls)
        ))
        return urls

    def parse(self, response):
        all_link_followed = False
        try:
            all_links = response.xpath('''//a[starts-with(text(),'Alle anzeigen')]/@href''')
            if len(all_links)>0:
                URLOPTIONS = collections.OrderedDict(
                    urlparse.parse_qsl(
                        urlparse.urlparse(
                            all_links[0].extract()
                        ).query)
                )
                URLOPTIONS['LISTE']=''
                URLOPTIONS['letter']=''
                new_url = '{}?{}'.format(self.BASE_URL,
                                                    urlencode(URLOPTIONS))
                all_link_followed = True
                logger.debug(u"following show all link: {} -> {}".format(
                    green(u'[{}]'.format(new_url)), response.url))

                yield response.follow(new_url,
                                    self.parse_list)
        except:
            if opts['GP'] not in ('KN','PN',):
                raise

        if not all_link_followed:
            urloptions = response.url.split('?')[1]
            opts = dict(urlparse.parse_qsl(urloptions))
            if not opts['GP'] in ('KN','PN',):
                logger.debug(u"no show all link, parsing list directly: {} -> {}".format(
                    green(u'[{}]'.format(new_url)), response.url))
                for x in self.parse_list(response):
                    yield x

    def parse_list(self, response):

        # rss = feedparser.parse(response.url)

        persons = PERSON.LIST.xt(response)
        logger.info(u"parsing list: {}, {} persons".format(
            green(u'[{}]'.format(response.url)), len(persons)))

        callback_requests = []

        # which llp are we in?
        urloptions = response.url.split('?')[1]
        opts = dict(urlparse.parse_qsl(urloptions))

        llp_roman = opts['GP']
        llp_item = LegislativePeriod.objects.get(roman_numeral=llp_roman)

        # function string
        function = opts['NRBR']
        function_str = self.RSS_TO_FUNCTION[function]
        function_item, f_created = Function.objects.get_or_create(
            title=function_str)

        logger.info(
            u"Scraping {} persons for LLP {}, {}".format(len(persons), llp_roman, function))

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
                logger.warning("Error saving Person {}: {}".format(
                    green(u'[{}]'.format(p['reversed_name'])),
                    e
                ))
                continue
            if created_person:
                logger.debug(u"Created Person {}".format(
                    green(u'[{}]'.format(p['reversed_name']))))
            else:
                logger.debug(u"Updated Person {}".format(
                    green(u"[{}]".format(p['reversed_name']))
                ))
            for mandate in p['mandates']:
                party_item = self.get_party_item(mandate)
                state_item = self.get_state_item(p['electoral_state'])
                # Create and append mandate
                try:
                    mandate_items = person_item.mandate_set.filter(
                        Q(function__title__contains='Nationalrat')
                        ).filter(
                        legislative_period=llp_item,
                        party=party_item
                    )
                    if not mandate_items:
                        mandate_items = [person_item.mandate_set.create(
                            function=function_item,
                            legislative_period=llp_item,
                            party=party_item,
                            state=state_item
                        )]
                    mandate_item = mandate_items[0]
                except Exception, e:
                    logger.warning(
                        red(u"Error saving Mandate {} ({}) / Person {}".format(function_item, party_item, person_item.pk)))
                    import ipdb
                    ipdb.set_trace()
            if changed:
                # In case we added/modified a mandate now,
                latest_mandate_item = person_item.get_latest_mandate()
                person_item.latest_mandate = latest_mandate_item
                logger.debug(
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
            logger.info(u"Created party {}".format(
                green(u'[{}]: {}'.format(party_item.short, party_item.titles))))

        return party_item

    def get_state_item(self, state):
        # Do we have this state already?
        state_item, created = State.objects.update_or_create(
            name=state['short'],
            title=state['long'])

        if created:
            state_item.save()

            logger.debug(u"Created state {}: '{}'".format(
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
            logger.debug(
                green(u"Skipping Person Detail, no changes: {}".format(
                    full_name)))
            return

        logger.debug(u"Updating Person Detail {}".format(
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
                party = None
                if mandate['party']:
                    if Party.objects.filter(short=mandate['party']):
                        party = Party.objects.filter(
                            short=mandate['party']).first()
                    elif Party.objects.filter(titles__contains=[mandate['party']]):
                        party = Party.objects.filter(
                            titles__contains=[mandate['party']]).first()
                    else:
                        logger.warning(u"{}: Can't find party {} for mandate".format(
                            person_data['full_name'], yellow(u"[{}]".format(mandate['party']))
                        ))
                        continue

                mandate['party'] = party
                mandate['legislative_period'] = LegislativePeriod.objects.get(
                    roman_numeral=mandate['llp_roman']) if mandate['llp_roman'] else None
                del mandate['llp']
                del mandate['llp_roman']
                mandate['function'],_ = Function.objects.update_or_create(title=mandate['function'])

                def uocparse(mandat, defaults=None):
                    r = {'defaults': {} if not defaults else defaults}
                    for k in mandat.keys():
                        dict_to_append = r if k in (
                            'person','function','party','legislative_period',
                            ) else r['defaults']
                        if dict_to_append==r and mandat[k]==None:
                            dict_to_append[k+'__isnull']=True
                        else:
                            dict_to_append[k]=mandat[k]
                    return r

                ms = Mandate.objects.all()
                mandate['person'] = person_item
                nrbr = False
                ftmp = None
                if 'Abgeordnet' in mandate['function'].title and 'Nationalrat' in mandate['function'].title:
                    nrbr = True
                    ms = ms.filter(
                        Q(function__title__contains='Nationalrat')).filter(
                        Q(function__title__contains='Abgeordnet'))
                    ftmp = mandate['function']
                    del mandate['function']


                p = uocparse(mandate, {} if not nrbr else {'function': ftmp})
                mq = ms.update_or_create(**p)

            person_item.latest_mandate = person_item.get_latest_mandate()

            person_item.save()
            # Instatiate slug
            person_item.slug

        except Exception as error:
            logger.exception(
                red(u"Error saving Person {}: \n\t{}".format(full_name, error)))
            raise error
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
                            logger.debug(u"Created comittee {}".format(
                                green(u"[{}]".format(comittee_item))
                            ))

                        function_data = {
                            'title': m['function'],
                            'short': m['function']
                        }

                        function_item, created_function = Function.objects.get_or_create(
                            **function_data)
                        if created_function:
                            logger.debug(u"Created function {}".format(
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
                            logger.debug(u"Created membership {}".format(
                                green(u"[{}]".format(membership_item))
                            ))
                    except Exception as error:
                        logger.warning(
                            red(u"Error adding Person's comittee membership {} {}: \n\t{}\n\t{}\n".format(full_name, person['source_link'], error, repr(comittee)))
                            )


        except Exception as error:
            logger.warning(
                red(u"Error adding Person's comittee memberships {}: \n\t{}".format(full_name, error)))
            #import ipdb
            #ipdb.set_trace()
            return
