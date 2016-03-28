# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from op_scraper.models import Entity, LobbyRegisterPerson


class Command(BaseCommand):
    def run_from_argv(self, argv):
        self._argv = argv
        self.execute()

    def handle(self, *args, **options):
        Entity.try_matching_lobbyreg_entries()
        print 'matched %s Entities' % (Entity.objects.filter(matching_lobbyreg_entry__isnull=False).count(),)
