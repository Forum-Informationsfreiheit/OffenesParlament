# -*- coding: UTF-8 -*-
import datetime
from django.db import models
from django.utils.html import remove_tags
from django.core.urlresolvers import reverse
from django.test import Client
from phonenumber_field.modelfields import PhoneNumberField
from annoying import fields
from django.contrib.postgres.fields import ArrayField
from django.conf import settings
from django.template.loader import render_to_string
import re
import json
import xxhash
import requests
import collections
import uuid

import markdown
import bleach

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class ParlIDMixIn(object):

    @property
    def parl_id_urlsafe(self):
        return self.parl_id.replace('/', '-').replace('(', '').replace(')', '').replace(' ', '_')


class CONSTANTS():
    PETITIONS_LINK_NAME = "petitionen"
    LAWS_LINK_NAME = "gesetze"


class Timestamped(models.Model):
    ts = models.DateTimeField(null=True)

    class Meta:
        abstract = True


class LlpManager(models.Manager):

    def get_current(self):
        llp = LegislativePeriod.objects.latest('start_date')
        return llp


class LegislativePeriod(models.Model):

    """
    A single legislative Period or 'Legislaturperiode'
    """

    number = models.IntegerField()
    roman_numeral = models.CharField(unique=True, max_length=255, default="")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    objects = LlpManager()

    def __unicode__(self):
        if self.end_date:
            rep_str = u"{} ({} – {})".format(
                self.roman_numeral,
                self.start_date,
                self.end_date)
        else:
            rep_str = u"{} (seit {})".format(
                self.roman_numeral,
                self.start_date)

        return rep_str

    @property
    def facet_repr(self):
        if self.end_date:
            rep_str = u"{} – {} ({})".format(
                self.start_date,
                self.end_date,
                self.roman_numeral)
        else:
            rep_str = u"aktuell seit {} ({})".format(
                self.start_date,
                self.roman_numeral)

        return rep_str

    @classmethod
    def get(cls, roman_numeral):
        try:
            return LegislativePeriod.objects.filter(roman_numeral=roman_numeral).get()
        except:
            return None


class Phase(models.Model):

    """
    A phase in the process of a law, grouping steps together
    """
    title = models.CharField(max_length=1023)

    def __unicode__(self):
        return self.title

    @property
    def title_extended(self):
        return self.title.replace('NR', 'Nationalrat').replace('BR', 'Bundesrat')


class Entity(models.Model):

    """
    An organisation or person commenting in a pre-parliamentary process (prelaw)
    """
    title = models.CharField(max_length=1023)
    title_detail = models.CharField(max_length=1023)
    email = models.EmailField(null=True, blank=True)
    phone = PhoneNumberField(null=True, blank=True)

    class Meta:
        unique_together = ("title", "title_detail")

    def __unicode__(self):
        return self.title


class Document(models.Model):

    """
    A linked document

    Optionally with stripped html content of html-version
    """
    title = models.CharField(max_length=1023)
    pdf_link = models.URLField(max_length=255, null=True)
    html_link = models.URLField(max_length=255, null=True)
    stripped_html = models.TextField(null=True)

    def __unicode__(self):
        return self.title


class PressRelease(models.Model, ParlIDMixIn):

    """
    A press release produced by the parliamentary staff
    """
    title = models.CharField(max_length=1023)
    subtitle = models.CharField(max_length=1023)
    full_text = models.TextField()
    release_date = models.DateField()
    source_link = models.URLField(max_length=255, default="")
    parl_id = models.CharField(max_length=30, unique=True, default="")
    topics = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class Category(models.Model):

    """
    A category for a law, prelaw, anfrage, beantwortung, etc.
    """
    title = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.title


class Keyword(models.Model):

    """
    A keyword assigned to laws and prelaws
    """
    title = models.CharField(max_length=255, unique=True)
    _title_urlsafe = models.CharField(max_length=255, default="")

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']

    @property
    def title_urlsafe(self):
        if not self._title_urlsafe:
            result = re.sub(r'[\.(), -]+', '-', self.title)
            self._title_urlsafe = re.sub(r'^-|-$', '', result)
            self.save()
        return self._title_urlsafe


