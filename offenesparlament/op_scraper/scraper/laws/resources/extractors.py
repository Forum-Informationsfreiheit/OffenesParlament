from django.utils.html import remove_tags
from scrapy import Selector

from laws.resources import SingleExtractor
from laws.resources import MultiExtractor


class TITLE(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/text()'


class PARL_ID(SingleExtractor):
    XPATH = '//*[@id="inhalt"]/span/text()'


class KEYWORDS(MultiExtractor):
    XPATH = '//*[@id="schlagwortBox"]/ul//li/a/text()'


class DOCS(MultiExtractor):
    LI_XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/div/ul/li'

    @classmethod
    def xt(cls, response):
        docs = []
        raw_docs = response.xpath(cls.LI_XPATH)
        for raw_doc in raw_docs:
            html_url, pdf_url = "", ""
            urls = raw_doc.css('a').xpath('@href').extract()
            for url in urls:
                if url.endswith('.pdf'):
                    pdf_url = url
                elif url.endswith('.html'):
                    html_url = url
            title = Selector(text=raw_doc.extract()).xpath(
                '//a[1]/text()').extract()[0]
            title = title[:title.index('/')].strip()
            docs.append({
                'title': title,
                'html_url': html_url,
                'pdf_url': pdf_url
            })
        return docs


class STATUS(SingleExtractor):
    XPATH = '//*[@id="content"]/div[3]/div[2]/div[1]/div[1]/p'

    @classmethod
    def xt(cls, response):
        status = remove_tags(
            response.xpath(cls.XPATH).extract()[0], 'em img p')
        status = status.replace('Status: ', '')
        return status


class CATEGORY(SingleExtractor):
    XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/h3/text()'


class DESCRIPTION(SingleExtractor):
    XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[1]'

    @classmethod
    def xt(cls, response):
        description = response.xpath(cls.XPATH).extract()[0]
        return remove_tags(description, 'p')
