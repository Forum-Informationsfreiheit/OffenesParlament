# -*- coding: utf-8 -*-
import datetime
import re
from xml.dom import minidom
from scrapy import Selector
from django.utils.html import remove_tags
from django.utils.dateparse import parse_datetime

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor

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

regexRSSTimestamp = re.compile('([0-9]{1,2} [A-Za-z]{3} [0-9]{4})')
regexTimestamp = re.compile('(\d{1,2})\.(\d{2})\.?(\d{2})?')
regexFindPage = re.compile('Seite_([0-9]*)\.html')
regexSpeakerId = re.compile('WWER/(PAD_[0-9]*)/')
regexDebateNr = re.compile('/[N,B]RSITZ_([0-9]*)/')
regexSpeakerPart = re.compile('.*?\s?'  # name, title etc. up until link
    '\[\[link\d+\]\]'  # placeholder for link
    '\s?(?:\(.*?\))?'  # optional political party in brackets
    '\s?(?:\[\[com\d+\]\])?'  # optional extra intro/info in brackets
    ':\s?',  # colon plus optional space , delimiter to actual text
    re.U | re.S)
regexAnnotation = re.compile('\[\[(?:link|com)\d+\]\]', re.U | re.S)
regexDuration = re.compile('.*?'
    '(\d{1,2})\.(\d{2}).{1,3}(\d{1,2})\.(\d{2}).?Uhr', re.U | re.S)

# When re-building paragraphs, prefix links with this
linkPrefix = 'https://www.parlament.gv.at'

class Paragraph():

    replace_id = 1  # Used to give unique ids to parts for replacement

    timstamp_css_class = set(['RE', 'RB'])

    class CLASSINFO(MultiExtractor):
        """ Get class attribute """
        XPATH = '@class'

    def __init__(self):
        self.src = ''
        self.plain = ''
        self.links = []
        self.comments = []
        self.cssclasses = []

    def get_timestamp(self):
        """
        If paragraph contains a timestamp, return it as list
        """
        if not self.timstamp_css_class.isdisjoint(self.cssclasses):
            tsmatch = regexTimestamp.match(self.plain.strip())
            if tsmatch is not None:
                return [int(v) for v in tsmatch.groups() if v is not None]
        return False

    def is_empty(self):
        if self.timstamp_css_class.isdisjoint(self.cssclasses):
            return len(self.plain) == 0
        else:
            return len(self.plain) <= 1

    @classmethod
    def createFromString(cls, p):
        return cls.createFromSelector(Selector(text=p).xpath('.//p')[0])

    @classmethod
    def createFromSelector(cls, p):
        """
        Pre-process a paragraph and replace comments and links with
        placeholders. Return resulting plain text, along with the
        replaced comments and links. Comments and links are each a list of
        tuples: (replace_text:str, replaced_element:Selector) .

        TODO: this method replaces I/comments first (before the links)
            that however means there might be a link inside a comment.
            this would have to be dealt with, e.g. by looking for markup in
            the replaced comments
        """
        html = p.extract()
        res = Paragraph()
        res.cssclasses = cls.CLASSINFO.xt(p)
        for i, com in enumerate(p.xpath('.//i')):
            com_extract = com.extract()
            com_plain  = ST.strip_tags(com_extract).strip()
            if com_plain.startswith('('):
                repl = '[[com{}]]'.format(cls.replace_id)
                if com_plain.endswith(':'):
                    # Check for a colon ':' that slipped inside the <i>, but
                    # actually belongs outside. Add it to the plaintext after
                    # the comment by adding it to the replace string
                    # TODO : should remove it from inner-text of comment/<i>
                    # TODO : can happen with other characters as well
                    repl += ':'
                html = html.replace(com_extract, repl)
                res.comments.append((repl, com))
                cls.replace_id += 1
        for i, a in enumerate(p.xpath('.//a[@href]')):
            a_extract = a.extract()
            repl = '[[link{}]]'.format(cls.replace_id)
            html = html.replace(a_extract, repl)
            res.links.append((repl, a))
            cls.replace_id += 1
        res.plain = res.src = ST.strip_tags(html).strip()
        return res


