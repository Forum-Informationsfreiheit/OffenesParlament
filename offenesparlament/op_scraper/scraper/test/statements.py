# -*- coding: utf-8 -*-
import unittest
import os
from io import open
import urllib2
from scrapy import Selector
from scrapy.http import Request
from parlament.resources.extractors.statement import DOCSECTIONS
from parlament.resources.extractors.statement import SECTION
from parlament.resources.extractors.statement import Paragraph

import logging
logging.basicConfig()

def open_or_fetch(fname, debate_url):
    """
    Helper method to open a debate-protocol from file, or fetch from url and
    save, if file does not exist yet.
    """
    try:
        with open(fname, encoding='windows-1252') as f:
                return f.read()
    except:
        response = urllib2.urlopen(debate_url)
        html = response.read().decode('windows-1252')
        with open(fname, 'w', encoding='windows-1252') as f:
            f.write(html)
        return html

class TestParseDebateXV53(unittest.TestCase):
    """
    Tests docsections extractor with parsing a complete debate protocol
    """

    def setUp(self):
        self.maxDiff = None
        debate_url = "https://www.parlament.gv.at/PAKT/VHG/XXV/NRSITZ/NRSITZ_00053/fnameorig_390290.html"
        fname = os.path.join(os.path.dirname(__file__), 'cache', 'NRSITZ_00053.html')
        content = open_or_fetch(fname, debate_url)
        self.doc = Selector(text=content)

    def test_debate_overview(self):
        sections = DOCSECTIONS.xt(self.doc)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'other']), 2)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'reg']), 355)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'other']), 0)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'pres']), 197)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'abg']), 147)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'min']), 10)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'kanz']), 1)

    def test_speaker_detect(self):
        sections = DOCSECTIONS.xt(self.doc)
        section = sections[39]
        self.assertEquals(section['speaker_id'], 'PAD_51579')
        self.assertTrue(section['full_text'].startswith(u'Frau Präsidentin!'))

    def test_time_and_pages(self):
        sections = DOCSECTIONS.xt(self.doc)

        self.assertEquals(sections[39]['time_start'], [10, 44, 40])
        self.assertEquals(sections[39]['time_end'], [10, 49])

        self.assertEquals(sections[39]['page_start'], 61)
        self.assertEquals(sections[39]['page_end'], 62)
        self.assertEquals(sections[40]['page_start'], 62)
        self.assertEquals(sections[40]['page_end'], 62)
        self.assertEquals(sections[190]['page_start'], 167)
        self.assertEquals(sections[190]['page_end'], 167)
        self.assertEquals(sections[191]['page_start'], 168)
        self.assertEquals(sections[191]['page_end'], 168)

class TestParseDebateXV51(unittest.TestCase):
    """
    Tests docsections extractor with parsing a complete debate protocol
    """

    def setUp(self):
        self.maxDiff = None
        debate_url = "https://www.parlament.gv.at/PAKT/VHG/XXV/NRSITZ/NRSITZ_00051/fnameorig_385039.html"
        fname = os.path.join(os.path.dirname(__file__), 'cache', 'NRSITZ_00051.html')
        content = open_or_fetch(fname, debate_url)
        self.doc = Selector(text=content)

    def test_document_read_successfully(self):
        self.assertEquals(len(self.doc.xpath('//div')), 489,
                          "the number of divs is 489")

    def test_debate_overview(self):
        sections = DOCSECTIONS.xt(self.doc)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'other']), 2)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'reg']), 484)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'other']), 1)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'pres']), 259)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'abg']), 179)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'min']), 45)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'kanz']), 0)

    def test_plaintext_extraction(self):
        unicode_firstp = u"""Für diese Sitzung hat das Bundeskanzleramt über Vertretung von Mitgliedern der Bundesregierung folgende Mitteilungen gemacht:"""
        unicode_secondp = u"""Die Bundesministerin für Familien und Jugend Dr. Sophie Karmasin wird durch die Bundesministerin für Inneres Mag. Johanna Mikl-Leitner vertreten."""
        sections = DOCSECTIONS.xt(self.doc)
        section = sections[3]
        paragraphs = section['full_text'].split('\n\n')
        self.assertEquals(len(paragraphs), 5, "Statement contains 5 paragraphs")
        self.assertEquals(paragraphs[0], unicode_firstp)
        self.assertEquals(paragraphs[1], unicode_secondp)

    def test_annotatedtext_extraction(self):
        unicode_firstp = u"""Für diese Sitzung hat das Bundeskanzleramt über Vertretung von Mitgliedern der Bundesregierung folgende Mitteilungen gemacht:"""
        unicode_secondp = u"""Die Bundesministerin für Familien und Jugend Dr. Sophie Karmasin wird durch die Bundesministerin für Inneres <a class="ref" href="https://www.parlament.gv.at/WWER/PAD_08214/index.shtml">Mag. Johanna Mikl-Leitner</a> vertreten."""
        sections = DOCSECTIONS.xt(self.doc)
        section = sections[3]
        paragraphs = section['annotated_text'].split('</p><p>')
        self.assertEquals(len(paragraphs), 5, "Statement contains 5 paragraphs")
        self.assertEquals(paragraphs[0], '<p>' + unicode_firstp)
        self.assertEquals(paragraphs[1], unicode_secondp)


