# -*- coding: utf-8 -*-
# myapp/management/commands/scrapy.py

from __future__ import absolute_import
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def run_from_argv(self, argv):
        self._argv = argv
        self.execute()

    def handle(self, *args, **options):
        from scrapy.cmdline import execute
        execute(self._argv[1:])
