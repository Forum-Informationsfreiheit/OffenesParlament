from django.shortcuts import render
from op_scraper.models import Person
from op_scraper.models import Law


def index(request):
    return render(request, 'base.html')


def person_list(request):
    person_list = Person.objects.order_by('reversed_name')
    # lists = []
    # sublist_length = ceil(len(person_list) / 3.0)
    # for i in range(3):
    #     start = int(i*sublist_length)
    #     end = int(min(len(person_list), (i+1)*sublist_length))
    #     lists.append(person_list[start:end])
    context = {'person_list': person_list}
    return render(request, 'person_list.html', context)


def gesetze_list(request):
    gesetze_list = Law.objects.order_by('parl_id')
    # lists = []
    # sublist_length = ceil(len(person_list) / 3.0)
    # for i in range(3):
    #     start = int(i*sublist_length)
    #     end = int(min(len(person_list), (i+1)*sublist_length))
    #     lists.append(person_list[start:end])
    context = {'gesetze_list': gesetze_list}
    return render(request, 'gesetze_list.html', context)


def person_detail(request, parl_id, name):
    person = Person.objects.get(parl_id=parl_id)
    context = {'person': person}
    return render(request, 'person_detail.html', context)


def gesetz_detail(request, parl_id, ggp):
    parl_id_restored = '({})'.format(parl_id.replace('.', '/'))
    gesetz = Law.objects.get(parl_id=parl_id_restored, legislative_period=ggp)
    context = {'gesetz': gesetz}
    return render(request, 'gesetz_detail.html', context)