class Law(Timestamped, ParlIDMixIn):

    """
    A single 'Verhandlungssache' or negotiable matter

    Can also be a prelaw (Vorparlamentarischer Prozess,
        i.e. Ministerialentwurf)

    """
    title = models.CharField(max_length=1023)
    status = models.TextField(null=True, blank=True)
    source_link = models.URLField(max_length=255, default="")
    parl_id = models.CharField(max_length=30, default="")

    description = models.TextField(blank=True)

    # Interna, Utilities
    _slug = models.CharField(max_length=255, default="")

    # Relationships
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="laws")
    press_releases = models.ManyToManyField(PressRelease, related_name="laws")
    documents = models.ManyToManyField(Document, related_name="laws")
    legislative_period = models.ForeignKey(
        LegislativePeriod, null=True, blank=True)
    references = models.OneToOneField(
        "self", blank=True, null=True, related_name="laws")

    def PRETTY_PHASES_LAW(self):
        just_spans = lambda s,g: u''.join(
                u'<span class="timeline_{k} timeline_value">{v}</span>'.format(k=k,v=v)
                for k,v in g.iteritems()) if hasattr(g,'iteritems') else None
        LAW_PHASES = [
                ['Vorparlamentarisches Verfahren', 'vorparl',
                    [
                        ['vp_ein', 'Entwurf eingegangen', r'^Einlangen im Nationalrat',
                            lambda s,g: """<span class="date">%s</span>""" % s.date.strftime('%d.%m.%Y')
                        ],
                        ['vp_st', 'Stellungnahmen', lambda x:
                            {'count': x.law.opinions.all().count(), 'end': x.title.replace('Ende der Begutachtungsfrist','').strip(' :')} if
                            'Ende der Begutachtungsfrist' in x.title and
                            x.law.opinions.all().count() else False,
                            just_spans],
                    ],
                ],
                ['Parlamentarisches Verfahren', 'parl',
                    [
                        ['nr_ein', 'Einlangen im Nationalrat', r'^Einlangen im Nationalrat',
                            lambda s,g: """<span class="date">%s</span>""" % s.date.strftime('%d.%m.%Y')
                            ],
                        ['nr_auss', 'Ausschuss', r': Zuweisung an den (?P<ausschuss>.*)',
                            lambda s,g:
                                just_spans(s,g)+u"""
                                <span class="date">%s</span>
                                """ % s.date.strftime('%d.%m.%Y')
                            ],
                        ['nr_plen', 'Plenarberatung',
                            r'Sitzung des Nationalrates',
                            lambda s,g: u"""<span class="text">%s</span>
                            <span class="date">%s</span>
                            """ % ( s.title.split(' der ',2)[-1].replace('Nationalrates','NR'),
                                s.date.strftime('%d.%m.%Y'),)
                            ],
                        ['nr_besch', 'Beschluss im Nationalrat', r'Gesetzesvorschlag in dritter Lesung',
                            lambda s,g: u"""
                                <span class="results">Dafür:%s</span>
                            """ % s.title.lower().split(u'dafür:',1)[1].replace('dagegen:','<br />Dagegen:') \
                                if u'dafür:' in s.title.lower() else
                                        'Angenommen'
                            ],
                        ['br_besch', 'Beschluss im Bundesrat', r'Beschluss im Bundesrat',
                            lambda s,g: u"""<span class="date">%s</span>""" % s.date.strftime('%d.%m.%Y')
                            ],
                    ]
                ]
            ]

        return LAW_PHASES

    def PRETTY_PHASES(self):
        PHASES = []
        if self.category and self.category.title in ('Gesetzentwurf',
                'Regierungsvorlage: Bundes(verfassungs)gesetz',):
            PHASES = self.PRETTY_PHASES_LAW()

#        if self.category.title in (u'Schriftliche Anfrage',
#                u'Anfragebeantwortung',):
#            PHASES = ['','',
#                    [
#                        ['ein', 'Einlangen im Nationalrat',r'^Einlangen im Nationalrat']
#                        ['ant', 'Beantwortung', r'asdf']
#                    ]
#                ]

        if not PHASES:
            return None

        steps = []

        if self.references:
            steps = steps + list(self.references.steps.all())

        steps = steps + list(self.steps.all())

        remaining_steps = steps

        for large_key, large_slug, stepdefs in PHASES:
            for stepdef in stepdefs:
                stepslug, steptitle, stepre, steptextf = stepdef

                for i,s in enumerate(remaining_steps):
                    refind = None
                    if not callable(stepre):
                        refind = re.search(stepre, s.title)
                        if refind:
                            refind = refind.groupdict() or True
                    else:
                        refind = stepre(s)
                    if refind:
                        stepdef.append(s)
                        stepdef.append(refind)
                        stepdef.append(steptextf(s,refind))
                        remaining_steps = remaining_steps[i+1:]
                        break

        return PHASES


    def api_slug(self):
        return "/api/laws/{}".format(self.pk)

    def steps_by_phases(self):
        """
        Returns a dict of phases containing the steps for display purposes
        """
        phases = collections.OrderedDict()
        for step in self.steps.all():
            if step.phase not in phases:
                phases[step.phase] = []
            phases[step.phase].append(step)

        return phases

    def steps_and_phases_json(self):
        """
        Returns a json representation of the steps_by_phases dict
        """
        steps = []
        for step in self.steps.all():
            steps.append({
                'pk': step.pk,
                'title': step.title,
                'phase': step.phase.title,
                'sortkey': step.sortkey,
                'date': step.date.isoformat(),
                'protocol_url': step.protocol_url,
                'source_link': step.source_link
            })

        return json.dumps(steps)

    def opinions_and_documents(self):
        return self.opinions.all().prefetch_related('documents')

    def opinions_json(self):
        """
        Returns a json representation of the opinios
        """
        ops = []
        for op in self.opinions.all():

            docs = []
            for d in op.documents.all():
                docs.append({
                    'title': d.title,
                    'pdf_link': d.pdf_link,
                    'html_link': d.html_link,
                })
            ops.append(
                {
                    'pk': op.pk,
                    'parl_id':  op.parl_id,
                    'date':  op.date.isoformat() if op.date else '',
                    'description':  op.description,
                    'source_link':  op.source_link,
                    'documents':  docs,
                    'keywords':  [kw.title for kw in op.keywords.all()],
                    'prelaw': op.prelaw.id,
                    'entity': op.entity.title if op.entity else None
                }
            )
        return json.dumps(ops)

    def documents_json(self):
        """
        Returns a json representation of the documents
        """
        docs = []
        for doc in self.documents.all():

            docs.append({
                'pk': doc.pk,
                'title': doc.title,
                'pdf_link': doc.pdf_link,
                'html_link': doc.html_link,
            })
        return json.dumps(docs)

    @property
    def llp_roman(self):
        if self.legislative_period:
            return self.legislative_period.roman_numeral
        else:
            return None

    @property
    def llps_facet(self):
        if self.legislative_period:
            return [self.legislative_period.facet_repr]
        else:
            return []

    @property
    def llps_facet_numeric(self):
        if self.legislative_period:
            return [self.legislative_period.number]
        else:
            return []

    @property
    def keyword_titles(self):
        return [kw.title for kw in self.keywords.all()]

    class Meta:
        unique_together = ("parl_id", "legislative_period")
        select_on_save = True

    @property
    def short_title(self):
        return (self.title[:100] + '...') if len(self.title) > 100 else self.title

    @property
    def slug(self):
        if not self._slug:
            if self.llp_roman:
                self._slug = reverse(
                    'gesetz_detail',
                    kwargs={
                        'parl_id': self.parl_id_urlsafe,
                        'ggp': self.llp_roman
                    }
                )
            else:
                self._slug = reverse(
                    'gesetz_detail',
                    kwargs={
                        'parl_id': self.parl_id_urlsafe
                    }
                )
            self.save()

        return self._slug

    @property
    def simple_status(self):
        if self.status is None:
            return 'offen'
        elif self.status.startswith('Beschlossen'):
            return 'beschlossen'
        elif self.status.startswith('Gesetzesantrag abgelehnt'):
            return 'abgelehnt'
        elif self.status.startswith(u'Zurückgezogen'):
            return 'zurückgezogen'
        elif self.status == 'response_received':
            return 'beantwortet'
        else:
            return 'offen'

    def __unicode__(self):
        return self.title


