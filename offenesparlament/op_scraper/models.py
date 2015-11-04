# -*- coding: UTF-8 -*-
from datetime import date
from django.db import models
from django.utils.html import remove_tags
from django.core.urlresolvers import reverse
from phonenumber_field.modelfields import PhoneNumberField
from annoying import fields
import re


class ParlIDMixIn(object):

    @property
    def parl_id_urlsafe(self):
        return self.parl_id.replace('/', '-').replace('(', '').replace(')', '').replace(' ', '_')


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
            rep_str = "{} ({} - {})".format(
                self.roman_numeral,
                self.start_date,
                self.end_date)
        else:
            rep_str = "{} (seit {})".format(
                self.roman_numeral,
                self.start_date)

        return rep_str

    @property
    def facet_repr(self):
        if self.end_date:
            rep_str = "{} - {} ({})".format(
                self.start_date,
                self.end_date,
                self.roman_numeral)
        else:
            rep_str = "aktuell seit {} ({})".format(
                self.start_date,
                self.roman_numeral)

        return rep_str


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


class Law(models.Model, ParlIDMixIn):

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
    legislative_period = models.ForeignKey(LegislativePeriod, null=True, blank=True)
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

    @property
    def llp_roman(self):
        return self.legislative_period.roman_numeral

    @property
    def llps_facet(self):
        return [self.legislative_period.facet_repr]

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
            self._slug = reverse(
                'gesetz_detail',
                kwargs={
                    'parl_id': self.parl_id_urlsafe,
                    'ggp': self.llp_roman
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
    titles = fields.JSONField(blank=True, null=True, default=[])
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


class Person(models.Model, ParlIDMixIn):

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
        Mandate, related_name='latest_mandate', null=True, blank=True)

    def __unicode__(self):
        return self.full_name

    @property
    def party(self):
        if self.latest_mandate is not None:
            return self.latest_mandate.party
        return None

    @property
    def llps(self):
        return [
            m.legislative_period
            for m in self.mandates.order_by('-legislative_period__end_date')
            if m.legislative_period]

    @property
    def llps_roman(self):
        return [llp.roman_numeral for llp in self.llps]

    @property
    def llps_facet(self):
        return [llp.facet_repr for llp in self.llps]

    def get_latest_mandate(self):
        """
        Returns the most recent mandate a person had.

        WARNING: This is a costly function and should only be used during
        scraping, not during list display of persons!
        """

        if self.mandates:
            return max(
                self.mandates.all(),
                key=lambda m: m.latest_end_date() or date(3000, 1, 1))
        else:
            return None

    @property
    def full_name_urlsafe(self):
        base_name = self.full_name or self.reversed_name
        return re.sub(u'[^a-zA-Z0-9ßöäüÖÄÜ]+', '-', base_name)

    @property
    def most_recent_function_or_occupation(self):
        return self.latest_mandate.function.title or self.occupation

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


class Statement(models.Model):

    """
    A Person's statemtn or comment as part of a Step
    """
    speech_type = models.CharField(max_length=255)
    protocol_url = models.URLField(max_length=255, default="")
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
    latest_content_hash = models.CharField(
        max_length=16, null=True, blank=True)

    # Relationships
    users = models.ManyToManyField(User, through="Subscription")


class Subscription(models.Model):

    """
    A single subscription of content for a user
    """
    user = models.ForeignKey(User)
    content = models.ForeignKey(SubscribedContent)

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

    def __unicode__(self):
        return self.title


class DebateStatement(models.Model):

    """
    Statement in a debate
    """

    # Datime from the debate date + the most recent timestamp found in debate
    date = models.DateTimeField(null=True)

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

    # For debug reasons, can contain extracted data as JSON string
    debugdump = models.TextField(null=True)

    def __unicode__(self):
        return u'{}, {}-{}, {}'.format(
            # self.person.full_name if self.person else '-',
            self.speaker_name,
            self.index,
            self.doc_section,
            self.date)

class Comittee(models.Model, ParlIDMixIn):
    """
    "Parlamentarischer Ausschuss"
    Comittee of either the Nationalrat or Bundesrat for a specific topic
    """
    name = models.CharField(max_length=255)
    parl_id = models.CharField(max_length=30)
    source_link = models.URLField(max_length=255, default="")
    nrbr = models.CharField(max_length=20)
    description = models.CharField(max_length=1000, default="", blank=True)

    # Relationships
    legislative_period = models.ForeignKey(
        LegislativePeriod, blank=True, null=True)

    class Meta:
        unique_together = ("parl_id", "legislative_period")

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
