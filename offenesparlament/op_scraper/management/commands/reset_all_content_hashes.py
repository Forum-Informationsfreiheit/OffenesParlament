from django.core.management.base import BaseCommand, CommandError
from op_scraper.models import SubscribedContent

class Command(BaseCommand):
    help = 'Resets all subscribed content hashes'

    def handle(self, *args, **options):
        from elasticsearch import Elasticsearch
        es = Elasticsearch(retry_on_timeout=True)
        if not es.indices.exists('archive'):
            es.indices.create('archive')
        for sc in SubscribedContent.objects.all():
            sc.reset_content_hashes()