class Opinion(models.Model, ParlIDMixIn):

    """
    A comment in the pre-parliamentary process by an entity
    """
    parl_id = models.CharField(max_length=120, unique=True, default="")
    date = models.DateField(null=True)
    description = models.TextField(blank=True)
    source_link = models.URLField(max_length=255, default="")

    # Relationships
    documents = models.ManyToManyField(Document)
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword)
    entity = models.ForeignKey(Entity, related_name='opinions')
    prelaw = models.ForeignKey(Law, related_name='opinions')

    class Meta:
        ordering = ['date']

    def __unicode__(self):
        return u'{} zu {}'.format(self.entity.title, self.prelaw.parl_id)


class Administration(models.Model):

    """
    An administration ('Regierung')
    """
    title = models.CharField(max_length=255, default="", unique=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)


class Function(models.Model):

    """
    A parliamentary function, like Abgeordnete or Mitglied des Bundesrates
    """
    title = models.CharField(max_length=1023)
    short = models.CharField(max_length=255)

    class Meta:
        unique_together = ("title", "short")

    def __unicode__(self):
        if self.title:
            return u"{} ({})".format(self.short, self.title)
        return self.title

    # Todo write method that scans function string for political party
    # shortform, e.g. ÖVP


class Party(models.Model):

    """
    A political party, or 'Klub'
    """
    titles = ArrayField(
        models.CharField(max_length=255),
        blank=True,
        null=True)

    short = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.short

    @property
    def short_css_class(self):
        return self.short.lower().replace(u'ä', 'ae').replace(u'ö', 'oe').replace(u'ü', 'ue')


class State(models.Model):

    """
    A state or wahlkreis in Austria
    """
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=1023)


class Mandate(models.Model):

    """
    A political Mandate for a certain function, with a start and possibly an
    end date
    """
    person = models.ForeignKey('Person')
    function = models.ForeignKey(Function)
    party = models.ForeignKey(Party, null=True, blank=True)

    # optional start_date and end_date
    # sometimes the mandates do not run as long as their legislative period
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Relationsships
    legislative_period = models.ForeignKey(
        LegislativePeriod, blank=True, null=True)
    state = models.ForeignKey(State, blank=True, null=True)
    # regierung, for instance, Faymann II
    administration = models.ForeignKey(Administration, blank=True, null=True)

    def __unicode__(self):
        return u"{} ({}), {} ".format(
            self.function,
            self.party,
            self.legislative_period)

    def _json(self):
        mandate = {}
        mandate['llp'] = unicode(self.legislative_period)
        mandate['pk'] = self.pk

        # If we have given start- and end-dates, take them
        # else take the ones from the legislative period
        if self.start_date or self.end_date:
            mandate['start_date'] = self.start_date.isoformat()
            mandate[
                'end_date'] = self.end_date.isoformat() if self.end_date else None
        else:
            if self.administration:
                adm = self.administration
                mandate['administration'] = {
                    "title": adm.title,
                    "start_date": adm.start_date.isoformat(),
                    "end_date": adm.end_date.isoformat() if adm.end_date else None,
                }
                mandate['start_date'] = adm.start_date.isoformat()
                mandate[
                    'end_date'] = adm.end_date.isoformat() if adm.end_date else None
            elif self.legislative_period:
                llp = self.legislative_period
                mandate['start_date'] = llp.start_date.isoformat()
                mandate[
                    'end_date'] = llp.end_date.isoformat() if llp.end_date else None

        if self.function:
            mandate['function'] = {
                "title": self.function.title,
                "short": self.function.short,
            }
        if self.state:
            mandate['state'] = {
                "title": self.state.title,
                "name": self.state.name,
            }
        if self.party:
            mandate['party'] = {
                "titles": self.party.titles,
                "short": self.party.short,
                "short_css_class": self.party.short_css_class,
            }
        return mandate

    def latest_end_date(self):

        if self.end_date:
            return self.end_date

        if self.legislative_period and self.legislative_period.end_date:
            return self.legislative_period.end_date

        if self.administration and self.administration.end_date:
            return self.administration.end_date

        return None

    def earliest_start_date(self):

        if self.start_date:
            return self.start_date

        if self.legislative_period and self.legislative_period.start_date:
            return self.legislative_period.start_date

        if self.administration and self.administration.start_date:
            return self.administration.start_date

        return None


