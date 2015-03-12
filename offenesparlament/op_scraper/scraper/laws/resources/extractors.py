from laws.resources import SingleExtractor
from laws.resources import MultiExtractor


class TITLE(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/text()'


class PARL_ID(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/span/text()'


class KEYWORDS(MultiExtractor):
    XPATH = '//*[@id="schlagwortBox"]/ul//li/a/text()'


class DOCS(MultiExtractor):
    XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/div/ul//li/a[1]/text()'
