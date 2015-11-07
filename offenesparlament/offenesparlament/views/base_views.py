# -*- coding: UTF-8 -*-
from django.shortcuts import render
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from op_scraper.models import Person
from op_scraper.models import Law
from op_scraper.models import LegislativePeriod
from op_scraper.models import Keyword
from op_scraper.models import User
from op_scraper.models import SubscribedContent
from op_scraper.models import Subscription
from op_scraper.models import Verification
from django.db.models import Count, Max
from django.core.mail import send_mail

import datetime
import xxhash
import requests
import uuid


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def person_list(request):
    person_list = Person.objects.all().select_related(
        'latest_mandate__party')[:200]
    context = {'person_list': person_list}
    return render(request, 'person_list.html', context)


def gesetze_list(request):
    laws = Law.objects \
        .annotate(last_update=Max('steps__date')) \
        .order_by('-last_update') \
        .select_related('category')
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
    context = {'law': gesetz}
    return render(request, 'gesetz_detail.html', context)


def keyword_detail(request, keyword):
    keyword = Keyword.objects.get(_title_urlsafe=keyword)
    laws = keyword.laws \
        .annotate(last_update=Max('steps__date')) \
        .order_by('-last_update')
    context = {'keyword': keyword, 'laws': laws}
    return render(request, 'keyword_detail.html', context)


def verify(request, email, key):
    """
    Verify a user's subscription for the given email
    """
    sub_qs = Subscription.objects.filter(
        user__email=email,
        verification__verification_hash=key)

    if sub_qs.exists() and sub_qs.count() == 1:
        sub = sub_qs.first()
        if sub.verification.verified:
            message = "Diese Subskription ist bereits bestätigt für {}!".format(
                email)
        else:
            sub.verification.verified = True
            sub.verification.save()
            message = "Email-Adresse {} bestätigt.".format(email)
    else:
        message = """
            Ups, da ist was schiefgelaufen - konnte {} nicht finden
            (oder nicht eindeutig zuordnen)!""".format(
            email)

    return render(request, 'verification.html', {'message': message})


def subscribe(request):
    url = request.POST['subscription_url']
    email = request.POST['email']

    user, created_user = User.objects.get_or_create(email=email)
    content, created_content = SubscribedContent.objects.get_or_create(url=url)
    if created_content:
        content_response = requests.get(url)
        content_hash = xxhash.xxh64(content_response.text).hexdigest()
        content.latest_content_hash = content_hash

    if not Subscription.objects.filter(user=user, content=content).exists():
        verification_hash = uuid.uuid4().hex
        verification_url = request.build_absolute_uri(
            reverse(
                'verify',
                kwargs={
                    'email': email,
                    'key': verification_hash}
            )
        )
        verification_item = Verification.objects.create(
            verified=False,
            verification_hash=verification_hash
        )

        Subscription.objects.create(
            user=user,
            content=content,
            verification=verification_item
        )
        send_mail(
            'Verify thine self!',
            """
            Hej there,<br /><br />
            please verify that you are the owner of this address by opening
            this verification link:<br /><br />
            <a href="{}">Verify me!</a>
            """.format(
                verification_url
            ),
            'from@example.com',
            ['to@example.com'],
            fail_silently=False)
        message = "Email-Verifikation gestartet"
    else:
        message = "Diese Seite ist bereits für diese Email abonniert!"

    messages.add_message(request, messages.INFO, message)
    return redirect(request.META['HTTP_REFERER'], {'message': message})
