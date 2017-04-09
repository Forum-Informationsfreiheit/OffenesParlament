from django.core.management.base import BaseCommand, CommandError
from op_scraper.tests.fixtures import regen_fixtures


class Command(BaseCommand):
    help = 'Generate and reset fixtures'

    def handle(self, *args, **options):
        regen_fixtures()
