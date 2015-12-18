# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import render

from op_scraper.tasks import scrape, update_elastic
from op_scraper.scraper.parlament.spiders.llp import LegislativePeriodSpider
from op_scraper.scraper.parlament.spiders.administrations import AdministrationsSpider
from op_scraper.scraper.parlament.spiders.laws_initiatives import LawsInitiativesSpider
from op_scraper.scraper.parlament.spiders.petitions import PetitionsSpider
from op_scraper.scraper.parlament.spiders.pre_laws import PreLawsSpider
from op_scraper.scraper.parlament.spiders.persons import PersonsSpider
from op_scraper.scraper.parlament.spiders.statement import StatementSpider
from op_scraper.scraper.parlament.spiders.comittees import ComitteesSpider


SPIDERS = {
    'llp': {
        'scraper': LegislativePeriodSpider,
        'has_options': False
    },
    'administrations': {
        'scraper': AdministrationsSpider,
        'has_options': False
    },
    'persons': {
        'scraper': PersonsSpider,
        'has_options': False
    },
    'pre_laws': {
        'scraper': PreLawsSpider,
        'has_options': True
    },
    'laws': {
        'scraper': LawsInitiativesSpider,
        'has_options': True
    },
    'petitions': {
        'scraper': PetitionsSpider,
        'has_options': True
    },
    'debates': {
        'scraper': StatementSpider,
        'has_options': True
    },
    'comittees': {
        'scraper': ComitteesSpider,
        'has_options': True
    },
}

SPIDER_CHOICES = (
    ('llp', 'Gesetzgebungsperioden'),
    ('administrations', 'Regierungsmitglieder'),
    ('persons', 'Personen'),
    ('pre_laws', 'Ministerialentwürfe und Vorparlamentarische Prozesses'),
    ('laws', 'Gesetze'),
    ('petitions', 'Petitionen'),
    ('debates', 'Debatten und Statements'),
    ('comittees', 'Ausschüsse')
)

from django import forms


def get_llp_choices(spider_name):
    """
    Computes a list of LLPs that are valid for the given Spider.
    """
    choices = [('all', 'Alle')]
    choices += [(llp, llp)
                for llp in SPIDERS[spider_name]['scraper'].ALLOWED_LLPS]
    return choices


class ScrapeForm(forms.Form):
    scraper = forms.ChoiceField(label='The Scraper', choices=SPIDER_CHOICES)
    llp = forms.ChoiceField(label='LLP', choices=())


def trigger_scrape(request, spider_name):
    # if this is a POST request we need to process the form data
    if not SPIDERS[spider_name]['has_options']:
        messages.success(
            request,
            'Scraping of {} triggered. Awesomeness ensues.'.format(
                spider_name))
        scrape.delay(SPIDERS[spider_name]['scraper'])
        return redirect('/admin/')

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ScrapeForm(request.POST)
        messages.success(
            request,
            'Scraping of {} triggered. Awesomeness ensues.'.format(
                spider_name))
        scrape.delay(SPIDERS[spider_name]['scraper'], **form.data.dict())
        return redirect('/admin/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ScrapeForm()
        form.fields['scraper'].initial = spider_name
        form.fields['scraper'].widget.attrs = {'disabled': 'disabled'}
        form.fields['llp'].choices = get_llp_choices(spider_name)

    return render(
        request,
        'admin/form_scrape.html',
        {
            'form': form,
            'spider_name': spider_name
        }
    )


def trigger_reindex(request):
    """
    Triggers an index update for ElasticSearch
    """
    messages.success(
        request, 'Updating ElasticSearch Index triggered! Awesomeness ensues.')
    update_elastic.delay()
    return redirect('/admin/')