class TestParseDebateXIII49(unittest.TestCase):
    """
    Tests docsections extractor with parsing a complete debate protocol
    """

    def setUp(self):
        self.maxDiff = None
        debate_url = "https://www.parlament.gv.at/PAKT/VHG/XXIII/NRSITZ/NRSITZ_00049/fnameorig_115155.html"
        fname = os.path.join(os.path.dirname(__file__), 'cache', 'NRSITZ_00049.html')
        content = open_or_fetch(fname, debate_url)
        self.doc = Selector(text=content)

    def test_document_read_successfully(self):
        self.assertEquals(len(self.doc.xpath('//div')), 104,
                          "the number of divs is 104")

    def test_debate_overview(self):
        sections = DOCSECTIONS.xt(self.doc)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'other']), 2)
        self.assertEquals(len([s for s in sections if s['text_type'] == 'reg']), 99)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'other']), 0)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'pres']), 56)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'abg']), 39)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'min']), 4)
        self.assertEquals(len([s for s in sections if s['speaker_role'] == 'kanz']), 0)

    def test_plaintext_extraction(self):
        unicode_firstp = u"""Meine sehr verehrten Damen und Herren!  Herr Bundesminister! Wir haben jetzt von Ihnen 28 Antworten auf 28 Fragen  die niemand gestellt hat, erhalten. Die 28 Fra­gen, die Sie nicht beantwortet haben, werden Sie ein zweites Mal beantworten können, und zwar im parlamentarischen Untersuchungsausschuss. """
        unicode_lastp = u"""Deshalb sehe ich den Untersuchungssausschuss als eine der größten politischen Chancen dieser Republik  und hoffe, dass dieses Haus diese Chance nützt. – Danke schön. """
        sections = DOCSECTIONS.xt(self.doc)
        section = sections[14]
        paragraphs = section['full_text'].split('\n\n')
        self.assertEquals(len(paragraphs), 28, "Statement contains 28 paragraphs")
        self.assertEquals(paragraphs[0], unicode_firstp)
        self.assertEquals(paragraphs[27], unicode_lastp)

    def test_annotatedtext_extraction(self):
        unicode_firstp = u"""Meine sehr verehrten Damen und Herren!  Herr Bundesminister! Wir haben jetzt von Ihnen 28 Antworten auf 28 Fragen <i class="comment">(Abg. Mag. Donnerbauer: Das sind Fakten!),</i> die niemand gestellt hat, erhalten. Die 28 Fra­gen, die Sie nicht beantwortet haben, werden Sie ein zweites Mal beantworten können, und zwar im parlamentarischen Untersuchungsausschuss. <i class="comment">(Beifall bei den Grünen. – Zwischenrufe bei der ÖVP.)</i>"""
        unicode_lastp = u"""Deshalb sehe ich den Untersuchungssausschuss als eine der größten politischen Chancen dieser Republik <i class="comment">(Zwischenruf des Abg. Großruck)</i> und hoffe, dass dieses Haus diese Chance nützt. – Danke schön. <i class="comment">(Beifall bei den Grünen. – Abg. Neuge­bauer: Vorverurteiler!)</i>"""
        sections = DOCSECTIONS.xt(self.doc)
        section = sections[14]
        paragraphs = section['annotated_text'].split('</p><p>')
        self.assertEquals(len(paragraphs), 28)
        self.assertEquals(paragraphs[0], '<p>'+unicode_firstp)
        self.assertEquals(paragraphs[27], unicode_lastp+'</p>')

    def test_timestamp_extraction(self):
        sections = DOCSECTIONS.xt(self.doc)
        self.assertEquals(sections[12]['timestamps'], [[13, 36, 43], [14, 5]])
        self.assertEquals(sections[12]['ref_timestamp'], [14, 5])
        self.assertEquals(sections[13]['timestamps'], [])  # No timestamps here
        self.assertEquals(sections[13]['ref_timestamp'], [14, 5])  # .. use latest from prev
        self.assertEquals(sections[29]['timestamps'], [[15, 11, 6], [15, 11]])

