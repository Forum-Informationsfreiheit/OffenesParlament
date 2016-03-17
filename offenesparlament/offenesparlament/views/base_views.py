# -*- coding: UTF-8 -*-
from django.shortcuts import render, redirect
from op_scraper.models import Person
from op_scraper.models import Law
from op_scraper.models import LegislativePeriod
from op_scraper.models import Keyword
from op_scraper.models import Inquiry
from op_scraper.models import InquiryResponse
from django.db.models import Count, Max, Min, Q

from offenesparlament.views.search import PersonSearchView
from op_scraper.search_indexes import extract_json_fields

import datetime
import urllib


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def generic_search_view(request, query):
    return render(request, 'generic_search_view.html')


def subscriptions(request):
    return render(request, 'subscriptions.html')


def person_list(request):
    llp = _ensure_ggp_is_set(request)
    return redirect('person_list_with_ggp', ggp=llp.roman_numeral)


def keyword_list(request):
    llp = _ensure_ggp_is_set(request)
    return redirect('keyword_list_with_ggp', ggp=llp.roman_numeral)


def gesetze_list(request):
    llp = _ensure_ggp_is_set(request)
    return redirect('laws_list_with_ggp', ggp=llp.roman_numeral)


def person_list_with_ggp(request, ggp):
    llp = _ensure_ggp_is_set(request, ggp)
    person_list = Person.objects \
        .filter(mandates__legislative_period=llp) \
        .order_by('reversed_name') \
        .select_related('latest_mandate__party')
    context = {'person_list': person_list}
    return render(request, 'person_list.html', context)


def gesetze_list_with_ggp(request, ggp):
    llp = _ensure_ggp_is_set(request, ggp)
    laws = Law.objects \
        .filter(legislative_period=llp) \
        .annotate(last_update=Max('steps__date')) \
        .order_by('-last_update') \
        .select_related('category')[:100]
    context = {'laws': laws}
    return render(request, 'gesetze_list.html', context)


def keyword_list_with_ggp(request, ggp):
    llp = _ensure_ggp_is_set(request, ggp)
    today = datetime.date.today()
    eight_weeks_ago = today - datetime.timedelta(weeks=8)
    top10_keywords = Keyword.objects \
        .filter(laws__steps__date__gte=eight_weeks_ago) \
        .annotate(num_steps=Count('laws__steps')) \
        .annotate(last_update=Max('laws__steps__date')) \
        .order_by('-num_steps')[:10]
    keywords = Keyword.objects.filter(laws__legislative_period=llp) \
        .order_by('title') \
        .distinct()
    context = {'top10_keywords': top10_keywords, 'keywords': keywords}
    return render(request, 'keyword_list.html', context)

def inquiry_detail(request, inq_id, ggp=None):
    if inq_id.split('_')[0] == 'AB' or inq_id.split('_')[0] == 'ABPR':
        if ggp is not None:
            inquiry = InquiryResponse.objects \
                .filter(parl_id=inq_id, law_ptr__legislative_period__roman_numeral=ggp) \
                .first().inquiries.first()
        else:
            inquiry = InquiryResponse.objects.filter(parl_id=inq_id).first().inquiries.first()
    elif ggp is not None:
        inquiry = Inquiry.objects \
            .filter(parl_id=inq_id, law_ptr__legislative_period__roman_numeral=ggp) \
            .first()
    else:
        inquiry = Inquiry.objects.filter(parl_id=inq_id).first()
    inquiry_type_verbal = inquiry.parl_id.split('_')[0][0] == 'M'
    inquiry_sender = inquiry.sender
    documents = inquiry.documents
    inquiry_response = inquiry.response
    mandates_receiver = inquiry.receiver.mandates.order_by('-end_date')
    # mandates_receiver_filtered = mandates_receiver.filter(legislative_period__in=LegislativePeriod.objects.filter(Q(start_date__lte=inquiry.first_date), Q(end_date__gte=inquiry.first_date) | Q(end_date__isnull=True)))
    # mandates_receiver_filtered = mandates_receiver.filter(Q(start_date__lte=inquiry.first_date), Q(end_date__gte=inquiry.first_date) | Q(end_date__isnull=True))
    first_date = inquiry.steps.order_by('date').first().date
    last_date = inquiry.steps.order_by('date').last().date
    receiver_mandate = mandates_receiver.first().function.title
    if first_date is not None:
      for mandate in mandates_receiver:
        if mandate.end_date is None or mandate.start_date is None:
          continue
        if mandate.earliest_start_date() <= first_date <= mandate.latest_end_date():
          receiver_mandate = mandate.function.title
          break
      # mandates_receiver_filtered = mandates_receiver.filter(Q(start_date__lte=first_date), Q(end_date__gte=last_date) | Q(end_date__isnull=True))

    steps = inquiry.steps.order_by('-date')
    for step in steps:
      step.title = step.title.replace("/PAKT/","https://www.parlament.gv.at/PAKT/")
      step.title = step.title.replace("/WWER/","https://www.parlament.gv.at/WWER/")
    context = {'inquiry': inquiry, 'documents': documents, \
        'inquiry_response': inquiry_response, 'first_date': first_date, \
        'inquiry_sender': inquiry_sender, 'steps': steps, \
        'last_date': last_date, 'inquiry_type_verbal': inquiry_type_verbal, \
        'reveiver_mandate': receiver_mandate}
    return render(request, 'inquiry_detail.html', context)

