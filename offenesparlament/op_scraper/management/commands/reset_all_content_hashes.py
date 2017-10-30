from django.core.management.base import BaseCommand, CommandError
from op_scraper.models import SubscribedContent

class Command(BaseCommand):
    help = 'Resets all subscribed content hashes'

    def handle(self, *args, **options):
        haystack.connections['archive'].get_backend().setup()
        for sc in SubscribedContent.objects.all():
            sc.reset_content_hashes()

