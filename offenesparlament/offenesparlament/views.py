from django.shortcuts import render
from op_scraper.models import Person
from op_scraper.models import Law
from op_scraper.models import LegislativePeriod
from op_scraper.models import Keyword
from django.db.models import Count, Max
import datetime


def index(request):
    return render(request, 'index.html')


def person_list(request):
    # select_related('party').order_by('reversed_name')
    person_list = Person.objects.all()[:200]
    context = {'person_list': person_list}
    return render(request, 'person_list.html', context)


def gesetze_list(request):
    laws = Law.objects \
            .annotate(last_update=Max('steps__date')) \
            .order_by('-last_update')
    context = {'laws': laws}
    return render(request, 'gesetze_list.html', context)

def keyword_list(request):
    today = datetime.date.today()
    eight_weeks_ago = today - datetime.timedelta(weeks=8)
    top10_keywords = Keyword.objects \
            .filter(laws__steps__date__gte=eight_weeks_ago) \
            .annotate(num_steps=Count('laws__steps')) \
            .annotate(last_update=Max('laws__steps__date')) \
            .order_by('-num_steps')[:10]
    keywords = Keyword.objects.all() \
            .order_by('title')
    context = {'top10_keywords': top10_keywords, 'keywords': keywords}
    return render(request, 'keyword_list.html', context)


def person_detail(request, parl_id, name):
    person = Person.objects.get(parl_id=parl_id)
    keywords = Keyword.objects \
            .filter(laws__steps__statements__person=person) \
            .annotate(num_steps=Count('laws__steps')) \
            .order_by('-num_steps')[:10]
    laws = Law.objects \
            .filter(steps__statements__person=person) \
            .annotate(last_update=Max('steps__date')) \
            .order_by('-last_update')
    context = {'person': person, 'keywords': keywords, 'laws': laws}
    return render(request, 'person_detail.html', context)


def gesetz_detail(request, parl_id, ggp):
    parl_id_restored = '({})'.format(
        parl_id.replace('-', '/').replace('_', ' '))
    llp = LegislativePeriod.objects.get(roman_numeral=ggp)
    gesetz = Law.objects.get(parl_id=parl_id_restored, legislative_period=llp)
    context = {'gesetz': gesetz}
    return render(request, 'gesetz_detail.html', context)


def keyword_detail(request, keyword):
    title_restored = u'{}'.format(keyword.replace('-', '/').replace('_', ' '))
    keyword = Keyword.objects.get(title=title_restored)
    laws = keyword.laws \
            .annotate(last_update=Max('steps__date')) \
            .order_by('-last_update')
    context = {'keyword': keyword, 'laws': laws}
    return render(request, 'keyword_detail.html', context)


