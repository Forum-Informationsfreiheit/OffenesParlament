from django.shortcuts import render
from op_scraper.models import Person


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

def person_detail(request, parl_id, name):
    person = Person.objects.get(pk=parl_id)
    context = {'person': person}
    return render(request, 'person_detail.html', context)
