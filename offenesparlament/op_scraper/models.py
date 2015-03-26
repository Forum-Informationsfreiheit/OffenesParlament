# -*- coding: UTF-8 -*-
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


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
    email = models.EmailField()
    phone = PhoneNumberField()

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


class PressRelease(models.Model):

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


class Law(models.Model):

    """
    A single 'Verhandlungssache' or negotiable matter

    Can also be a prelaw (Vorparlamentarischer Prozess,
        i.e. Ministerialentwurf)

    """
    title = models.CharField(max_length=255)
    status = models.TextField(null=True, blank=True)
    source_link = models.URLField(max_length=200, default="")
    parl_id = models.CharField(max_length=30, default="")
    legislative_period = models.IntegerField(default=1)
    description = models.TextField(blank=True)

    # Relationships
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword, related_name="laws")
    press_releases = models.ManyToManyField(PressRelease, related_name="laws")
    documents = models.ManyToManyField(Document, related_name="laws")
    references = models.OneToOneField(
        "self", blank=True, null=True, related_name="laws")

    class Meta:
        unique_together = ("parl_id", "legislative_period")

    def __unicode__(self):
        return self.title


class Step(models.Model):

    """
    A single step in the parliamentary process
    """
    title = models.CharField(max_length=255)
    sortkey = models.CharField(max_length=6)
    date = models.DateField()
    protocol_url = models.URLField(max_length=200, default="")

    # Relationships
    phase = models.ForeignKey(Phase)
    law = models.ForeignKey(Law, related_name='steps')

    def __unicode__(self):
        return self.title


class Opinion(models.Model):

    """
    A comment in the pre-parliamentary process by an entity
    """
    parl_id = models.CharField(max_length=30, unique=True, default="")
    date = models.DateField()
    description = models.TextField(blank=True)

    # Relationships
    documents = models.ManyToManyField(Document)
    category = models.ForeignKey(Category, null=True, blank=True)
    keywords = models.ManyToManyField(Keyword)
    entity = models.ForeignKey(Entity)
    steps = models.ManyToManyField(Step)
    prelaw = models.ForeignKey(Law)

    def __unicode__(self):
        return self.entity.title
