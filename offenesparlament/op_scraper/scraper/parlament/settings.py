# -*- coding: utf-8 -*-

# Scrapy settings for laws project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'scraper'

SPIDER_MODULES = ['parlament.spiders']
NEWSPIDER_MODULE = 'parlament.spiders'

BASE_URL = "http://www.parlament.gv.at/PAKT/RGES/filter.psp"

# Gesetzgebungsperioden (legislation periods) to scrape
LLP = range(24, 26)
# LLP = [25]


URLOPTIONS = {
    'view': 'RSS',
    'jsMode': 'RSS',
    'xdocumentUri': '/PAKT/RGES/index.shtml',
    'anwenden': 'Anwenden',
    'RGES': 'ALLE',
    'SUCH': ' ',
    'listeId': '103',
    'FBEZ': 'FP_003',
}

LOG_LEVEL = 'INFO'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'laws (+http://www.yourdomain.com)'
