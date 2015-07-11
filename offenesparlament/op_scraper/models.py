# -*- coding: UTF-8 -*-
from django.db import models
from django.utils.html import remove_tags
from phonenumber_field.modelfields import PhoneNumberField
from annoying import fields
import re


class ParlIDMixIn(object):

    @property
    def parl_id_urlsafe(self):
        return self.parl_id.replace('/', '-').replace('(', '').replace(')', '').replace(' ', '_')


class LegislativePeriod(models.Model):

    """
    A single legislative Period or 'Legislaturperiode'
    """

    number = models.IntegerField()
    roman_numeral = models.CharField(unique=True, max_length=255, default="")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __unicode__(self):
        if self.end_date:
            rep_str = "{} ({} - {})".format(
                self.roman_numeral,
                self.start_date,
                self.end_date)
        else:
            rep_str = "{} (since {})".format(
                self.roman_numeral,
                self.start_date)

        return rep_str


class Phase(models.Model):

    """
    A phase in the process of a law, grouping steps together
    """
    title = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class Entity(models.Model):

    """
    An organisation or person commenting in a pre-parliamentary process (prelaw)
    """
    title = models.CharField(max_length=255)
    title_detail = models.CharField(max_length=255)
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
    title = models.CharField(max_length=255)
    pdf_link = models.URLField(max_length=200, null=True)
    html_link = models.URLField(max_length=200, null=True)
    stripped_html = models.TextField(null=True)

    def __unicode__(self):
        return self.title


class PressRelease(models.Model, ParlIDMixIn):

    """
    A press release produced by the parliamentary staff
    """
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255)
    full_text = models.TextField()
    release_date = models.DateField()
    source_link = models.URLField(max_length=200, default="")
    parl_id = models.CharField(max_length=30, unique=True, default="")
    topics = models.CharField(max_length=255)
    format = models.CharField(max_length=255)
    tags = models.CharField(max_length=255)

    def __unicode__(self):
        return self.title


class Category(models.Model):

    """
    A category for a law or prelaw
    """
    title = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.title


class Keyword(models.Model):

    """
    A keyword assigned to laws and prelaws
    """
    title = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']


class Law(models.Model, ParlIDMixIn):

    """
    A single 'Verhandlungssache' or negotiable matter

    Can also be a prelaw (Vorparlamentarischer Prozess,
        i.e. Ministerialentwurf)

    """
    title = models.CharField(max_length=255)
    status = models.TextField(null=True, blank=True)
    source_link = models.URLField(max_length=200, default="")
    parl_id = models.CharField(max_length=30, default="")

    description = models.TextField(blank=True)

    # Relationships
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="laws")
    press_releases = models.ManyToManyField(PressRelease, related_name="laws")
    documents = models.ManyToManyField(Document, related_name="laws")
    legislative_period = models.ForeignKey(LegislativePeriod)
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

    class Meta:
        unique_together = ("parl_id", "legislative_period")

    @property
    def short_title(self):
        return (self.title[:100] + '...') if len(self.title) > 100 else self.title

    def __unicode__(self):
        return self.title


class Opinion(models.Model, ParlIDMixIn):

    """
    A comment in the pre-parliamentary process by an entity
    """
    parl_id = models.CharField(max_length=30, unique=True, default="")
    date = models.DateField(null=True)
    description = models.TextField(blank=True)
    source_link = models.URLField(max_length=200, default="")

    # Relationships
    documents = models.ManyToManyField(Document)
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword)
    entity = models.ForeignKey(Entity, related_name='opinions')
    prelaw = models.ForeignKey(Law, related_name='opinions')

    def __unicode__(self):
        return u'{} zu {}'.format(self.entity.title, self.prelaw.parl_id)


class Step(models.Model):

    """
    A single step in the parliamentary process
    """
    title = models.CharField(max_length=255)
    sortkey = models.CharField(max_length=6)
    date = models.DateField()
    protocol_url = models.URLField(max_length=200, default="")
    source_link = models.URLField(max_length=200, default="")

    # Relationships
    phase = models.ForeignKey(Phase)
    law = models.ForeignKey(Law, null=True, blank=True, related_name='steps')
    opinion = models.ForeignKey(
        Opinion, null=True, blank=True, related_name='steps')

    def __unicode__(self):
        return remove_tags(self.title, 'a')


class Function(models.Model):

    """
    A parliamentary function, like Abgeordnete or Mitglied des Bundesrates
    """
    title = models.CharField(max_length=255)

    def __unicode__(self):
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


class Mandate(models.Model):

    """
    A political Mandate for a certain function, with a start and possibly an
    end date
    """
    function = models.ForeignKey(Function)
    party = models.ForeignKey(Party, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __unicode__(self):
        return u"{} ({}): {} - {} ".format(
            self.function,
            self.party,
            self.start_date,
            self.end_date)


class Person(models.Model, ParlIDMixIn):

    """
    A single person in parliament, including Abgeordnete, Regierungsmitglieder,
    etc.
    """
    parl_id = models.CharField(max_length=30, primary_key=True)
    source_link = models.URLField(max_length=200, default="")
    photo_link = models.URLField(max_length=200, default="")
    photo_copyright = models.CharField(max_length=255, default="")
    full_name = models.CharField(max_length=255)
    reversed_name = models.CharField(max_length=255)
    birthdate = models.DateField(null=True, blank=True)
    birthplace = models.CharField(max_length=255, null=True, blank=True)
    deathdate = models.DateField(null=True, blank=True)
    deathplace = models.CharField(max_length=255, null=True, blank=True)
    occupation = models.CharField(max_length=255, null=True, blank=True)

    # Relationsships
    party = models.ForeignKey(Party)
    mandates = models.ManyToManyField(Mandate)

    def __unicode__(self):
        return self.full_name

    @property
    def full_name_urlsafe(self):
        return re.sub(u'[^a-zA-Z0-9ßöäüÖÄÜ]+', '-', self.full_name)

    @property
    def most_recent_function_or_occupation(self):
        mandates = self.mandates.filter(end_date=None).order_by('-start_date')
        if mandates and len(mandates) > 0:
            return mandates[0].function
        else:
            mandates = self.mandates.order_by('-end_date')
            if mandates and len(mandates) > 0:
                return mandates[0].function
            else:
                return self.occupation


class Statement(models.Model):

    """
    A Person's statemtn or comment as part of a Step
    """
    speech_type = models.CharField(max_length=255)
    protocol_url = models.URLField(max_length=200, default="")
    index = models.IntegerField(default=1)

    # Relationships
    person = models.ForeignKey(Person, related_name='statements')
    step = models.ForeignKey(Step, related_name='statements')

    def __unicode__(self):
        return u'{}: {} zu {}'.format(self.person.full_name, self.speech_type, self.step.law.parl_id)
