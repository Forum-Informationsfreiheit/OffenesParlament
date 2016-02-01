from django.core.management.base import BaseCommand, CommandError
from op_scraper.subscriptions import check_subscriptions


class Command(BaseCommand):
    help = 'Checks subscriptions for updates and sends emails'

    def handle(self, *args, **options):
        check_subscriptions()
