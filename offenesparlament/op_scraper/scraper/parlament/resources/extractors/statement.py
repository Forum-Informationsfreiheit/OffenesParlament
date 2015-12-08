# -*- coding: utf-8 -*-
import datetime
import re
from scrapy import Selector
from django.utils.html import remove_tags
from django.utils.dateparse import parse_datetime

from parlament.resources.extractors import BaseExtractor
from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean
from parlament.settings import BASE_HOST

import logging
logger = logging.getLogger(__name__)

regexStripTags = re.compile('<.*?>')
regexTimestamp = re.compile('([0-9]{1,2} [A-Za-z]{3} [0-9]{4})')
regexFindPage = re.compile('Seite_([0-9]*)\.html')
regexSpeakerId = re.compile('WWER/(PAD_[0-9]*)/')
regexDebateNr = re.compile('/NRSITZ_([0-9]*)/')
SPEAKER_CLASSES = ['Abgeordneter', 'Abgeordnete']
PRES_CLASSES = ['Präsident', 'Präsidentin']
PARAGRAPH_CLASSES = ['MsoNormal', 'StandardRB', 'MsoListBullet']


class RSS_DEBATES(MultiExtractor):

    """
    Debate meta data (inlcuding the url to the detailed transcript) from
    RSS feded.
    """
    XPATH = '//item'

    class RSSITEM(SingleExtractor):

        """
        An rss-item of the feed, representing a single debate.
        """
        class TITLE(SingleExtractor):
            XPATH = './/title/text()'

        class DETAIL_LINK(SingleExtractor):
            XPATH = './/link/text()'

        class DATE(SingleExtractor):
            XPATH = './/pubdate/text()'

        @classmethod
        def xt(cls, response):

            # Debatedate
            dtime = None
            dtime_text = cls.DATE.xt(response)
            try:
                dtime = datetime.datetime.strptime(
                    regexTimestamp.findall(dtime_text)[0], '%d %b %Y')
            except ValueError:
                logger.warn(u"Could not parse date '{}'".format(dtime_text))

            # Protocol URL from description field
            descr = Selector(text=response.xpath('.//description').extract()[0])
            links = filter(lambda v: v.strip().endswith('.html'),
                           descr.xpath('//a/@href').extract())
            protocol_url = ''
            if len(links):
                protocol_url = links[0]

            # Debate-nr from protocol url
            dnr = None
            try:
                dnr = int(regexDebateNr.findall(protocol_url)[0])
            except IndexError, ValueError:
                logger.warn(u"Could not parse debate_nr from '{}'".format(protocol_url))

            return {
                'date': dtime,
                'debate_type': None, #  is part of the url, actually
                'title': cls.TITLE.xt(response),
                'protocol_url': protocol_url,
                'nr': dnr,
                'detail_url': cls.DETAIL_LINK.xt(response)
            }

    @classmethod
    def xt(cls, response):
        return [cls.RSSITEM.xt(item) for item in response.xpath(cls.XPATH)]