class Person(Timestamped, ParlIDMixIn):

    """
    A single person in parliament, including Abgeordnete, Regierungsmitglieder,
    etc.
    """
    parl_id = models.CharField(max_length=30, primary_key=True)
    source_link = models.URLField(max_length=255, default="")
    photo_link = models.URLField(max_length=255, default="")
    photo_copyright = models.CharField(max_length=255, default="")
    full_name = models.CharField(max_length=255)
    reversed_name = models.CharField(max_length=255)
    birthdate = models.DateField(null=True, blank=True)
    birthplace = models.CharField(max_length=255, null=True, blank=True)
    deathdate = models.DateField(null=True, blank=True)
    deathplace = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)

    # Interna, Utilities
    _slug = models.CharField(max_length=255, default="")

    # Relationsships
    latest_mandate = models.ForeignKey(
        Mandate, related_name='latest_mandate', null=True, blank=True,
        on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.full_name or self.reversed_name

    def api_slug(self):
        return "/api/persons/{}".format(self.pk)

    @property
    def party(self):
        if self.latest_mandate is not None:
            return self.latest_mandate.party
        return None

    @property
    def llps(self):
        return list(set([
            m.legislative_period
            for m in self.mandate_set.all().order_by('-legislative_period__end_date')
            if m.legislative_period]))

    @property
    def llps_roman(self):
        return [llp.roman_numeral for llp in self.llps]

    @property
    def llps_facet(self):
        return [llp.facet_repr for llp in self.llps]

    @property
    def llps_facet_numeric(self):
        return [llp.number for llp in self.llps]

    def get_latest_mandate(self):
        """
        Returns the most recent mandate a person had.

        WARNING: This is a costly function and should only be used during
        scraping, not during list display of persons!
        """

        if self.mandate_set.count()>0:
            return max(
                self.mandate_set.all(),
                key=lambda m: m.latest_end_date() or datetime.date(3000, 1, 1))
        else:
            return None

    @property
    def full_name_urlsafe(self):
        base_name = self.full_name or self.reversed_name
        return re.sub(u'[^a-zA-Z0-9ßöäüÖÄÜ]+', '-', base_name)

    @property
    def most_recent_function_or_occupation(self):
        if not self.latest_mandate is None and not self.latest_mandate.function is None:
            return self.latest_mandate.function.title or self.occupation
        else:
            return self.occupation

    @property
    def slug(self):
        if not self._slug:
            self._slug = reverse(
                'person_detail',
                kwargs={
                    'parl_id': self.parl_id_urlsafe,
                    'name': self.full_name_urlsafe
                }
            )
            self.save()

        return self._slug

    # JSON for ES Index Generation
    def mandates_json(self):
        mandates = []
        for mand in self.mandate_set.all():
            mandates.append(mand._json())
        return json.dumps(mandates)

    def statements_json(self):
        statements = []
        for st in self.statements.all():
            statement = st._json()
            if st.protocol_url and self.debate_statements.count():
                try:
                    page_number = int(
                        re.match('^.*SEITE_(\d+).*$', st.protocol_url).group(1))

                    dsq = self.debate_statements\
                        .filter(page_start=page_number)\
                        .filter(date__year=st.step.date.year)\
                        .filter(date__month=st.step.date.month)\
                        .filter(date__day=st.step.date.day)
                    if dsq.count() >= 1:
                        statement['debate_statement'] = [
                            ds.id for ds in dsq.all()]
                    elif not dsq.count():
                        # no matching debatestatement found
                        pass
                except:
                    # something went wrong
                    # logger.warn("Problem finding debate_statement: {}".format(
                    #     e.message))
                    pass
            statements.append(statement)
        return json.dumps(statements)

    def debate_statements_json(self):
        debate_statements = []
        for st in self.debate_statements.all():
            debate_statements.append(st._json())
        return json.dumps(debate_statements)

    def inquiries_sent_json(self):
        inquiries_sent = []
        for inq in self.inquiries_sent.all():
            inquiries_sent.append(inq._json())
        return json.dumps(inquiries_sent)

    def inquiries_received_json(self):
        inquiries_received = []
        for inq in self.inquiries_received.all():
            inquiries_received.append(inq._json())
        return json.dumps(inquiries_received)

    def inquiries_answered_json(self):
        inquiries_answered = []
        for inq in self.inquiries_answered.all():
            inquiries_answered.append(inq._json())
        return json.dumps(inquiries_answered)


class InquiryResponse(Law):
    sender = models.ForeignKey(
        Person, related_name='inquiries_answered', default="")

    @property
    def llp_roman(self):
        return self.legislative_period.roman_numeral

    def _json(self):
        inquiry = {
            'id': self.id,
            'pk': self.pk,
            'llp': self.legislative_period.roman_numeral if self.legislative_period else None,
            'ts': self.ts.isoformat() if self.ts else None,
            'title': self.title,
            'description': self.description,
            'category': self.category.title if self.category else None,
            'source_link': self.source_link,
            'sender_id': self.sender.parl_id if self.sender else None,
            'sender_name': self.sender.full_name if self.sender else None,
            'keywords': self.keyword_titles,
            'status': self.status,
        }
        return inquiry


class Inquiry(Law):

    """
    An inquiry to the members of government
    """
    # Relationships
    sender = models.ManyToManyField(
        Person, related_name='inquiries_sent', default="")
    receiver = models.ForeignKey(
        Person, related_name='inquiries_received', default="")
    response = models.ForeignKey(
        InquiryResponse, null=True, blank=True, related_name='inquiries', default="")

    def _json(self):
        inquiry = {
            'id': self.id,
            'pk': self.pk,
            'llp': self.legislative_period.roman_numeral if self.legislative_period else None,
            'ts': self.ts.isoformat() if self.ts else None,
            'title': self.title,
            'description': self.description,
            'category': self.category.title if self.category else None,
            'source_link': self.source_link,
            'receiver_id': self.receiver_id,
            'receiver_name': self.receiver.full_name,
            'sender_ids': [s.parl_id for s in self.sender.all()],
            'sender_names': [s.full_name for s in self.sender.all()],
            'keywords': self.keyword_titles,
            'status': self.status,
            'response_id': self.response_id if self.response_id else None,
            'response_title': self.response.title if self.response else None,
        }
        return inquiry

    @property
    def llp_roman(self):
        if self.legislative_period:
            return self.legislative_period.roman_numeral
        else:
            return None


class Step(models.Model):

    """
    A single step in the parliamentary process
    """
    title = models.TextField()
    sortkey = models.CharField(max_length=6)
    date = models.DateField()
    protocol_url = models.URLField(max_length=255, default="")
    source_link = models.URLField(max_length=255, default="")

    # Relationships
    phase = models.ForeignKey(Phase)
    law = models.ForeignKey(Law, null=True, blank=True, related_name='steps')
    opinion = models.ForeignKey(
        Opinion, null=True, blank=True, related_name='steps')

    class Meta:
        ordering = ['sortkey']

    def __unicode__(self):
        try:
            return remove_tags(self.title, 'a')
        except:
            return self.title



class Statement(models.Model):

    """
    A Person's statemtn or comment as part of a Step
    """
    speech_type = models.CharField(max_length=255)
    protocol_url = models.URLField(max_length=255, default="", null=True)
    index = models.IntegerField(default=1)

    # Relationships
    person = models.ForeignKey(Person, related_name='statements')
    step = models.ForeignKey(Step, related_name='statements')

    def get_href_to_debate(self):
        try:
            ids = re.match('.*?/([XVIMCD]*)/.*?(NR|BR)SITZ_(\d*).*?SEITE_(\d*)\.html',
                           self.protocol_url)
            if ids is not None:
                llp, debtype, debnr, pagenr = ids.groups()
                return reverse('debate_detail', args=(llp, debtype, debnr)) \
                       + '#statement_pg_' + str(int(pagenr))
        except:
            pass

        return None

    def __unicode__(self):
        return u'{}: {} zu {}'.format(self.person.full_name, self.speech_type, self.step.law.parl_id)

    def _json(self):
        statement = {
            'pk': self.pk,
            "type": self.speech_type,
            "date": self.step.date.isoformat(),
            "law": self.step.law.title if self.step.law else None,
            "law_id": self.step.law.id if self.step.law else None,
            "law_category": self.step.law.category.title if self.step.law else None,
            "law_slug": self.step.law.slug if self.step.law else None,
            "protocol_url": self.protocol_url,
        }
        return statement



class Verification(models.Model):

    """
    A generic Verification via random hash. Can be linked to a Subscription,
    and is being used for one-time links as well.
    """

    verified = models.BooleanField(default=False)
    verification_hash = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now=True, null=True)

    def regen_verification_hash(self):
        self.verification_hash = uuid.uuid4().hex

    def save(self, *args, **kwargs):
        if self.verification_hash==None:
            self.regen_verification_hash()
        super(Verification,self).save(*args,**kwargs)