class RSS_DEBATES(MultiExtractor):

    """
    Get the debates metadata (inlcuding urls of transcript) from the RSS feed.
    """
    XPATH = '//item'

    class RSSITEM(SingleExtractor):

        """
        An rss-item of the feed, representing metadata of a single debate.
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
                    regexRSSTimestamp.findall(cls.DATE.xt(response))[0],
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
    Actual debate contents. Statements, parts of a debate document.
    These sections are helpful to construct the statements.
    For llp >= 22, one section corrsponds to one statement - some sections at
    the beginning or end of a protocol exluded.

    The SECTION creates the dictionary with parsed content from the section.
    While looping over the sections, timestamp and page are kept, so both can
    be set to sections where any of them are missing.

    """

    XPATH = '//div[contains(@class, \'Section\')]'

    @classmethod
    def xt(cls, response):
        """
        Extract sections (statements) from document (protocol)

        """
        sections = []
        current_maxpage = None
        current_timestamp = None

        for item_index, item in enumerate(response.xpath(cls.XPATH)):
            res = SECTION.xt(item)
            pages = res['pages']
            timestamps = res['timestamps']

            # If we have page(s) or timestamp(s) in this section,
            # keep them for possible later reference
            if len(pages):
                current_maxpage = max(pages)
            if len(timestamps):
                current_timestamp = max(timestamps)

            # Update the section with the context of the document
            res['ref_timestamp'] = current_timestamp
            res['time_start'] = min(timestamps) if len(timestamps) else None
            res['time_end'] =  max(timestamps) if len(timestamps) else None
            res['page_start'] =  min(pages) - 1 if len(pages) else current_maxpage
            res['page_end'] = max(pages) if len(pages) else current_maxpage

            sections.append(res)

        return sections


