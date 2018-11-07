# -*- coding: utf-8 -*-
# myapp/management/commands/scrapy.py

from __future__ import absolute_import
from django.core.management.base import BaseCommand
from op_scraper.models import Inquiry

class Command(BaseCommand):
    def run_from_argv(self, argv):
        self._argv = argv
        self.execute()

    def handle(self, *args, **options):
        Inquiry.objects.filter(_slug='/gesetze/XXIV/J_11481/').delete()