class User(models.Model):

    """
    A user that subscribed certain pages
    """
    email = models.EmailField(unique=True)

    # Relationships
    verification = models.OneToOneField(Verification, null=True, blank=True)

    # Interna, Utilities
    _list_slug = models.CharField(max_length=255, default="")

    @property
    def list_slug(self):
        if not self._list_slug:
            self._list_slug = reverse(
                'list',
                kwargs={
                    'email': self.user.email,
                    'key': self.verification.verification_hash
                }
            )
            self.save()


class SubscribedContent(models.Model):

    """
    A news- or page-subscription
    """
    url = models.URLField(max_length=255, unique=True)
    ui_url = models.URLField(max_length=255, null=True, blank=True)

    latest_content_hashes = models.TextField(null=True, blank=True)
    # deprecated due to usage of ES for archived content
    # latest_content = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=255, default="")
    single = models.BooleanField(default=False)
    category = models.CharField(max_length=255, default="search")

    # Relationships
    users = models.ManyToManyField(User, through="Subscription")

    def get_content(self):
        """
        Executes a request to ES for this subscription's search URL

        Returns the textual response (json in string)
        """

        c = Client()

        try:
            response = c.get(self.url)
            content = json.loads(response.content)['result']
        except Exception, e:
            logger.error(
                "Couldn't get or deserialize SubscribedContent ES response for url {} ({}): {}".format(
                    self.url, response.content if 'response' in locals() else '-',
                    e
                    )
                )

        return content

    def generate_content_hashes(self, content=None):
        """
        Generate a dictionary which maps parl_ids to their respective hashes

        Used for speedy comparison of changes
        """
        if not content:
            content = self.get_content()

        content_hashes = {}
        for res in content:
            content_hashes[res['parl_id']] = self._hash_content(res)
        return json.dumps(content_hashes)

    def _hash_content(self, content):
        # To avoid deleting other SubscribedContent's archived latest_content,
        # we MUST salt the hash with this SC's URL (which is unique)
        hash_string = "{} +++ {}".format(self.url, json.dumps(content))
        hashed = xxhash.xxh64(hash_string).hexdigest()
        return hashed

    def store_latest_content(self, content):
        from elasticsearch import Elasticsearch
        es = Elasticsearch(retry_on_timeout=True)

        for content_item in content:
            content_id_hash = self._hash_content(content_item)
            es.index(index="archive", doc_type='modelresult', id=content_id_hash, body=content_item)

    def retrieve_latest_content(self):
        from elasticsearch import Elasticsearch
        es = Elasticsearch(retry_on_timeout=True)

        content = []

        try:
            hashes = json.loads(self.latest_content_hashes).values()
        except:
            # something went wrong with the latest content hashes saved in the
            # db. ignore & fail gracefully, b/c they will be regenerated the next time reset_content_hashes
            # is called
            pass

        for content_id_hash in hashes:
            try:
                res = es.get(index="archive", doc_type="modelresult", id=content_id_hash)
                content.append(res['_source'])
            except Exception, e:
                from raven.contrib.django.raven_compat.models import client
                client.captureException()
        return content

    def clear_latest_content(self):
        if not self.latest_content_hashes:
            return

        from elasticsearch import Elasticsearch
        es = Elasticsearch(retry_on_timeout=True)
        hashes = json.loads(self.latest_content_hashes).values()
        for content_id_hash in hashes:
            if es.exists(index="archive", doc_type="modelresult", id=content_id_hash):
                es.delete(index="archive", doc_type="modelresult", id=content_id_hash)

    def reset_content_hashes(self):
        """
        Resets content's hashes after an email-sending
        """
        self.clear_latest_content()
        self.latest_content_hashes = self.generate_content_hashes()
        self.store_latest_content(self.get_content())
        self.save()