class SECTION(SingleExtractor):
    """
    A single section of the protocol.
    A section is a div-element `<div class="WordSection..">` that
    contains a single speech in paragraphs of text.
    It also contains entity-links, i-elements (for explanatory
    comments not part of the actual speech), as well as page-numbers,
    time-stamps and other artefacts.

    In the paragraphs, comments and links are first replaced with placeholders.
    Then, the speaker and role speaker (if any) and the type of the section
    is determined.
    In the end full_text and annotated_text are re-assembled by replacing
    the placeholders again with cleaned links (<a>) and comments (<i>).

    Timestamps and page numbers are also detected.
    """

    # Tags for section-type (is regular debate-speech,
    # or some other text e.g. intro on top of debate protocol)
    TAG_STMT_REGULAR = 'reg'
    TAG_STMT_OTHER = 'other'

    # Tags for speaker role
    TAG_SPKR_ROLE_PRES = 'pres'
    TAG_SPKR_ROLE_ABG = 'abg'
    TAG_SPKR_ROLE_KANZLER = 'kanz'
    TAG_SPKR_ROLE_MINISTER = 'min'
    TAG_SPKR_ROLE_OTHER = 'other'

    class ALL_TEXT(SingleExtractor):
        @classmethod
        def xt(cls, el):
            return ST.strip_tags(el.extract())

    class CLASSINFO(MultiExtractor):
        """ Get class attribute """
        XPATH = '@class'

    class HREF(SingleExtractor):
        """ Get href attribute """
        XPATH = '@href'

    class NAME(SingleExtractor):
        """ Get name attribute """
        XPATH = '@name'

    class RAWCONTENT(SingleExtractor):
        """
        Get raw content of all paragraphs (mainly for comparison to see if
        we missed something with the finer, paragaph-wise extraction).
        """
        @classmethod
        def xt(cls, response):
            textparts = []
            for txt in response.xpath('p'):
                textparts.append(txt.extract())
            return '\n\n'.join([' '.join(p.splitlines()) for p in textparts])

    class PARAGRAPHS(SingleExtractor):
        """
        Extract paragraphs that contain actual (speech) content (as opposed
        to elements that are empty, contain timestamps or are part of the
        footer of protocol-pages.
        """

        PARAGRAPH_CLASSES = [
            # classes that contain content
            'MsoNormal',
            'StandardRB',
            'StandardR',
            'StandardRE',
            'MsoListBullet',
            'MsoBodyText',

            # mostly timestamps
            'RB',
            'RE'

            # problematic (contains content sometimes)
            # 'ZM'
        ]

        @classmethod
        def _is_text(cls, response):
            pclass = None
            try:
                pclass = response.xpath('.//@class').extract().pop().strip()
            except:
                pass
            if pclass in cls.PARAGRAPH_CLASSES or pclass is None:
                return True

        @classmethod
        def xt(cls, response):
            """
            Paragraphs by classname that indicates content of a statement.
            """
            return [t for t in response.xpath('p') if cls._is_text(t)]

    @classmethod
    def get_p(cls, p):
        return Paragraph.createFromSelector(p)

    @classmethod
    def get_speaker_role(cls, textpart):
        """
        Examining first word of textpart to get reference of speaker-role.
        """
        if textpart.startswith(u'Präs'):
            return cls.TAG_SPKR_ROLE_PRES
        elif textpart.startswith(u'Abg'):
            return cls.TAG_SPKR_ROLE_ABG
        elif textpart.startswith(u'Bundeskanz'):
            return cls.TAG_SPKR_ROLE_KANZLER
        elif textpart.startswith(u'Bundesmin'):
            return cls.TAG_SPKR_ROLE_MINISTER
        else:
            return cls.TAG_SPKR_ROLE_OTHER

    @classmethod
    def detect_speaker(cls, plain, links):
        """
        Speaker information. If paragraph contains speaker header.
        Return a dictionary with (name, id, role-tag, cleaned-text, ...) and
        False otherwise.
        Less strict version. Test a few things, then accept it as speaker-info.
        """

        res = {"found": False}
        parts = plain.split(':')
        if len(parts) < 2 or not len(links):
            # must have the colon, must have at least one link
            return res

        speakerpart = parts[0]
        replacecode, link_selector = links[0]

        if replacecode not in speakerpart:
            # speakerpart must contain the first link
            return res

        tokens = speakerpart.split()
        if len(tokens) > 20:
            # must not have more than 20 words before colon
            return res

        name = cls.ALL_TEXT.xt(link_selector)
        personlink = cls.HREF.xt(link_selector)
        ids = regexSpeakerId.findall(personlink)
        speaker_id = ids[0] if len(ids) else None
        role = cls.get_speaker_role(plain)
        replaced = ':'.join(parts[1:]).strip()
        res = {"name":name,
               "id":speaker_id,
               "role": role,
               "found": True,
               "cleaned": replaced}
        return res

    # @classmethod
    # def _detect_speaker2(cls, plain, links):
    #     """
    #     Speaker information.
    #     Regex, (too) strict version.
    #     """
    #     try:
    #         match = regexSpeakerPart.findall(plain)[0]
    #         replacecode, link_selector = links[0]
    #         if replacecode in match:
    #             name = cls.ALL_TEXT.xt(link_selector)
    #             personlink = cls.HREF.xt(link_selector)
    #             ids = regexSpeakerId.findall(personlink)
    #             speaker_id = ids[0] if len(ids) else None
    #             role = cls.get_speaker_role(plain)
    #             replaced = plain.replace(match, '')
    #             return {"name":name, "id":speaker_id, "role": role,
    #                     "found": True, "cleaned": replaced}
    #     except IndexError:
    #         pass
    #     return {"found": False}

    @classmethod
    def xt_duration_ts(cls, rawtext):
        """ Look for duration (from-to) time (hh:mm) patterns in whole text """
        rawtext = ST.strip_tags(rawtext)
        found = []
        for l in rawtext.split("\n"):
            ts_parts = regexDuration.match(l)
            if ts_parts is not None and len(ts_parts.groups()) == 4:
                try:
                    found.append([int(v) for v in ts_parts.groups()[0:2]])
                except:
                    pass
        return found

    @classmethod
    def p_mkplain(cls, p, comments, links):
        """
        Build the final plain-text representation.
        For links, use only the text(); leave out comments entirely.
        """

        # Replace links
        for key, content in links:
            p = p.replace(key, cls.ALL_TEXT.xt(content))

        # Replace/clear the rest
        for match in regexAnnotation.findall(p):
            p = p.replace(match, '')

        return p

    @classmethod
    def p_mkannotate(cls, p, comments, links):
        """
        Build the final annotated (html) representation of a paragraph.
        """
        for key, content in comments:
            textel = minidom.Text()
            textel.data = cls.ALL_TEXT.xt(content)
            el = minidom.Element('i')
            el.setAttribute('class', 'comment')
            el.appendChild(textel)
            p = p.replace(key, el.toxml())

        for key, content in links:
            el = minidom.Element('a')
            el.setAttribute('class', 'ref')
            el.setAttribute('href', linkPrefix + cls.HREF.xt(content))
            textel = minidom.Text()
            textel.data = cls.ALL_TEXT.xt(content)
            el.appendChild(textel)
            p = p.replace(key, el.toxml())

        return p

    @classmethod
    def merge_split_paragraphs(cls, textparts):
        """
        Re-merge paragraphs that have been divided by pagebreaks,
        footer lines etc.
        """
        if not len(textparts):
            return []
        merged = [textparts[0]]
        for p in textparts[1:]:
            if len(p) and p[0].islower():
                pindx = len(merged) - 1
                if len(merged) and len(merged[pindx])>1 \
                        and merged[pindx][-1] == '-':
                    merged[pindx] = merged[pindx][0:-1]
                merged[pindx] += p
            else:
                merged.append(p)
        return [' '.join(p.splitlines()) for p in merged]

    @classmethod
    def xt(cls, item):
        pages = []
        timestamps = []

        # Parse section-classname
        classnames = cls.CLASSINFO.xt(item)

        # Pre-process paragraphs
        paragraphs = []
        for par in [cls.get_p(p) for p in cls.PARAGRAPHS.xt(item)]:
            ts = par.get_timestamp()
            if ts:
                timestamps.append(ts)
            elif not par.is_empty():
                paragraphs.append(par)

        # Look for statement header / speaker information (look in the
        # first paragraphs only)
        # This also removes the speaker-part from the paragraph
        speakerdoc = False
        for par in paragraphs[0:2]:
            speakerdoc = cls.detect_speaker(par.plain, par.links)
            if speakerdoc['found']:
                par.plain = speakerdoc['cleaned']
                break

        # Create the final representation of plaintext and annotated
        # text - also attempt to re-merge paragraphs that belong together
        plain_pars = [cls.p_mkplain(p.plain, p.comments, p.links)\
                      for p in paragraphs]
        plain_pars = cls.merge_split_paragraphs(plain_pars)
        annotated_pars = [cls.p_mkannotate(p.plain, p.comments, p.links)\
                          for p in paragraphs]
        annotated_pars = cls.merge_split_paragraphs(annotated_pars)

        # Look for page-number
        for a in item.xpath('.//a[@name]'):
            name = cls.NAME.xt(a)
            nms = regexFindPage.findall(name)
            if len(nms):
                pages.append(int(nms[0]))

        res = {'raw_text': cls.RAWCONTENT.xt(item),
               'full_text': "\n\n".join(plain_pars),
               'annotated_text': '<p>' + '</p><p>'.join(annotated_pars) + '</p>',
               'doc_section': classnames[0] if len(classnames) else None,
               'timestamps': timestamps,
               'pages': pages,
               'paragraphs': paragraphs
               }

        # Speaker parts
        if speakerdoc is not False and speakerdoc['found']:
            res['text_type'] =  cls.TAG_STMT_REGULAR
            res['speaker_name'] = speakerdoc['name']
            res['speaker_id'] = speakerdoc['id']
            res['speaker_role'] = speakerdoc['role']
        else:
            res['text_type'] =  cls.TAG_STMT_OTHER
            res['speaker_name'] = None
            res['speaker_id'] = None
            res['speaker_role'] = None

        if res['text_type'] == cls.TAG_STMT_OTHER and not len(res['timestamps']):
            # Intro-section that might contain duration of the debate:
            res['timestamps'] += cls.xt_duration_ts(res['raw_text'])

        return res