def person_detail(request, parl_id, name):
    person = Person.objects \
        .select_related('latest_mandate') \
        .get(parl_id=parl_id)
    statement_list = person.statements \
        .select_related('step__law')
    keywords = Keyword.objects \
        .filter(laws__steps__statements__person=person) \
        .annotate(num_steps=Count('laws__steps')) \
        .order_by('-num_steps')[:10]
    laws = Law.objects \
        .filter(steps__statements__person=person) \
        .annotate(last_update=Max('steps__date')) \
        .select_related('category') \
        .order_by('-last_update')
    subscription_title = person.full_name
    url_params = {'parl_id': person.parl_id}
    subscription_url = '/suche/gesetze?{}'.format(urllib.urlencode(url_params))

    # instantiate appropriate search view
    # psv = PersonSearchView()
    # # query ES
    # (result, facets) = psv.get_queryset({'parl_id': parl_id})
    # # only proceed if we actually found something
    # if len(result):
    #     # since this is a detail page, return all the fields from the index
    #     es_person = psv.build_result_set(result, 'all')[0]
    #     # extract the fields that are in JSON-Format for easier manipulation in
    #     # the template
    #     es_person = extract_json_fields(es_person, 'person')
    # else:
    #     # In Future, we might want to _only_ hit the database when we do not
    #     # find our person via the search index
    #     # That way, if the person is in the index, we can serve the page faster,
    #     # but we still have a fallback in case the index isn't up2date for some
    #     # reason
    #     es_person = None
    # print(es_person.keys())

    # add inquiries_sent here
    inquiries_sent = person.inquiries_sent \
       .annotate(first_date=Min('steps__date')).order_by('-first_date')
    context = {
        'person': person,
        'statement_list': statement_list,
        'keywords': keywords,
        'laws': laws,
        'inquiries_sent': inquiries_sent,
        'subscription_url': subscription_url,
        'subscription_title': subscription_title
    }
    return render(request, 'person_detail.html', context)


def gesetz_detail(request, parl_id, ggp=None):
    parl_id_restored = '({})'.format(
        parl_id.replace('-', '/').replace('_', ' '))
    if ggp:
        llp = LegislativePeriod.objects.get(roman_numeral=ggp)
        gesetz = Law.objects.get(
            parl_id=parl_id_restored, legislative_period=llp)
    else:
        llp = None
        gesetz = Law.objects.get(parl_id=parl_id, legislative_period=llp)
    if hasattr(gesetz, 'laws'):
        return redirect('{}#vorparlamentarisch'.format(gesetz.laws.slug))
    subscription_title = u"{} ({})".format(gesetz.title, gesetz.legislative_period.roman_numeral)
    url_params = {'parl_id': gesetz.parl_id, 'llps': gesetz.legislative_period.roman_numeral}
    subscription_url = '/suche/gesetze?{}'.format(urllib.urlencode(url_params))
    context = {
        'law': gesetz,
        'subscription_url': subscription_url,
        'subscription_title': subscription_title
    }
    return render(request, 'gesetz_detail.html', context)


def keyword_detail(request, keyword):
    keyword = Keyword.objects.get(_title_urlsafe=keyword)
    laws = keyword.laws \
        .annotate(last_update=Max('steps__date')) \
        .order_by('-last_update')
    context = {'keyword': keyword, 'laws': laws}
    return render(request, 'keyword_detail.html', context)


def _ensure_ggp_is_set(request, ggp_roman_numeral=None):
    """Make sure a valid GGP is set as session var and set the current one if
    it isn't. Return the selected GGP's roman numeral."""
    if ggp_roman_numeral is not None:
        llp = LegislativePeriod.objects.get(roman_numeral=ggp_roman_numeral)
        request.session['ggp_roman_numeral'] = llp.roman_numeral
        request.session['ggp_facet_repr'] = llp.facet_repr
    elif 'ggp_roman_numeral' not in request.session or request.session['ggp_roman_numeral'] is None:
        llp = LegislativePeriod.objects.get_current()
        request.session['ggp_roman_numeral'] = llp.roman_numeral
        request.session['ggp_facet_repr'] = llp.facet_repr
    llp = LegislativePeriod.objects.get(
        roman_numeral=request.session['ggp_roman_numeral'])
    return llp