class Subscription(models.Model):

    """
    A single subscription of content for a user
    """
    user = models.ForeignKey(User)
    content = models.ForeignKey(
        SubscribedContent, related_name='subscriptions')

    # Relationships
    verification = models.OneToOneField(Verification, null=True, blank=True)

    class Meta:
        unique_together = ("user", "content")

    # Interna, Utilities
    _unsub_slug = models.CharField(max_length=255, default="")

    @property
    def unsub_slug(self):
        if not self._unsub_slug:
            self._unsub_slug = reverse(
                'unsubscribe',
                kwargs={
                    'email': self.user.email,
                    'key': self.verification.verification_hash
                }
            )
            self.save()

        return self._unsub_slug


class CommentedContent(models.Model):
    created_by = models.ForeignKey(User)
    created_by_name = models.CharField(max_length=120, verbose_name='Name des Autors oder der Organisation')
    created_by_link = models.URLField(max_length=250, verbose_name='Website des Autors', blank=True)

    image = models.ImageField(null=True,
            help_text='Wird auf 100pxx100px verkleinert und in einem Kreis dargestellt',
            verbose_name='Autorenbild', blank=True)

    title = models.CharField(max_length=240, verbose_name='Titel')
    body = models.TextField(verbose_name='Text',
            help_text=u'''Sie könnnen diesen Text Überschriften und sonstige Formatierung mittels
            <a href="https://daringfireball.net/projects/markdown/syntax" target="_blank">Markdown-Format</a> formatieren.<br />
            Links auf OffenesParlament.at werden in Kästen mit Informationen zum verlinkten Inhalt (beispielsweise Titel und Status) umgewandelt.''')

    admin_notification_sent = models.BooleanField(default=False)

    approved_by = models.ForeignKey(User, null=True, related_name='approved_content')
    approved_at = models.DateTimeField(null=True)

    def __unicode__(self):
        return u'CommentedContent %d by %s: %s' % (
                self.pk,
                self.created_by_name,
                self.title,)

    def get_absolute_url(self):
        if self.approved_at:
            return reverse(
                    'commentedcontent_view',
                    kwargs={
                        'pk': self.pk,
                    })
        return None

    def get_edit_url(self):
        return reverse('commentedcontent_update', kwargs={
            'pk': self.pk
            })

    @classmethod
    def sanitize_and_expand_text(cls,text):
        matches = list(re.finditer('^https://offenesparlament.at(/gesetze/.*)$', text, re.MULTILINE))
        objs = [[x.group(0), Law.objects.filter(_slug=x.group(1).strip()).first()] for x in matches]
        texts_between = [text[0:matches[0].start()]]+[text[a.end():b.start()] for a,b in zip(matches[0:-1],matches[1:])]+[text[matches[-1].end():]]

        obj_renders = [render_to_string('op_scraper/kontext_law_partial.html', {'law': o[1], 'link': o[0]}) for o in
                objs]


        texts_between_clean = [bleach.linkify(bleach.clean(markdown.markdown(t),
                tags=settings.BLEACH_ALLOWED_TAGS,
                attributes=settings.BLEACH_ALLOWED_ATTRIBUTES,
                strip=settings.BLEACH_STRIP_TAGS
                ))
                for t in texts_between]

        output = []
        for i,t in enumerate(texts_between_clean):
            output.append(t)
            if i<len(obj_renders):
                output.append(obj_renders[i])
        return ''.join(output)

    def rendered_text(self):
        return type(self).sanitize_and_expand_text(self.body)

    @classmethod
    def published(cls):
        return cls.objects.filter(approved_at__isnull=False)


