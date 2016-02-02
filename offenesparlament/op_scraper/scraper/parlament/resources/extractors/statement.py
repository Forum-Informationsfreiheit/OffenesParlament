# -*- coding: utf-8 -*-
import datetime
import re
import xml
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


class ST():
    regexStripTags = re.compile('<.*?>')

    @classmethod
    def strip_tags(cls, txt):
        try:
            return ''.join(cls.regexStripTags.split(txt))
        except TypeError:
            print("Cannot strip tags from {}".format(txt))
            return ''

regexTimestamp = re.compile('([0-9]{1,2} [A-Za-z]{3} [0-9]{4})')
regexFindPage = re.compile('Seite_([0-9]*)\.html')
regexSpeakerId = re.compile('WWER/(PAD_[0-9]*)/')
regexDebateNr = re.compile('/NRSITZ_([0-9]*)/')
regexLink0 = re.compile('.*?\s?\[\[link\d+\]\](?: \(.*?\))?:\s?', re.U | re.S)
regexAnnotation = re.compile('\[\[(?:link|com)\d+\]\]', re.U | re.S)
SPEAKER_CLASSES = ['Abgeordneter', 'Abgeordnete']
PRES_CLASSES = ['Präsident', 'Präsidentin']
PARAGRAPH_CLASSES = ['MsoNormal', 'StandardRB', 'StandardRE', 'MsoListBullet']


