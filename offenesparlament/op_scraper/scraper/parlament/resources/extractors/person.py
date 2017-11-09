# -*- coding: utf-8 -*-
import datetime
import roman
import re

from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PERSON:

    class DETAIL:

        class FULL_NAME(SingleExtractor):
            XPATH = '//*[@id="inhalt"]/text()'

        class PHOTO_URL(SingleExtractor):
            XPATH = "//div[contains(concat(' ', normalize-space(@class), ' '), ' teaserPortraitLarge ')]/a/img/@src"

        class PHOTO_COPYRIGHT(SingleExtractor):
            XPATH = "//div[contains(concat(' ', normalize-space(@class), ' '), ' teaserPortraitLarge ')]/a/span/@title"

        class MANDATES:
            XPATH = "//h4[text()='Politische Mandate']/following-sibling::ul[1]/li"

            @classmethod
            def xt(cls, response):
                mandates_raw = response.xpath(cls.XPATH).extract()
                mandates = []
                for mandate in mandates_raw:
                    mandate = _clean(remove_tags(mandate, 'li'))

                    if "<div" in mandate and "</div>" in mandate:
                        mandate = _clean(remove_tags(
                            Selector(text=mandate).xpath("//div").extract()[0],
                            'div'))

                    function = mandate.split(u'<br>')[0].split(',')[0]
                    party = mandate.split(u'<br>')[0].split(',')[1]
                    llp_raw = re.match(
                        '^.*\((.*)\. GP\).*$', function
                        )
                    function = re.sub(
                        '\((.*)\. GP\)','', function
                        ).strip()

                    m_llp_roman_begin = \
                        m_llp_roman_end = \
                            llp_raw.group(1) if llp_raw else ''

                    if u'–' in m_llp_roman_begin:
                        m_llp_roman_begin,m_llp_roman_end = m_llp_roman_begin.split(u'–')

                    for llp in range(roman.fromRoman(m_llp_roman_begin.strip('. ')),
                                    roman.fromRoman(m_llp_roman_end.strip('. '))+1
                                    ) if m_llp_roman_begin else [None]:
                        llp_roman = roman.toRoman(llp) if llp else None

                        # Start Date
                        try:
                            start_date = _clean(
                                mandate.split('<br>')[1].split(u'\u2013')[0])

                            start_date = datetime.datetime.strptime(
                                start_date, "%d.%m.%Y").date()
                        except:
                            logger.error(
                                u"Failed to parse mandate start date: {}".format(start_date))
                            start_date = None

                        # End Date
                        try:
                            end_date = mandate.split(
                                '<br>')[1].split(u'\u2013')
                            if len(end_date) > 1 and end_date[1]:
                                end_date = datetime.datetime.strptime(
                                    _clean(end_date[1]), "%d.%m.%Y").date()
                            else:
                                end_date = None
                        except:
                            logger.error(
                                u"Failed to parse mandate end date: {}".format(end_date))
                            end_date = None

                        mandates.append({
                            'function': function,
                            'party': _clean(party),
                            'start_date': start_date,
                            'end_date': end_date,
                            'llp': llp,
                            'llp_roman': llp_roman,
                        })

                return mandates

        class BIO:
            XPATH = "//h3[contains(concat(' ', normalize-space(@class), ' '), ' hidden ') and text()='Lebenslauf']/following-sibling::p"

            @classmethod
            def xt(cls, response):
                bio = {
                    'birthdate': None,
                    'birthplace': '',
                    'deathdate': None,
                    'deathplace': '',
                    'occupation': ''
                }
                bio_data = response.xpath(cls.XPATH).extract()
                if bio_data:
                    bio_data = bio_data[0]
                else:
                    return bio

                # Birth Data
                for data in bio_data.split('<br>'):
                    birth = Selector(text=data)\
                        .xpath("//em[contains(text(),'Geb.')]/parent::*/text()")\
                        .extract()
                    if birth:
                        birth = birth[0]
                        bio['birthdate'] = _clean(birth.split(',')[0])
                        try:
                            bio['birthdate'] = datetime.datetime.strptime(
                                bio['birthdate'], "%d.%m.%Y").date()
                        except:
                            logger.error("Failed to parse birthdate: {}".format(
                                bio['birthdate']))
                            bio['birthdate'] = None
                        if len(birth.split(',')) > 1:
                            bio['birthplace'] = birth.split(',')[1].strip()

                    # Death Data
                    death = Selector(text=data)\
                        .xpath("//em[contains(text(),'Verst.')]/parent::*/text()")\
                        .extract()
                    if death:
                        death = death[0]
                        bio['deathdate'] = _clean(death.split(',')[0])
                        try:
                            bio['deathdate'] = datetime.datetime.strptime(
                                bio['deathdate'], "%d.%m.%Y").date()
                        except:
                            logger.error("Failed to parse deathdate: {}".format(
                                bio['deathdate']))
                            bio['deathdate'] = None
                        if len(death.split(',')) > 1:
                            bio['deathplace'] = death.split(',')[1].strip()

                    # Occupation
                    occupation = Selector(text=data)\
                        .xpath("//em[contains(text(),'Beruf')]/parent::*/text()")\
                        .extract()
                    if occupation:
                        occupation = occupation[0]
                        bio['occupation'] = occupation.split(',')[0].strip()
                return bio

    class PARTY(SingleExtractor):
        XPATH = '//li'
        XPATH_SHORT = '//li/span/text()'
        XPATH_TITLE = '//li/span/@title'

        class SHORT(SingleExtractor):
            XPATH = '//li/span/text()'

        class TITLE(SingleExtractor):
            XPATH = '//li/span/@title'

        @classmethod
        def xt(cls, selector):
            """
            Extract the elements
            """
            parties_raw = cls._xt(selector)
            parties = []
            for party in parties_raw:
                try:
                    party_short = PERSON.PARTY.SHORT.xt(Selector(text=party))
                    party_title = PERSON.PARTY.TITLE.xt(Selector(text=party))
                    parties.append([party_short, party_title])
                except IndexError:
                    pass
            return parties

    class LIST(SingleExtractor):
        XPATH = '//table//tbody//tr'

        @classmethod
        def xt(cls, response):
            persons = []
            raw_persons = response.xpath(cls.XPATH).extract()
            for raw_person in raw_persons:
                source_link = Selector(text=raw_person).xpath(
                    '//td//a/@href').extract()[0]
                reversed_name = _clean(
                    Selector(text=raw_person).xpath('//td//a/text()').extract()[0])
                if ' siehe ' in reversed_name:
                    reversed_name = reversed_name.split(' siehe ')[1]

                mandates = []
                party_spans = Selector(text=raw_person).xpath(
                    '//td[2]//span').extract()
                for party_span in party_spans:
                    party_short = Selector(text=party_span).xpath(
                        '//span/text()').extract()[0]
                    party_title = '' #disabled because it became huge
                    mandates.append(
                        {'short': party_short, 'title': party_title})

                electoral_state = {
                    'short': Selector(text=raw_person).xpath('//td[last()]//span/text()').extract(),
                    'long': Selector(text=raw_person).xpath('//td[last()]//span/@title').extract()}
                electoral_state['short'] = electoral_state['short'][0] if len(electoral_state['short'])>0 else ''
                electoral_state['long'] = electoral_state['long'][0] if len(electoral_state['long'])>0 else ''

                persons.append({
                    'source_link': source_link,
                    'reversed_name': reversed_name,
                    'mandates': mandates,
                    'electoral_state': electoral_state,
                })

            return persons