class Petition(Law):

    """
    "Beteiligung der BürgerInnen"
    Either a "Bürgerinitiative" or a "Petition" (started by members of the parliament)
    """
    signable = models.BooleanField()
    signing_url = models.URLField(max_length=255, default="")
    signature_count = models.IntegerField(default=0)

    # Relationships
    reference = models.OneToOneField(
        "self", blank=True, null=True, related_name='redistribution')

    def real_slug(self):
        # slug contains a link to the law-detail page (gesetze)
        return self.slug.replace(CONSTANTS.LAWS_LINK_NAME, CONSTANTS.PETITIONS_LINK_NAME)

    def __unicode__(self):
        return u'{} eingebracht von {}'.format(
            super(Petition, self).__unicode__(),
            ", ".join([unicode(c) for c in self.creators.all()]))

    @property
    def full_signature_count(self):
        """
        Return the signature count including the count in the previous period
        (if this Petition is a "Neuverteilung")
        """
        full_count = self.signature_count
        if self.reference is not None:
            full_count = full_count + self.reference.signature_count

        return full_count

    @property
    def slug(self):
        if not self._slug:
            self._slug = '#'
            self.save()

        return self._slug


class PetitionCreator(models.Model):

    """
    Creator of a "Bürgerinitiative" or "Petition".
    Can be a member of the parliament.
    """
    full_name = models.CharField(max_length=255)

    # Relationships
    created_petitions = models.ManyToManyField(
        Petition, related_name='creators')
    person = models.OneToOneField(
        Person, null=True, related_name='petitions_created')

    def __unicode__(self):
        if self.person is not None:
            return u'{}'.format(self.person.full_name)
        else:
            return u'{}'.format(self.full_name)


class PetitionSignature(models.Model):

    """
    Public signature of a "Bürgerinitiative" or "Petition"
    """
    full_name = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=50)
    location = models.CharField(max_length=255)
    date = models.DateField()

    # Relationships
    petition = models.ForeignKey(Petition, related_name='petition_signatures')

    def __unicode__(self):
        return u'Unterschrift von {} ({}-{}) am {} für {}'\
            .format(self.full_name, self.postal_code, self.location, self.date, self.petition)


class Debate(models.Model):

    """
    A debate / session in parlament, on a specific date.
    """
    date = models.DateTimeField()
    title = models.CharField(max_length=255, null=True)
    debate_type = models.CharField(max_length=255, null=True)
    protocol_url = models.URLField(max_length=255, null=True)
    detail_url = models.URLField(max_length=255, null=True, blank=True)
    nr = models.IntegerField(null=True)
    llp = models.ForeignKey(LegislativePeriod, null=True, blank=True)

    # Interna, Utilities
    _slug = models.CharField(max_length=255, default="")

    @property
    def parl_id(self):
        return u"{}_{}{}".format(
            self.debate_type,
            self.nr,
            "_{}".format(self.llp.roman_numeral) if self.llp else u"",
        )

    def api_slug(self):
        return "/api/debates/{}".format(self.pk)

    @property
    def slug(self):
        if not self._slug:
            self._slug = reverse(
                'debate_detail',
                kwargs={
                    'debate_type': self.debate_type,
                    'ggp': self.llp.roman_numeral if self.llp else None,
                    'number': self.nr
                }
            )
            self.save()

        return self._slug

    @property
    def statements_full_text(self):
        return [
            [
                st.index,
                st.doc_section,
                st.text_type,
                st.time_start,
                st.time_end,
                st.person.parl_id if st.person else None,
                st.speaker_role,
                st.speaker_name,
                st.full_text
            ]
            for st
            in self.debate_statements.order_by('index').all()
        ]

    @property
    def is_protocol_available(self):
        return not ("VorlaeufigesSten.Protokoll" in self.protocol_url)

    @property
    def full_title(self):
        if self.debate_type == 'NR':
            return "{} des Nationalrats".format(self.title)
        else:
            return "{} des Bundesrates".format(self.title)

    @property
    def llps_facet(self):
        if self.llp:
            return [self.llp.facet_repr]
        else:
            return []

    @property
    def llps_facet_numeric(self):
        if self.llp:
            return [self.llp.number]
        else:
            return []

    def __unicode__(self):
        return self.full_title


