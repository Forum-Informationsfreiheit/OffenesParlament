# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue


from scrapy import log
import collections


class LawsInitiativesSpider(scrapy.Spider):
    name = "laws_initiatives"
    allowed_domains = ["parlament.gv.at"]
    start_urls = (
        'http://www.parlament.gv.at/',
    )

    DEBUG_URLS = [
        'http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml']

    def __init__(self, **kw):
        super(LawsInitiativesSpider, self).__init__(**kw)
        # add at least a default URL for testing

        self.start_urls = kw.get('urls') or self.DEBUG_URLS

        for url in self.start_urls:
            if not url.startswith('http://') and not url.startswith('https://'):
                url = 'http://%s/' % url
        self.link_extractor = LinkExtractor()
        self.cookies_seen = set()

    def parse(self, response):
        title = response.xpath('//*[@id="inhalt"]/text()').extract()[0].strip()
        id = response.xpath(
            '//*[@id="inhalt"]/span/text()').extract()[0].strip()
        tags = response.xpath(
            '//*[@id="schlagwortBox"]/ul//li/a/text()').extract()
        docs = response.xpath(
            '//*[@id="content"]/div[3]/div[2]/div[2]/div/ul//li/a[1]/text()').extract()

        logtext = u"Scraping {} with id {} @ {}".format(
            red(title),
            cyan(u"[{}]".format(id)),
            blue(response.url)
        )

        if tags:
            logtext += u"\n  {} \n     * {}".format(
                green(u"Tags:"),
                u"\n     * ".join(tags),
            )

        if docs:
            logtext += u"\n  {} \n     * {}".format(
                green(u"Available Documents:"),
                u"\n     * ".join(docs)
            )

        # is the tab 'Parlamentarisches Verfahren available?'
        if response.xpath('//*[@id="ParlamentarischesVerfahren"]'):
            url_postfix = response.xpath(
                '//*[@id="ParlamentarischesVerfahren"]/a/@href').extract()[0]
            req = scrapy.Request(response.url + url_postfix,
                                 callback=self.parse_parliament_steps)
            req.meta['logtext'] = logtext
            return req

        log.msg(logtext, level=log.INFO)

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
        stepstring = u"\n     * ".join(
            [u"{}: {}".format(s['date'], s['step']) for s in steps])
        logtext = u"{}\n  {}\n     * {}".format(
            response.meta['logtext'],
            green(u"Process in Parliament:"),
            stepstring)
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
