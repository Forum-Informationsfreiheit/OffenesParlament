from __future__ import absolute_import

from celery import shared_task
from django.db import transaction
from haystack.management.commands import update_index
from scrapy.crawler import CrawlerProcess

from op_scraper.subscriptions import check_subscriptions


DEFAULT_CRAWLER_OPTIONS = {
    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
}


@shared_task
def scrape(spider, **kwargs):
    from django.contrib import admin
    admin.autodiscover()
    with transaction.atomic():
        process = CrawlerProcess(DEFAULT_CRAWLER_OPTIONS)
        process.crawl(spider, **kwargs)
        # the script will block here until the crawling is finished
        process.start()
    return


@shared_task
def update_elastic():
    update_index.Command().handle()
    return


@shared_task
def check_subscriptions():
    print "Checking subscriptions"
    check_subscriptions()
    return