class TestDocsectionsParagraphs(unittest.TestCase):

    def test_detect_speaker_abgeordneter(self):
        abg_paragraph = u"""<p class=MsoNormal style='margin-top:.70em;margin-right:0cm;margin-bottom:.70em; margin-left:0cm'><b><span lang=DE style='display:none'><!--†--></span>Abgeordneter
<A HREF="/WWER/PAD_12907/index.shtml">Fritz&nbsp;Grillitsch</A></b> (&Ouml;VP)<span style='display:none'><!--¦--></span>: Herr <span lang=DE>Bundesminister,
ich bin dir sehr dankbar, dass du aufgrund deiner Produktion in &Ouml;ster&shy;reich.&nbsp;&#8211; Herzlichen Dank
daf&uuml;r. <i>(Abg. <b>Neubauer</b>&nbsp;&#8211; in Richtung &Ouml;VP, eine entsprechen&shy;de Handbewegung andeutend&nbsp;&#8211;:
Klatschen!)</i></span></p>
"""
        par = Selector(text=abg_paragraph).xpath('.//p')[0]
        p = SECTION.get_p(par)
        speaker = SECTION.detect_speaker(p.plain, p.links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_12907')
        self.assertEqual(speaker['role'], 'abg')


    def test_detect_speaker_minister_simple(self):
        abg_paragraph = u"""<p class=MsoNormal style='margin-top:.70em;margin-right:0cm;margin-bottom:.70em; margin-left:0cm'><b><span lang=DE style='display:none'><!--†--></span>Bundesminister f&uuml;r Land- und Forstwirtschaft,
Umwelt und Wasserwirtschaft <A HREF="/WWER/PAD_83296/index.shtml">Ing.&nbsp;Andr&auml;&nbsp;Rupprechter</A></b>: Herr <span lang=DE>Bundesminister,
ich bin dir sehr dankbar, dass du aufgrund deiner Produktion in &Ouml;ster&shy;reich.&nbsp;&#8211; Herzlichen Dank
daf&uuml;r. <i>(Abg. <b>Neubauer</b>&nbsp;&#8211; in Richtung &Ouml;VP, eine entsprechen&shy;de Handbewegung andeutend&nbsp;&#8211;:
Klatschen!)</i></span></p>
"""
        par = Selector(text=abg_paragraph).xpath('.//p')[0]
        p = SECTION.get_p(par)
        speaker = SECTION.detect_speaker(p.plain, p.links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_83296')
        self.assertEqual(speaker['role'], 'min')


    def test_detect_speaker_minister(self):
        # This paragraph has invalid HTML around the speaker link, and
        # only part of the speaker-name+title is enclosed by the link
        paragraph = u"""<p class=MsoNormal><b><span lang=DE style='display:none;letter-spacing:-.2pt'><!--†--></span><span style='letter-spacing:-.2pt'>Bundesminister f&uuml;r Land- und Forstwirtschaft,
Umwelt und Wasserwirtschaft <A HREF="/WWER/PAD_83296/index.shtml">Dipl.-</span>Ing.&nbsp;Andr&auml;&nbsp;Rupprechter</A><span style='display:none'><!--¦--></span>:</b> Grunds&auml;tzlich ist neben dem Heimmarkt
der Exportmarkt au&szlig;erordentlich wichtig f&uuml;r die <span lang=DE>&ouml;sterreichische
Landwirtschaft, Lebensmittelwirtschaft, weshalb wir uns gerade auch aufgrund
der Russland-Krise letztes Jahr bem&uuml;ht haben, zus&auml;tzliche neue
Drittlandm&auml;rkte zu finden. Und das ist tats&auml;chlich gelungen: Der agra&shy;rische
Au&szlig;enhandel hat sich im Jahr&nbsp;2014 trotz der sehr schwierigen
Wirtschafts&shy;bedingungen positiv entwickelt, weist immerhin ein Plus von
2,4&nbsp;Prozent gegen&uuml;ber 2013 auf, trotz des Wegfalls des so wichtigen
Marktes in Russland.</span></p>
"""
        par = Selector(text=paragraph).xpath('.//p')[0]
        p = SECTION.get_p(par)
        speaker = SECTION.detect_speaker(p.plain, p.links)
        # self.assertEqual(speaker['found'], True)
        # self.assertEqual(speaker['id'], 'PAD_12907')
        # self.assertEqual(speaker['role'], 'abg')



class TestDocsectionsDetectSpeaker(unittest.TestCase):
    """
    Testing extraction of speaker attributes from a paragraph.
    """

    def test_clean(self):
        plain = u"""Abgeordneter
[[link2]] (ÖVP): Herr Bundesminister,
ich bin dir sehr dankbar, dass du aufgrund deiner Produktion in Öster­reich. – Herzlichen Dank
dafür."""
        links = [('[[link2]]', Selector(text=u'<A HREF="/WWER/PAD_12907/index.shtml">Fritz&nbsp;Grillitsch</A>').xpath('.//a[@href]')[0])]
        speaker = SECTION.detect_speaker(plain, links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_12907')
        self.assertEqual(speaker['role'], 'abg')
        self.assertTrue(speaker['cleaned'].startswith('Herr Bundesminister'))

    def test_with_linebreak(self):
        plain = u"""Abgeordneter [[link270]]
(STRONACH): Frau Präsidentin! Hohes
Haus! Mei­ne sehr geehrten Fernsehzuschauer! Am Anfang möchte ich
verstanden? Oder warum sind wir nicht dafür? [[com269]]
"""
        links = [('[[link270]]', Selector(text=u'<A HREF="/WWER/PAD_123456/index.shtml">Test&nbsp;Person</A>').xpath('.//a[@href]')[0])]
        speaker = SECTION.detect_speaker(plain, links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_123456')
        self.assertEqual(speaker['role'], 'abg')
        self.assertTrue(speaker['cleaned'].startswith(u'Frau Präsidentin!'))

    def test_no_party_with_comment(self):
        plain = u"""Abgeordneter
[[link496]][[com494]]: Herr
Präsident! Ich nehme das zur Kenntnis. Aber ich hätte mich gefreut,
hätten Sie den Herrn Bundesminister genauso zur Räson gerufen, denn
das wäre längst fällig gewesen. [[com495]]
"""
        links = [('[[link496]]', Selector(text=u'<A HREF="/WWER/PAD_123456/index.shtml">Test&nbsp;Person</A>').xpath('.//a[@href]')[0])]
        speaker = SECTION.detect_speaker(plain, links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_123456')
        self.assertEqual(speaker['role'], 'abg')
        self.assertTrue(speaker['cleaned'].startswith(u'Herr'))


    def test_long(self):
        plain = u"""Bundesminister für Land- und Forstwirtschaft,
Umwelt und Wasserwirtschaft [[link5]]: Herr Bundesminister,
ich bin dir sehr dankbar, dass du aufgrund deiner Produktion in Öster­reich. – Herzlichen Dank
dafür. [[com4]]"""
        links = [('[[link5]]', Selector(text=u'<A HREF="/WWER/PAD_83296/index.shtml">Ing.&nbsp;Andr&auml;&nbsp;Rupprechter</A>').xpath('.//a[@href]')[0])]
        speaker = SECTION.detect_speaker(plain, links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_83296')
        self.assertEqual(speaker['role'], 'min')
        self.assertTrue(speaker['cleaned'].startswith('Herr Bundesminister'))

    def test_colon_inside_comment(self):
        # Here, the colon to delimit speaker part from speech has slipped
        # inside the comment
        raw = """<p class="MsoNormal" style="margin-top:.70em;margin-right:0cm;margin-bottom:.70em; margin-left:0cm"><b><span style="display:none"><!--†--></span>Präsidentin <a href="/WWER/PAD_08240/">Dr.&nbsp;Eva&nbsp;Glawischnig-Piesczek</a><span style="display:none"><!--¦--></span></b> <i>(das Glockenzeichen gebend):</i> Ich bitte um ein bisschen mehr Aufmerksamkeit! Danke.</p>
<p class="MsoNormal" style="margin-top:.70em;margin-right:0cm;margin-bottom:.70em; margin-left:0cm"><b><span style="display:none">&nbsp;</span></b></p>"""
        par = Selector(text=raw).xpath('.//p')[0]
        p = SECTION.get_p(par)
        speaker = SECTION.detect_speaker(p.plain, p.links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_08240')
        self.assertEqual(speaker['role'], 'pres')
        self.assertTrue(speaker['cleaned'].startswith('Ich bitte um ein'))

    def test_detect_speaker2(self):
        raw = """<div><p class="StandardRB" style="margin-bottom:.70em"><a name="R_41346_10"><b><span style="display:none"><!--†--></span>Abgeordneter </b></a><b><a href="/WWER/PAD_01781/">Dr.&nbsp;Wolfgang&nbsp;Schüssel</a></b> (ÖVP) <i>(zur Geschäftsbehandlung)</i><i><span style="display: none"><!--¦--></span>:</i> Ich meine, in der Sache selber haben wir das, glaube ich, zuerst schon besprochen. Es ist Sache des Präsidiums, zu entscheiden. </p>
<p class="StandardRE">Nur, lieber Peter Westenthaler, das Argument halte ich für höchst bedenklich, dass man quasi jetzt einer Vielzahl von Exekutivbeamten unterstellt: Weil sie zu wenig ver­dienen, sind sie korruptionsgefährdet. <i>(Abg. Ing.&nbsp;<b>Westenthaler:</b> Es ist aber so!)</i> Das weise ich mit aller Entschiedenheit zurück, meine Damen und Herren! <i>(Beifall bei ÖVP, SPÖ und Grünen.)</i></p>
<p class="RE" style="margin-bottom:1.20em">16.42</p></div>"""
        par = Selector(text=raw).xpath('.//p')[0]
        p = SECTION.get_p(par)
        speaker = SECTION.detect_speaker(p.plain, p.links)
        self.assertEqual(speaker['found'], True)
        self.assertEqual(speaker['id'], 'PAD_01781')
        self.assertEqual(speaker['role'], 'abg')
        self.assertTrue(speaker['cleaned'].startswith('Ich meine, in der'))

    def test_detect_speaker3(self):
        raw = """<div class=WordSection40>
<p class=RB style='margin-top:1.30em'>10.44<span style='display:none'>.40</span></p>
<p class=StandardRB style='margin-bottom:.80em'><a name="R_129460_7"><b><span style='display:none'><!--†--></span>Abgeordneter <A HREF="/WWER/PAD_51579/index.shtml">Ing.&nbsp;Robert&nbsp;Lugar</A></b>
(STRONACH)</a><span style='display:none'><!--¦--></span>: Frau Pr&auml;sidentin! Hohes
Haus! Mei&shy;ne sehr geehrten Fernsehzuschauer! Am Anfang m&ouml;chte ich
zun&auml;chst eines klarstel&shy;len: Na selbstverst&auml;ndlich wollten wir
immer ein Minderheitsrecht verankern! Ich habe seit sechs Jahren im Parlament
daf&uuml;r gek&auml;mpft, dass das endlich kommen wird, und heute beraten wir
dar&uuml;ber. Es werden das ja auch alle hier einstimmig
beschlie&szlig;en&nbsp;&#8211; au&szlig;er uns. Und jetzt geht es darum zu
erkl&auml;ren, warum. Sind wir so bockig? Oder ha&shy;ben wir es nicht
verstanden? Oder warum sind wir nicht daf&uuml;r? <i>(Abg. <b>Brosz: </b>Ich
glaube eher das Zweitere!&nbsp;&#8211; Abg. <b>Schimanek: </b>Beides!)</i></p>
</div>"""
        par = Selector(text=raw).xpath('.//div')[0]
        section = SECTION.xt(par)
        # print(section['paragraphs'][0].src.encode('utf-8'))
        self.assertEquals(section['speaker_id'], 'PAD_51579')
        self.assertTrue(section['full_text'].startswith(u'Frau Präsidentin!'))



#     def test_invalid(self):
#         plain = u"""Bundesminister für Land- und Forstwirtschaft,
# Umwelt und Wasserwirtschaft [[link3]]Ing. Andrä Rupprechter: Grundsätzlich ist neben dem Heimmarkt
# der Exportmarkt außerordentlich wichtig für die österreichische
# Landwirtschaft, Lebensmittelwirtschaft, weshalb wir uns gerade auch aufgrund
# der Russland-Krise letztes """
#         links = [('[[link5]]', Selector(text=u'<A HREF="/WWER/PAD_83296/index.shtml">Dipl.-</span>Ing.&nbsp;Andr&auml;&nbsp;Rupprechter</A>').xpath('.//a')[0])]
#         speaker = SECTION.detect_speaker(plain, links)
#         self.assertEqual(speaker['found'], True)
#         self.assertEqual(speaker['id'], 'PAD_83296')
#         self.assertEqual(speaker['role'], 'other')
#         self.assertTrue(speaker['cleaned'].startswith('Grundsätzlich ist neben dem'))


class TestMergeParagraphs(unittest.TestCase):
    def test_merge_starts_lowercase(self):
        self.assertEquals(
            SECTION.merge_split_paragraphs(['This is a ', 'test']),
            ['This is a test'])

    def test_donot_merge_startsuppercase(self):
        self.assertEquals(
            SECTION.merge_split_paragraphs(['This is a ', 'Test']),
            ['This is a ', 'Test'])

    def test_merge_remove_hyphen(self):
        self.assertEquals(
            SECTION.merge_split_paragraphs(['Test un-', 'tested']),
            ['Test untested'])

    def test_empty(self):
        self.assertEquals(SECTION.merge_split_paragraphs([]),[])

    def test_emptyfirst(self):
        self.assertEquals(SECTION.merge_split_paragraphs(['', 'test']),
            ['test'])


class TestParagraph(unittest.TestCase):
    def test_get_timestamp(self):
        p = Paragraph.createFromString('<p class="RB">12.45.07</p>')
        self.assertEquals(p.get_timestamp(), [12,45,07])
        p = Paragraph.createFromString('<p class="RB"><!--.-->12.45.07</p>')
        self.assertEquals(p.get_timestamp(), [12,45,07])
        p = Paragraph.createFromString('<p class="RB">12.45</p>')
        self.assertEquals(p.get_timestamp(), [12,45])
        p = Paragraph.createFromString('<p class="RE">12.45.07</p>')
        self.assertEquals(p.get_timestamp(), [12,45,07])
        p = Paragraph.createFromString('<p class="RE">12.45</p>')
        self.assertEquals(p.get_timestamp(), [12,45])
        p = Paragraph.createFromString('<p class="MsoNormal">12.45</p>')
        self.assertEquals(p.get_timestamp(), False)
