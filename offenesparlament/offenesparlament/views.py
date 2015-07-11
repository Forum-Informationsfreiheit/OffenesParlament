from django.shortcuts import render
from op_scraper.models import Person
from op_scraper.models import Law
from op_scraper.models import LegislativePeriod


def index(request):
    return render(request, 'index.html')


def person_list(request):
    person_list = Person.objects.order_by('reversed_name')
    context = {'person_list': person_list}
    return render(request, 'person_list.html', context)


def gesetze_list(request):
    gesetze_list = Law.objects.order_by('parl_id')
    context = {'gesetze_list': gesetze_list}
    return render(request, 'gesetze_list.html', context)


def person_detail(request, parl_id, name):
    person = Person.objects.get(parl_id=parl_id)
    context = {'person': person}
    return render(request, 'person_detail.html', context)


def gesetz_detail(request, parl_id, ggp):
    parl_id_restored = '({})'.format(
        parl_id.replace('-', '/').replace('_', ' '))
    llp = LegislativePeriod.objects.get(roman_numeral=ggp)
    gesetz = Law.objects.get(parl_id=parl_id_restored, legislative_period=llp)
    context = {'gesetz': gesetz}
    return render(request, 'gesetz_detail.html', context)
