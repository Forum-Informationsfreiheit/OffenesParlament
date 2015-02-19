import feedparser
import roman
base_url = "http://www.parlament.gv.at/PAKT/RGES/filter.psp"

# sample link for single law
# http://www.parlament.gv.at/PAKT/VHG/XXV/I/I_00458/index.shtml


def get_laws(GP="XXV"):
    """
    Returns the RSS url for the requested Gesetzgebungsperiode
    """
    url_options = "view=RSS&jsMode=RSS&xdocumentUri=%2FPAKT%2FRGES%2Findex.shtml&GP={}&anwenden=Anwenden&RGES=ALLE&SUCH=&listeId=103&FBEZ=FP_003".format(
        GP)
    laws_url = "{}?{}".format(base_url, url_options)
    return laws_url


def scrape_laws(entries):
    """
    Scrapes a list of laws
    """
    from twisted.internet import reactor
    from scrapy.crawler import Crawler
    from scrapy.settings import Settings
    from scrapy import log
    import sys
    sys.path.append('../scrapers/laws/laws')
    from spiders.laws_initiatives import LawsInitiativesSpider

    links = [entry['link'] for entry in entries]

    spider = LawsInitiativesSpider(urls=links)
    crawler = Crawler(Settings())
    crawler.configure()
    crawler.crawl(spider)
    crawler.start()
    log.start()
    reactor.run()  # the script will block here

# GPS = range(1, 26)
GPS = [25]

for i in GPS:
    roman_numeral = roman.toRoman(i)
    rss = feedparser.parse(get_laws(roman_numeral))
    print "GP {}: {} laws".format(roman_numeral, len(rss['entries']))
    scrape_laws(rss['entries'])
