# -*- coding: UTF-8 -*-
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http import HttpResponse
from op_scraper.models import User
from op_scraper.models import SubscribedContent
from op_scraper.models import Subscription
from op_scraper.models import Verification
from offenesparlament.constants import EMAIL
from offenesparlament.constants import MESSAGES
from offenesparlament.forms import SubscriptionsLoginForm

from django.shortcuts import render

import xxhash
import requests
import uuid
import json

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


def login(request):
    if request.method == 'POST':
        form = SubscriptionsLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            return redirect('list_subscriptions', email=email)
    else:
        form = SubscriptionsLoginForm()

    return render(request, 'subscription/login.html', {'form': form})


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
            message = MESSAGES.EMAIL.ALREADY_VERIFIED.format(
                email)
        else:
            sub.verification.verified = True
            sub.verification.save()
            sub.user.verification.verified = True
            message = MESSAGES.EMAIL.SUCCESSFULLY_SUBSCRIBED.format(
                email)
    else:
        message = MESSAGES.EMAIL.OOPS.format(
            email)

    return render(request, 'subscription/verification.html', {'message': message})


def list(request, email, key=None):
    """
    List a user's subscriptions or (re-)send the email with the hashkey
    """
    message = ""
    if User.objects.filter(email=email).exists():
        user = User.objects.get(email=email)
        if not key:
            list_url = request.build_absolute_uri(
                reverse(
                    'list_subscriptions',
                    kwargs={
                        'email': email,
                        'key': user.verification.verification_hash}
                )
            )

            email_sent = EMAIL.SUBSCRIPTION_LIST.send(
                email, {'list_url': list_url})
            if email_sent:
                message = MESSAGES.EMAIL.SUBSCRIPTION_LINK_SENT.format(email)
            else:
                message = MESSAGES.EMAIL.ERROR_SENDING_EMAIL.format(email)

            return render(request, 'subscription/list_subscriptions.html', {'message': message})
        else:
            subscriptions = user.subscription_set.all()
            return render(
                request,
                'subscription/list_subscriptions.html',
                {
                    'message': message,
                    'user': user,
                    'subscriptions': subscriptions
                }
            )
    else:
        message = MESSAGES.EMAIL.SUBSCRIPTION_LINK_SENT.format(email)
        return render(request, 'subscription/list_subscriptions.html', {'message': message})


def unsubscribe(request, email, key):
    """
    Unsubscribe a certain subscription
    """
    sub_qs = Subscription.objects.filter(
        user__email=email,
        verification__verification_hash=key)

    if (User.objects.filter(email=email).exists() and
            sub_qs.exists() and
            sub_qs.count() == 1):

        user = User.objects.get(email=email)
        sub = sub_qs.first()
        content = sub.content
        message = MESSAGES.EMAIL.SUBSCRIPTION_DELETED.format(content.url)

        sub.delete()
        if content.subscriptions.count() == 0:
            content.delete()

        list_subscriptions_link = request.build_absolute_uri(
            reverse(
                'list_subscriptions',
                kwargs={
                    'email': email,
                    'key': user.verification.verification_hash}
            )
        )

        return redirect(list_subscriptions_link, {'message': message})
    else:
        message = MESSAGES.EMAIL.OOPS.format(email)
        return render(
            request, 'subscription/list_subscriptions.html',
            {'message': message})

    return render(
        request,
        'subscription/unsubscribe.html',
        {'message': message})


def subscribe(request):
    """
    Subcribe the given email to the given URL.
    """
    # we must unset the limiting for accurate results
    url = request.build_absolute_uri(
        request.POST['subscription_url']) + "&limit=-1&fieldset=all"
    title = request.POST['subscription_title']
    email = request.POST['email']
    category = request.POST[
        'category'] if 'category' in request.POST else 'search'

    logger.info(u"Creating subscription of {} (category '{}') for {} @ {}".format(
        title,
        category,
        email,
        url
    ))

    user, created_user = User.objects.get_or_create(email=email)
    if created_user:
        user_verification_hash = uuid.uuid4().hex
        user_verification = Verification.objects.create(
            verified=False,
            verification_hash=user_verification_hash)
        user.verification = user_verification
        user.save()

    content_default = {
        'title': title
    }
    content, created_content = SubscribedContent.objects.get_or_create(
        url=url, defaults=content_default)
    if created_content:
        hashes = content.generate_content_hashes()
        content.latest_content_hashes = hashes
        content.latest_content = content.get_content()
        content.category = category
        content.save()

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

        email_sent = EMAIL.VERIFY_SUBSCRIPTION.send(
            email, {'verification_url': verification_url})
        if email_sent:
            message = MESSAGES.EMAIL.VERIFICATION_SENT.format(email)
        else:
            message = MESSAGES.EMAIL.ERROR_SENDING_EMAIL.format(
                email)
    else:
        message = MESSAGES.EMAIL.ALREADY_SUBSCRIBED

    return HttpResponse(message)
