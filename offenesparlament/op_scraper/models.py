# -*- coding: UTF-8 -*-
import datetime
from django.db import models
from django.utils.html import remove_tags
from django.core.urlresolvers import reverse
from phonenumber_field.modelfields import PhoneNumberField
from annoying import fields
from django.contrib.postgres.fields import ArrayField
import re
import json
import xxhash
import requests

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

    def steps_by_phases(self):
        """
        Returns a dict of phases containing the steps for display purposes
        """
        phases = {}
        for step in self.steps.all():
            if step.phase not in phases:
                phases[step.phase] = []
            phases[step.phase].append(step)

        return phases

    def steps_by_phases_json(self):
        """
        Returns a json representation of the steps_by_phases dict
        """
        phases = {}
        for step in self.steps.all():
            if step.phase not in phases:
                phases[step.phase.title] = []
            phases[step.phase.title].append({
                'title': step.title,
                'sortkey': step.sortkey,
                'date': step.date.isoformat(),
                'protocol_url': step.protocol_url,
                'source_link': step.source_link
            })

        return json.dumps(phases)

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
    title = title = models.CharField(max_length=1023)


class Mandate(models.Model):

    """
    A political Mandate for a certain function, with a start and possibly an
    end date
    """
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
    mandates = models.ManyToManyField(Mandate)
    latest_mandate = models.ForeignKey(
        Mandate, related_name='latest_mandate', null=True, blank=True,
        on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.full_name or self.reversed_name

    @property
    def party(self):
        if self.latest_mandate is not None:
            return self.latest_mandate.party
        return None

    @property
    def llps(self):
        return list(set([
            m.legislative_period
            for m in self.mandates.order_by('-legislative_period__end_date')
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

        if self.mandates:
            return max(
                self.mandates.all(),
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
    @property
    def mandates_json(self):
        mandates = []
        for mand in self.mandates.all():
            mandate = {}
            mandate['llp'] = unicode(mand.legislative_period)

            # If we have given start- and end-dates, take them
            # else take the ones from the legislative period
            if mand.start_date or mand.end_date:
                mandate['start_date'] = mand.start_date.isoformat()
                mandate[
                    'end_date'] = mand.end_date.isoformat() if mand.end_date else None
            elif mand.legislative_period:
                llp = mand.legislative_period
                mandate['start_date'] = llp.start_date.isoformat()
                mandate[
                    'end_date'] = llp.end_date.isoformat() if llp.end_date else None

            if mand.administration:
                adm = mand.administration
                mandate['administration'] = {
                    "title": adm.title,
                    "start_date": adm.start_date.isoformat(),
                    "end_date": adm.end_date.isoformat() if adm.end_date else None,
                }
                mandate['start_date'] = adm.start_date.isoformat()
                mandate[
                    'end_date'] = adm.end_date.isoformat() if adm.end_date else None

            if mand.function:
                mandate['function'] = {
                    "title": mand.function.title,
                    "short": mand.function.short,
                }
            if mand.state:
                mandate['state'] = {
                    "title": mand.state.title,
                    "name": mand.state.name,
                }
            if mand.party:
                mandate['party'] = {
                    "titles": mand.party.titles,
                    "short": mand.party.short,
                    "short_css_class": mand.party.short_css_class,
                }

            mandates.append(mandate)
        return json.dumps(mandates)

    @property
    def statements_json(self):
        statements = []
        for st in self.statements.all():
            statement = {
                "type": st.speech_type,
                "date": st.step.date.isoformat(),
                "law": st.step.law.title if st.step.law else None,
                "law_id": st.step.law.id if st.step.law else None,
                "law_category": st.step.law.category.title if st.step.law else None,
                "law_slug": st.step.law.slug if st.step.law else None,
                "protocol_url": st.protocol_url,
            }
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

    @property
    def debate_statements_json(self):
        debate_statements = []
        for st in self.debate_statements.all():
            statement = {
                'id': st.id,
                'speaker_role': st.speaker_role,
                'full_text': st.full_text,
                'annotated_text': st.annotated_text,
                'text_type': st.text_type,
                'datetime': st.date.isoformat(),
                'debate_title': st.debate.title,
                'debate_date': st.debate.date.date().isoformat(),
                'debate_type': st.debate.debate_type,
                'debate_llp': st.debate.llp.facet_repr,
                'debate_protocol_url': st.debate.protocol_url,
                'debate_detail_url': st.debate.detail_url,
            }
            debate_statements.append(statement)
        return json.dumps(debate_statements)

    @property
    def inquiries_sent_json(self):
        inquiries_sent = []
        for inq in self.inquiries_sent.all():
            inquiry = {
                'id': inq.id,
                'llp': inq.legislative_period.roman_numeral if inq.legislative_period else None,
                'ts': inq.ts.isoformat() if inq.ts else None,
                'title': inq.title,
                'description': inq.description,
                'category': inq.category.title if inq.category else None,
                'source_link': inq.source_link,
                'receiver_id': inq.receiver_id,
                'receiver_name': inq.receiver.full_name,
                'keywords': inq.keyword_titles,
                'status': inq.status,
            }
            inquiries_sent.append(inquiry)
        return json.dumps(inquiries_sent)

    @property
    def inquiries_received_json(self):
        inquiries_received = []
        for inq in self.inquiries_received.all():
            inquiry = {
                'id': inq.id,
                'llp': inq.legislative_period.roman_numeral if inq.legislative_period else None,
                'ts': inq.ts.isoformat() if inq.ts else None,
                'title': inq.title,
                'description': inq.description,
                'category': inq.category.title if inq.category else None,
                'source_link': inq.source_link,
                'sender_ids': [s.parl_id for s in inq.sender.all()],
                'sender_names': [s.full_name for s in inq.sender.all()],
                'keywords': inq.keyword_titles,
                'status': inq.status,
            }
            inquiries_received.append(inquiry)
        return json.dumps(inquiries_received)

    @property
    def inquiries_answered_json(self):
        inquiries_answered = []
        for inq in self.inquiries_answered.all():
            inquiry = {
                'id': inq.id,
                'llp': inq.legislative_period.roman_numeral if inq.legislative_period else None,
                'ts': inq.ts.isoformat() if inq.ts else None,
                'title': inq.title,
                'description': inq.description,
                'category': inq.category.title if inq.category else None,
                'source_link': inq.source_link,
                'sender_ids': [p.parl_id for i in inq.inquiries.all() for p in i.sender.all()],
                'sender_names': [p.full_name for i in inq.inquiries.all() for p in i.sender.all()],
                'keywords': inq.keyword_titles,
                'status': inq.status,
            }
            inquiries_answered.append(inquiry)
        return json.dumps(inquiries_answered)


class InquiryResponse(Law):
    sender = models.ForeignKey(
        Person, related_name='inquiries_answered', default="")

    @property
    def llp_roman(self):
        return self.legislative_period.roman_numeral


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
    title = models.CharField(max_length=1023)
    sortkey = models.CharField(max_length=6)
    date = models.DateField()
    protocol_url = models.URLField(max_length=255, default="")
    source_link = models.URLField(max_length=255, default="")

    # Relationships
    phase = models.ForeignKey(Phase)
    law = models.ForeignKey(Law, null=True, blank=True, related_name='steps')
    opinion = models.ForeignKey(
        Opinion, null=True, blank=True, related_name='steps')

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

    def __unicode__(self):
        return u'{}: {} zu {}'.format(self.person.full_name, self.speech_type, self.step.law.parl_id)


class Verification(models.Model):

    """
    A generic Verification via random hash. Can be linked to a Subscription,
    and is being used for one-time links as well.
    """

    verified = models.BooleanField()
    verification_hash = models.CharField(max_length=32)


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
    latest_content = models.TextField(null=True, blank=True)
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
        content_response = requests.get(self.url)
        return content_response.text

    def generate_content_hashes(self, content=None):
        """
        Generate a dictionary which maps parl_ids to their respective hashes

        Used for speedy comparison of changes
        """
        if not content:
            es_response = json.loads(self.get_content())
        else:
            try:
                es_response = json.loads(content)
            except:
                es_response = json.loads(self.get_content())

        content_hashes = {}
        for res in es_response['result']:
            content_hashes[res['parl_id']] = xxhash.xxh64(
                json.dumps(res)).hexdigest()
        return json.dumps(content_hashes)

    def reset_content_hashes(self):
        """
        Resets content's hashes after an email-sending
        """
        self.latest_content_hashes = self.generate_content_hashes()
        self.latest_content = self.get_content()
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
        return self.title


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
