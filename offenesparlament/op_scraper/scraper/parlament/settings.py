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

BASE_HOST = "https://www.parlament.gv.at"

LOG_LEVEL = 'INFO'
LOG_ENABLED = False
DOWNLOADER_STATS = False
STATS_ENABLED = False
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'laws (+http://www.yourdomain.com)'


# CONCURRENT_REQUESTS_PER_DOMAIN = 4
# CONCURRENT_REQUESTS = 8

AUTOTHROTTLE_ENABLED = False

# Cache requests:
#DOWNLOADER_MIDDLEWARES = {
#    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
#}
#HTTPCACHE_POLICY = 'scrapy.extensions.httpcache.DummyPolicy'
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
#HTTPCACHE_ENABLED = True
#HTTPCACHE_DIR = '/tmp/scrapy-cache'