class DOCSECTIONS(MultiExtractor):

    """
    Parts of a debate document
    These sections are helpful to construct the statements.
    """
    XPATH = '//div[contains(@class, \'Section\')]'
    pclasses = set()  # to keep track of P's classes we find

    class CLASSINFO(MultiExtractor):
        XPATH = '@class'

    class TIMESTAMPS(MultiExtractor):
        XPATH = './/p[@class="RE"]/span/text()'

    class HREF(SingleExtractor):
        XPATH = '@href'

    class NAME(SingleExtractor):
        XPATH = '@name'

    class TEXT(SingleExtractor):
        XPATH = 'text()'

    class CONTENT(SingleExtractor):
        """
        Main, textual content of the section
        """
        @classmethod
        def xt(cls, response):
            textparts = []
            for txt in response.xpath('p'):
                try:
                    pclass = txt.xpath('@class').extract().pop().strip()
                    if pclass in PARAGRAPH_CLASSES:
                        textparts.append(txt.extract())
                except:
                    # p with no class
                    textparts.append(txt.extract())
                    logger.warning(u"No class in element, but keeping: '{}'"
                                   .format(txt.extract()))

            raw = ' '.join(''.join(textparts).splitlines())
            return {'raw_text': raw,
                    'clean': ''.join(regexStripTags.split(raw)).strip()}

    # def _filter_paragraph(cls, p):
    #     """
    #     Rules whether a paragraph contains text that belongs in
    #     the statement
    #     """
    #     pass

    @classmethod
    def _clean_timestamps(cls, timestamps):
        """
        Parse potential timestamp-strings to numeric (min, sec) tuples
        """
        ts = []
        for t in timestamps:
            try:
                ts.append([int(v) for v in t.split('.')])
            except ValueError:
                logger.warn(u"Value error in timestamp: '{}'".format(t))
        return ts


    @classmethod
    def xt(cls, response):
        """
        Extract sections (statements) from document (protocol)
        """
        sections = []
        current_maxpage = None
        current_timestamp = None

        for item_index, item in enumerate(response.xpath(cls.XPATH)):
            pages = []
            links = []

            # Parse section
            content = cls.CONTENT.xt(item)
            classnames = cls.CLASSINFO.xt(item)
            timestamps = cls.TIMESTAMPS.xt(item)

            # Collect links
            for a in item.xpath('.//a[@href]'):
                links.append((cls.HREF.xt(a), cls.TEXT.xt(a)))

            # Look for page-number
            for a in item.xpath('.//a[@name]'):
                name = cls.NAME.xt(a)
                nms = regexFindPage.findall(name)
                if len(nms):
                    pages.append(int(nms[0]))

            # If we have page(s) or timestamp(s) in this section,
            # keep them for possible later reference
            if len(pages):
                current_maxpage = max(pages)
            timestamps = cls._clean_timestamps(timestamps)
            if len(timestamps):
                current_timestamp = max(timestamps)

            res = {'raw_text': content['raw_text'],
                   'full_text': content['clean'],
                   'doc_section': classnames[0] if len(classnames) else None,
                   'links': links,
                   'timestamps': timestamps,
                   'ref_timestamp': current_timestamp,
                   'page_start': min(pages) if len(pages) else current_maxpage,
                   'page_end': max(pages) if len(pages) else current_maxpage,
                   }
            # res = dict(res.items() +
            #            StatementPostprocess(content).process().items())

            res['text_type'] = StatementPostprocess.detect_sectiontype(res)
            res['speaker_name'] = StatementPostprocess.get_speaker_name(res)
            res['speaker_id'] = StatementPostprocess.get_speaker_id(res)
            res['speaker_role'] = StatementPostprocess.get_speaker_role(res)

            sections.append(res)
        return sections


class StatementPostprocess():

    """
    Extract speaker name, party, title and role
    """

    TAG_SPKR_ROLE_PRES = 'pres'
    TAG_SPKR_ROLE_OTHER = 'other'

    TAG_STMT_REGULAR = 'reg'
    TAG_STMT_OTHER = 'other'

    @classmethod
    def detect_sectiontype(cls, data):
        """ Detect the type of section from the data we extracted
        so far.
            - look at the first link, and test if it links to
              a person profile
            (- alternatively, we could test if the first line
               matches the  regular expression "<title> <name>:" )
        """
        stype = cls.TAG_STMT_OTHER
        if len(data['links']):
            href = data['links'][0][0]
            if 'WWER' in href:
                stype = cls.TAG_STMT_REGULAR
        return stype

    @classmethod
    def get_speaker_name(cls, data):
        if len(data['links']):
            return data['links'][0][1]

    @classmethod
    def get_speaker_id(cls, data):
        if len(data['links']):
            ids = regexSpeakerId.findall(data['links'][0][0])
            if ids:
                return ids[0]

    @classmethod
    def get_speaker_role(cls, data):
        return cls.TAG_SPKR_ROLE_PRES \
               if data['full_text'].startswith(u'Präs') \
               else cls.TAG_SPKR_ROLE_OTHER