class DebateStatement(models.Model):

    """
    Statement in a debate
    """

    # Datime from the debate date + the most recent timestamp found in debate
    date = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)

    # Ref. to debate
    debate = models.ForeignKey(Debate, null=True,
                               related_name='debate_statements')

    # Enumeration of the sections as they were parsed
    # (might be useful for ordering)
    index = models.IntegerField(default=1)

    # The name of the div's class / section in the transcript
    doc_section = models.CharField(max_length=255)

    # Flags about the type of the section
    text_type = models.CharField(max_length=12, null=True)

    # .. and the role of the speaker, if it the section is a real statement
    speaker_role = models.CharField(max_length=12, null=True)

    # Start and end pages of the statement in the transcript
    page_start = models.IntegerField(null=True)
    page_end = models.IntegerField(null=True)

    time_start = models.CharField(max_length=12, null=True, blank=True)
    time_end = models.CharField(max_length=12, null=True, blank=True)

    # Cleaned text, will then contain only the statement of the speaker
    full_text = models.TextField(null=True)

    # Statement / transcript section, as it was fetched
    raw_text = models.TextField(null=True)

    # Will contain statement and links, references etc. - cleaned
    # and properly marked-up
    annotated_text = models.TextField(null=True)

    # Person ref (speaker)
    person = models.ForeignKey(Person, null=True,
                               related_name='debate_statements')
    # Name of speaker (useful for cases without person-ref for speaker?)
    speaker_name = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return u'{}, {}-{}, {}'.format(
            # self.person.full_name if self.person else '-',
            self.speaker_name,
            self.index,
            self.doc_section,
            self.date)

    def _json(self):
        statement = {
                'id': self.id,
                'pk': self.pk,
                'speaker_role': self.speaker_role,
                'full_text': self.full_text,
                'annotated_text': self.annotated_text,
                'text_type': self.text_type,
                'datetime': self.date.isoformat(),
                'debate_title': self.debate.title,
                'debate_date': self.debate.date.date().isoformat(),
                'debate_type': self.debate.debate_type,
                'debate_llp': self.debate.llp.facet_repr,
                'debate_protocol_url': self.debate.protocol_url,
                'debate_detail_url': self.debate.detail_url,
        }

        return statement

    @property
    def speaker_role_verbose(self):
        return {
            'pres': 'PräsidentIn',
            'min': 'MinisterIn',
            'abg': 'AbgeordneteR',
        }.get(self.speaker_role, '')


class Comittee(Timestamped, ParlIDMixIn):

    """
    "Parlamentarischer Ausschuss"
    Comittee of either the Nationalrat or Bundesrat for a specific topic
    """
    name = models.CharField(max_length=511)
    parl_id = models.CharField(max_length=30)
    source_link = models.URLField(max_length=255, default="")
    nrbr = models.CharField(max_length=20)
    description = models.TextField(default="", blank=True)
    active = models.BooleanField(default=True)

    # Relationships
    legislative_period = models.ForeignKey(
        LegislativePeriod, blank=True, null=True)
    laws = models.ManyToManyField(Law, blank=True, related_name='comittees')
    parent_comittee = models.ForeignKey(
        "self", blank=True, null=True, related_name='sub_comittees')

    class Meta:
        # NR comittees are unique by parl_id & legislative period
        # BR comittees additionaly need active for uniqueness
        unique_together = ("parl_id", "legislative_period", "active")

    def __unicode__(self):
        return u'{} [{}] in {}'\
            .format(self.name, self.parl_id, self.legislative_period)


class ComitteeMembership(models.Model):

    """
    Membership in a Comittee
    """
    date_from = models.DateField()
    date_to = models.DateField(blank=True, null=True)

    # Relationships
    comittee = models.ForeignKey(Comittee, related_name='comittee_members')
    person = models.ForeignKey(Person, related_name='comittee_memberships')
    function = models.ForeignKey(Function, related_name='comittee_function')

    def __unicode__(self):
        return u'{}: {} des {} ({}-{})'\
            .format(self.person, self.function, self.comittee, self.date_from, self.date_to)


class ComitteeMeeting(models.Model):

    """
    Meeting ("Sitzung") of a Comittee
    """
    number = models.IntegerField()
    date = models.DateField()

    # Relationships
    comittee = models.ForeignKey(Comittee, related_name='comittee_meetings')
    agenda = models.OneToOneField(
        Document, related_name='comittee_meeting', null=True)

    class Meta:
        unique_together = ("number", "date", "comittee")


class ComitteeAgendaTopic(models.Model):

    """
    Agenda topic ("Tagesordnungspunkt") of a Comittee meeting
    """
    number = models.IntegerField()
    text = models.TextField()
    comment = models.CharField(max_length=255, null=True, blank=True)

    # Relationships
    meeting = models.ForeignKey(ComitteeMeeting, related_name='agenda_topics')
    law = models.ForeignKey(Law, related_name='agenda_topics', null=True)
