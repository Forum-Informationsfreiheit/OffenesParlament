# -*- coding: utf-8 -*-
import scrapy


from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue
from ansicolor import magenta

from roman import fromRoman

from scrapy import log

from parlament.spiders import BaseSpider
from parlament.resources.extractors.petition import *

from parlament.settings import BASE_HOST
from parlament.resources.util import _clean

from op_scraper.models import LegislativePeriod
from op_scraper.models import Petition


class PetitionsSpider(BaseSpider):
    BASE_URL = "{}/{}".format(BASE_HOST, "PAKT/BB/filter.psp")

    #http://www.parlament.gv.at/PAKT/BB/filter.psp?xdocumentUri=%2FPAKT%2FBB%2Findex.shtml&NRBR=NR&anwenden=Anwenden&GP=XXV&BBET=ALLE&SUCH=&listeId=104&FBEZ=FP_004&pageNumber=

    URLOPTIONS = {
        'view': 'RSS',
        'jsMode': 'RSS',
        'xdocumentUri': '/PAKT/BB/index.shtml',
        'NRBR': 'NR',
        'anwenden': 'Anwenden',
        'BBET': 'ALLE',
        'SUCH': '',
        'listeId': '104',
        'FBEZ': 'FP_004',
    }

    name = "petitions"

    def __init__(self, **kw):
        super(PetitionsSpider, self).__init__(**kw)

        if 'llp' in kw:
            try:
                self.LLP = [int(kw['llp'])]
            except:
                pass

        # add at least a default URL for testing
        self.start_urls = self.get_urls()

        self.cookies_seen = set()
        self.idlist = {}

    def parse(self, response):
        # Extract fields
        title = PETITION.TITLE.xt(response)
        parl_id = PETITION.PARL_ID.xt(response)

        LLP = LegislativePeriod.objects.get(
            roman_numeral=response.url.split('/')[-4])

        # Create and save Petition
        petition_data = {
            'title': title
        }

        petition_item, petition_created = Petition.objects.update_or_create(
            parl_id=parl_id,
            legislative_period=LLP,
            source_link=response.url,
            defaults=petition_data)

        petition_item.save()

        # Log our progress
        if petition_created:
            logtext = u"Created {} with id {}, LLP {} @ {}"
        else:
            logtext = u"Updated {} with id {}, LLP {} @ {}"

        logtext = logtext.format(
            red(title),
            cyan(u"[{}]".format(parl_id)),
            green(str(LLP)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)
