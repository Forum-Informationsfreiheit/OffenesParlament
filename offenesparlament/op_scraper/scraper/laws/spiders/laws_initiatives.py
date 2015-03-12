# -*- coding: utf-8 -*-
import scrapy


from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue

from scrapy import log
import collections


from laws.resources.extractors import *
from laws.resources.rss import get_urls

from op_scraper.models import Phase
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion


class LawsInitiativesSpider(scrapy.Spider):
    name = "laws_initiatives"
    allowed_domains = ["parlament.gv.at"]

    DEBUG_URLS = [
        'http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml']

    def __init__(self, **kw):
        super(LawsInitiativesSpider, self).__init__(**kw)

        # add at least a default URL for testing
        self.start_urls = get_urls() or self.DEBUG_URLS

        self.cookies_seen = set()

    def parse(self, response):
        title = TITLE.xt(response)
        parl_id = PARL_ID.xt(response)
        keywords = KEYWORDS.xt(response)
        docs = DOCS.xt(response)

        # Don't re-parse laws we already have
        # FIXME: at some point, we need to be able to update laws, not just skip
        # them if we already have them
        if Law.objects.filter(parl_id=parl_id).exists():
            log.msg(
                u"{} with ID {} already exists, skipping import".format(
                    red(title),
                    cyan(u"[{}]".format(parl_id))),
                level=log.INFO)
            return

        # Log our progress
        logtext = u"Scraping {} with id {} @ {}".format(
            red(title),
            cyan(u"[{}]".format(parl_id)),
            blue(response.url)
        )
        log.msg(logtext, level=log.INFO)

        # Create all keywords we don't yet have in the DB
        keyword_items = []
        for keyword in keywords:
            kw, created = Keyword.objects.get_or_create(title=keyword)
            if created:
                log.msg(u"Created keyword {}".format(
                    green(u'[{}]'.format(keyword))))
            keyword_items.append(kw)

        # Create all keywords we don't yet have in the DB
        doc_items = []
        for document in docs:
            # TODO
            pass

        law_item = Law.objects.create(
            title=title,
            parl_id=parl_id,
            source_link=response.url)
        law_item.save()
        law_item.keywords = keyword_items

        # if tags:
        #     logtext += u"\n  {} \n     * {}".format(
        #         green(u"Tags:"),
        #         u"\n     * ".join(tags),
        #     )

        # if docs:
        #     logtext += u"\n  {} \n     * {}".format(
        #         green(u"Available Documents:"),
        #         u"\n     * ".join(docs)
        #     )

        law_item.save()

        # is the tab 'Parlamentarisches Verfahren available?'
        # if response.xpath('//*[@id="ParlamentarischesVerfahren"]'):
        #     url_postfix = response.xpath(
        #         '//*[@id="ParlamentarischesVerfahren"]/a/@href').extract()[0]
        #     req = scrapy.Request(response.url + url_postfix,
        #                          callback=self.parse_parliament_steps)
        #     req.meta['logtext'] = logtext
        #     return req

    def parse_parliament_steps(self, response):
        """
        Callback function to parse the additional 'Parlamentarisches Verfahren'
        page
        """
        rows = response.xpath(
            '//*[@id="content"]/div[3]/div[3]/table/tbody//tr[(@class!="historyHeader" and @class!="close") or not(@class)]')
        steps = [
            {'date': self._clean(row.xpath('string(td[1])').extract()),
             'step': self._clean(row.xpath('string(td[2])').extract())}
            for row in rows]

        # import ipdb; ipdb.set_trace()
        # stepstring = u"\n     * ".join(
        #     [u"{}: {}".format(s['date'], s['step']) for s in steps])
        # logtext = u"{}\n  {}\n     * {}".format(
        #     response.meta['logtext'],
        #     green(u"Process in Parliament:"),
        #     stepstring)
        logtext = response.meta['logtext']
        log.msg(logtext, level=log.INFO)
        pass

    def _clean(self, to_clean):
        """
        Removes all \n and \t characters as well as trailing and leading
        whitespace
        """
        if isinstance(to_clean, collections.Iterable):
            to_clean = to_clean[0]

        to_clean = to_clean.replace(
            '\t', '').replace('\n', '').strip()
        return to_clean
