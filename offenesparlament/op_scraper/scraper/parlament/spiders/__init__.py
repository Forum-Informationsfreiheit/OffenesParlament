from logging.config import dictConfig
from django.conf import settings
import scrapy
from scrapy.utils.project import get_project_settings


import feedparser
import roman
from urllib import urlencode
from ansicolor import red
from ansicolor import cyan
from ansicolor import green
from ansicolor import blue
from parlament.settings import BASE_HOST


class BaseSpider(scrapy.Spider):

    """
    Base class for scraping parliamentary sites
    """

    # Law Periods/Gesetzgebungsperioden to scrape
    LLP = [20, 21, 22, 23, 24, 25]

    # Basic URL after host to scrape (must be rss)
    BASE_URL = ""

    # Options dictionary for rss url
    URLOPTIONS = {}

    allowed_domains = ["parlament.gv.at"]

    IGNORE_TIMESTAMP = False

    SCRAPED_COUNTER = 0
    TOTAL_COUNTER = 0

    def __init__(self, **kw):
        super(BaseSpider, self).__init__(**kw)

        if 'ignore_timestamp' in kw:
            self.IGNORE_TIMESTAMP = True

        scrapy_settings = get_project_settings()

        # shut off annoying debug level core api messages
        import scrapy
        scrapy.core.engine.logger.setLevel(scrapy_settings.get('LOG_LEVEL','WARNING'))
        self.logger.logger.setLevel(scrapy_settings.get('LOG_LEVEL','WARNING'))

    def print_debug(self):
        """
        Collects and prints a structured debug message
        """
        message = """
    {bar}

    {title}

      Scraping LLPs: {llps}
      Ignoring Timestamps: {IGNORE_TIMESTAMP}
      Base URL:      {url}

    {bar}
        """.format(
            bar=cyan(
                '############################################################'),
            title=red(self.title),
            llps=self.LLP or "Not applicable",
            url=self.BASE_URL,
            IGNORE_TIMESTAMP=self.IGNORE_TIMESTAMP,
        )
        self.logger.info(message)

    def get_urls(self):
        """
        Returns a list of URLs to scrape
        """

        def unmangle_url(url):
            from scrapy import Selector
            if not '<a' in url:
                u = url
            else:
                u = Selector(text=url).xpath('//a/@href').extract()[0]
            if not '//' in u:
                u='{}{}'.format(BASE_HOST,u)
            return u

        urls = []
        if self.LLP:
            for i in self.LLP:
                roman_numeral = roman.toRoman(i)
                options = self.URLOPTIONS.copy()
                options['GP'] = roman_numeral
                url_options = urlencode(options)
                url_llp = "{}?{}".format(self.BASE_URL, url_options)
                rss = feedparser.parse(url_llp)

                self.logger.info("GP {}: {} laws".format(
                    roman_numeral, len(rss['entries']))
                )
                urls = urls + [unmangle_url(entry['link'])
                               for entry in rss['entries']]

        self.TOTAL_COUNTER = len(urls)
        return urls
