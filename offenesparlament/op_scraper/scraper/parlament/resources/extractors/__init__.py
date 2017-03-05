# Base Classes
from datetime import datetime


class BaseExtractor:

    """
    Basic scrapy extraction class.
    """
    @classmethod
    def _xt(cls, response):
        """
        Extract based on the classes XPATH expression
        """
        value = response.xpath(cls.XPATH).extract()
        return value


class SingleExtractor(BaseExtractor):

    """
    Only extracts single elements
    """

    @classmethod
    def xt(cls, response):
        """
        Extract the first element in class's xpath-expression
        """
        try:
            value = cls._xt(response)[0].strip()
        except IndexError:
            value = ""
        return value


class MultiExtractor(BaseExtractor):

    """
    Only extracts multiple elements
    """
    @classmethod
    def xt(cls, response):
        """
        Extract all textual elements in class's xpath-expression
        """
        values = cls._xt(response)
        values = [v.strip() for v in values if isinstance(v, unicode)]
        return values


class GENERIC:

    class TIMESTAMP(SingleExtractor):
        @classmethod
        def xt(cls, response):
            tstring = response.xpath(
                '//*[@id="utilities"]/div/span/text()').extract()[0]
            tstring = tstring.replace(u'LETZTES UPDATE: ', '')
            try:
                ts = datetime.strptime(tstring, '%d.%m.%Y; %H:%M')
                return ts
            except:
                import ipdb
                ipdb.set_trace()
