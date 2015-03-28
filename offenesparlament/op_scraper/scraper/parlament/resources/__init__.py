# Base Classes


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