class RSS_DEBATES(MultiExtractor):

    """
    Debate meta data (inlcuding the url to the detailed transcript) from
    RSS feed.
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
            XPATH = './/pubDate/text()'

        class DESCRIPTION(SingleExtractor):
            XPATH = './/description/text()'

        class PROTOCOL_URL(SingleExtractor):
            XPATH = './/a[contains(@href, \'html\')]/@href'

        @classmethod
        def xt(cls, response):

            # Debatedate
            dtime = None
            try:
                dtime = datetime.datetime.strptime(
                    regexTimestamp.findall(cls.DATE.xt(response))[0],
                    '%d %b %Y')
            except (IndexError, ValueError):
                logger.warn(u"Could not parse date '{}'".format(dtime_text))

            # Protocol URL from description field
            descr = Selector(text=cls.DESCRIPTION.xt(response))
            protocol_url = cls.PROTOCOL_URL.xt(descr)

            # Debate-nr from protocol url
            dnr = None
            try:
                dnr = int(regexDebateNr.findall(protocol_url)[0])
            except (IndexError, ValueError):
                logger.warn(
                    u"Could not parse debate_nr from '{}'".format(protocol_url))

            return {
                'date': dtime,
                'debate_type': None,  # is part of the url, actually
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
    Actual debate contents. Statements. parts of a debate document.
    These sections are helpful to construct the statements.
    """
    XPATH = '//div[contains(@class, \'Section\')]'
    pclasses = set()  # to keep track of P's classes we find
    replace_id = 1

    TAG_SPKR_ROLE_PRES = 'pres'
    TAG_SPKR_ROLE_ABG = 'abg'
    TAG_SPKR_ROLE_OTHER = 'other'

    TAG_STMT_REGULAR = 'reg'
    TAG_STMT_OTHER = 'other'

    class CLASSINFO(MultiExtractor):
        XPATH = '@class'

    class TIMESTAMPS(MultiExtractor):
        """
        Paragraphs by classname that indicates timestamp-content
        """
        XPATH = './/p[re:test(@class, "^(RB|RE)")]'

    class HREF(SingleExtractor):
        XPATH = '@href'

    class NAME(SingleExtractor):
        XPATH = '@name'

    class TEXT(SingleExtractor):
        XPATH = 'text()'

    class MULTITEXT(MultiExtractor):
        XPATH = 'text()'

        @classmethod
        def xtclean(cls, el):
            return ''.join([v.strip() for v in cls.xt(el)])

    class CONTENT_PLAIN(SingleExtractor):
        """
        TODO: sometimes , RE classes contain actual text
        """
        @classmethod
        def _is_text(cls, response):
            pclass = None
            try:
                pclass = response.xpath('.//@class').extract().pop().strip()
            except:
                pass
            if pclass in PARAGRAPH_CLASSES or pclass is None:
                return True

        @classmethod
        def xt(cls, response):
            """
            Paragraphs by classname that indicates content of a statement.
            """
            return [t for t in response.xpath('p') if cls._is_text(t)]

    class CONTENT(SingleExtractor):
        """
        Main, textual content of the section
        """
        @classmethod
        def xt(cls, response):
            textparts = []
            for txt in response.xpath('p'):
                textparts.append(txt.extract())
            return '\n\n'.join([' '.join(p.splitlines()) for p in textparts])

    @classmethod
    def _clean_timestamps(cls, timestamps):
        """
        Parse potential timestamp-strings to numeric (min, sec) tuples
        """
        ts = []
        for t in filter(lambda v: len(v) >= 2, timestamps):
            try:
                ts.append([int(v) for v in t.split('.')])
            except ValueError:
                logger.warn(u"Value error in timestamp: '{}'".format(t))
        return ts

    @classmethod
    def paragraph(cls, p):
        """
        Clean raw-html paragraph and replace comments and links
        with placeholders. Return resulting plain text, along with the
        replaced comments and links. Comments and links are each a list of
        tuples: (replace_text:str, replaced_element:Selector) .

        TODO: this method replaces I/comments first (before the links)
            that however means there might be a link inside a comment.
            this would have to be dealt with, e.g. by looking for markup in
            the replaced comments
        """
        html = p.extract()
        comments = []
        links = []
        for i, com in enumerate(p.xpath('.//i')):
            com_extract = com.extract()
            if ST.strip_tags(com_extract).startswith('('):
                repl = '[[com{}]]'.format(cls.replace_id)
                html = html.replace(com_extract, repl)
                comments.append((repl, com))
                cls.replace_id += 1
        for i, a in enumerate(p.xpath('.//a[@href]')):
            a_extract = a.extract()
            repl = '[[link{}]]'.format(cls.replace_id)
            html = html.replace(a_extract, repl)
            links.append((repl, a))
            cls.replace_id += 1

        return ST.strip_tags(html).strip(), comments, links

    @classmethod
    def p_mkplain(cls, p, comments, links):
        """
        Build the final plain-text representation.
        For now, this simply replaces all comments + links placeholders.
        """
        for match in regexAnnotation.findall(p):
            p = p.replace(match, '')
        return p

    @classmethod
    def p_mkannotate(cls, p, comments, links):
        """
        Build the final annotated (html) representation of a paragraph.
        """
        for key, content in comments:
            textel = xml.dom.minidom.Text()
            textel.data = ST.strip_tags(content.extract())
            el = xml.dom.minidom.Element('i')
            el.setAttribute('class', 'comment')
            el.appendChild(textel)
            p = p.replace(key, el.toxml())

        for key, content in links:
            el = xml.dom.minidom.Element('a')
            el.setAttribute('class', 'ref')
            el.setAttribute('href', cls.HREF.xt(content))
            textel = xml.dom.minidom.Text()
            textel.data = cls.MULTITEXT.xtclean(content)
            el.appendChild(textel)
            p = p.replace(key, el.toxml())

        return p

    @classmethod
    def get_speaker_role(cls, textpart):
        """
        By examining the first word of the textpart containing
        the speaker
        """

        if textpart.startswith(u'Präs'):
            return cls.TAG_SPKR_ROLE_PRES
        elif textpart.startswith(u'Abg'):
            return cls.TAG_SPKR_ROLE_ABG
        else:
            return cls.TAG_SPKR_ROLE_OTHER

    @classmethod
    def get_speaker_id(cls, data):
        """
        Get from the first of the extracted links
        """

        if len(data['links']):
            ids = regexSpeakerId.findall(data['links'][0][0])
            if ids:
                return ids[0]

    @classmethod
    def get_speaker_name(cls, data):
        """
        Get from the first of the extracted links
        """

        if len(data['links']):
            return data['links'][0][1]

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
    def merge_split_paragraphs(cls, textparts):
        """
        Re-merge paragraphs that have been divided by pagebreaks, footer lines etc.
        """
        merged = []
        for p in textparts:
            if len(p) and p[0].islower():
                pindx = len(merged) - 1
                if len(merged) and \
                   len(merged[pindx]) and merged[pindx][-1] == '-':
                    merged[pindx] = merged[pindx][0:-1]
                merged[pindx] += p
            else:
                merged.append(p)

        return [' '.join(p.splitlines()) for p in merged]

    @classmethod
    def xt(cls, response):
        """
        Extract sections (statements) from document (protocol)

        A section is a div-element `<div class="WordSection..">` that
        contains a single speech in paragraphs of text.
        It also contains entity-links, i-elements (for explanatory
        comments not part of the actual speech), as well as page-numbers,
        time-stamps and other artefacts.

        """
        sections = []
        current_maxpage = None
        current_timestamp = None

        for item_index, item in enumerate(response.xpath(cls.XPATH)):
            pages = []
            stmt_links = []
            annotated = ""
            plaintext = ""

            # Parse section
            rawtext = cls.CONTENT.xt(item)
            classnames = cls.CLASSINFO.xt(item)
            timestamps = [ST.strip_tags(ts)
                          for ts in cls.TIMESTAMPS.xt(item)]

            # P-looping, carry out annotations
            paragraphs = []
            plain_pars = []
            annotated_pars = []
            speaker_parts = []
            for p in cls.CONTENT_PLAIN.xt(item):
                plain, comments, links = cls.paragraph(p)
                if plain != '':

                    # collect/append all links
                    stmt_links += ([(cls.HREF.xt(a), cls.TEXT.xt(a))
                                    for k, a in links])
                    try:
                        match = regexLink0.findall(plain)[0]
                        plain = plain.replace(match, '')
                        # keep speaker parts for later
                        speaker_parts.append(match)
                    except IndexError:
                        pass

                    paragraphs.append(plain)
                    plain_pars.append(cls.p_mkplain(plain, comments, links))
                    annotated_pars.append(
                        cls.p_mkannotate(plain, comments, links))

            # Attempt to re-merge paragraphs that were split up only by
            # page-breaks of the protocol
            plain_pars = cls.merge_split_paragraphs(plain_pars)

            full_text = "\n\n".join(plain_pars)
            annotated = "\n\n".join(annotated_pars)

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

            res = {'raw_text': rawtext,
                   'full_text': full_text,
                   'annotated_text': annotated,
                   'doc_section': classnames[0] if len(classnames) else None,
                   'links': stmt_links,
                   'timestamps': timestamps,
                   'ref_timestamp': current_timestamp,
                   'time_start': min(timestamps) if len(timestamps) else None,
                   'time_end': max(timestamps) if len(timestamps) else None,
                   'page_start': min(pages) if len(pages) else current_maxpage,
                   'page_end': max(pages) if len(pages) else current_maxpage,
                   }

            res['text_type'] = cls.detect_sectiontype(res)
            res['speaker_name'] = cls.get_speaker_name(res)
            res['speaker_id'] = cls.get_speaker_id(res)

            # Use part of the word-section to detect the speaker-role
            speaker_part = speaker_parts[0] if len(speaker_parts) else ''
            res['speaker_role'] = cls.get_speaker_role(speaker_part)

            sections.append(res)
        return sections
