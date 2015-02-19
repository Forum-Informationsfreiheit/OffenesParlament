# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from ansicolor import red
from ansicolor import cyan
from scrapy import log


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

        logtext = u"Scraping {} with id {}".format(
                red(title),
                cyan(u"[{}]".format(id))
                )

        if tags:
            logtext += u"\n  Tags: {}".format(
                u", ".join(tags),
                )

        if docs:
            logtext += u"\n  Available Documents: {}".format(
                u"\n   * ".join(docs)
                )

        log.msg(logtext, level=log.INFO)
        pass
