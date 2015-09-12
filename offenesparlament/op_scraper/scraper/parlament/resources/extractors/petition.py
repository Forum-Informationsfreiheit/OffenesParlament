import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import SingleExtractor
from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean
from parlament.settings import BASE_HOST

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PETITION:

    class TITLE(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/text()'

    class PARL_ID(SingleExtractor):
        XPATH = '//*[@id="inhalt"]/span/text()'
