import datetime
from django.utils.html import remove_tags
from scrapy import Selector

from parlament.resources.extractors import MultiExtractor
from parlament.resources.util import _clean

import re
import time
import datetime

# import the logging library
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class PETITION:

    class SIGNATURE_COUNT(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[4]/p[2]/span/text()'

        @classmethod
        def xt(cls, response):
            raw_signature_count=response.xpath(cls.XPATH).extract()
            if len(raw_signature_count) > 0:
                # sometimes there can be signatures also in the next llp, find all numbers in text
                raw_count = re.findall(r'\d+', raw_signature_count[0])
                if len(raw_count) > 0:
                    count = int(raw_count[0])
                    return count

            return 0


    class CREATORS(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[starts-with(text(),"{}")]'

        @classmethod
        def xt(cls, response):
            XPATH_BI_creator = cls.XPATH.format("Erstunterzeichner")
            XPATH_PET_creator = cls.XPATH.format("eine Petition")

            creators = []

            raw_creators_list = response.xpath(XPATH_PET_creator).extract()
            if len(raw_creators_list) > 0:
                # PET started by members of parliament
                for raw_creator in raw_creators_list:
                    creator_sel = Selector(text=raw_creator)
                    raw_parl_id_url = creator_sel.xpath("//a/@href").extract()
                    name = u''
                    parl_id = u''
                    if len(raw_parl_id_url) > 0:
                        raw_parl_id = raw_parl_id_url[0].split("/")
                        if len(raw_parl_id) > 1:
                            parl_id = raw_parl_id[2]
                    raw_name = creator_sel.xpath("//a/text()").extract()
                    if len(raw_name) > 0:
                        name = raw_name[0]
                    if parl_id != u'' and name != u'':
                        creators.append((parl_id, name))
            else:
                raw_creators_list = response.xpath(XPATH_BI_creator).extract()
                if len(raw_creators_list) > 0:
                    # BI first signed by a person
                    name = _clean(raw_creators_list[0].split("\t")[1])
                    creators.append(("", name))
                # VBG seem to have no visible "starter"

            return creators

    class SIGNING(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/ul/li/a'

        @classmethod
        def xt(cls, response):
            raw_url_list = response.xpath(cls.XPATH).extract()
            if len(raw_url_list) > 0:
                raw_url = raw_url_list[0]
                url_sel = Selector(text=raw_url)
                text = url_sel.xpath('//text()').extract()
                if text[0] == u'Hier k\xf6nnen Sie zustimmen':
                    signing_url = url_sel.xpath('//@href').extract()
                    return signing_url, True
            return '', False

    class OPINIONS(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/h4[text()="Stellungnahmen"]/following-sibling::ul[1]/li'

        @classmethod
        def xt(cls, response):
            ops = []
            raw_ops = response.xpath(cls.XPATH).extract()
            for raw_op in raw_ops:
                op_sel = Selector(text=raw_op)

                raw_url = op_sel.xpath('//a/@href').extract()
                if len(raw_url) > 0:
                    url = raw_url[0]
                else:
                    url = u''
                raw_parl_id = op_sel.xpath('//span/text()').extract()
                if len(raw_parl_id) > 0:
                    parl_id = raw_parl_id[0]
                else:
                    parl_id = u''

                # TODO: check what title should be
                # title = op_sel.xpath('//td[3]/text()').extract()[0]
                # if title:
                #    title = _clean(title).replace("*", ", ")
                # else:
                #    title = None

                email = op_sel.xpath('//a[@class="mail"]/@href').extract()
                if email:
                    email = email[0].replace('mailto:', '')
                    # title = op_sel.xpath('//td[3]/a/text()').extract()[0]
                else:
                    email = None
                ops.append({
                    'date': '',  # date,
                    'url': url,
                    'email': email,
                    'title': '',  # title,
                    'parl_id': parl_id
                })

            return ops

    class REFERENCE(MultiExtractor):

        XPATH = '//*[@id="content"]/div[3]/div[2]/div[2]/p[starts-with(text(),"Neuverteilung")]/a/@href'

        @classmethod
        def xt(cls, response):
            raw_reference = response.xpath(cls.XPATH).extract()
            if len(raw_reference) > 0:
                ref_url = raw_reference[0]
                splitted_url = ref_url.split('/')
                llp = u''
                parl_id = u''
                if len(splitted_url) > 4:
                    llp = splitted_url[3]
                    raw_parl_id = splitted_url[5].split('_')
                    if len(raw_parl_id) > 1:
                        pet_type = raw_parl_id[0]
                        number = int(raw_parl_id[1])
                        parl_id = u'({}/{})'.format(number, pet_type)

                return llp, parl_id

            return None

    class SIGNATURES(MultiExtractor):

        XPATH = '//*[@id="filterListeBI_001"]/table/tr'

        @classmethod
        def xt(cls, response):
            raw_signatures = response.xpath(cls.XPATH).extract()

            signatures = []
            for raw_signature in raw_signatures:
                sig_sel = Selector(text=raw_signature)
                signature_list = sig_sel.xpath('//td/text()').extract()
                if len(signature_list) > 0:
                    full_name = _clean(signature_list[0])

                    if len(signature_list) > 1:
                        postal_code = _clean(signature_list[1])
                    else:
                        postal_code = u''

                    if len(signature_list) > 2:
                        location = _clean(signature_list[2])
                    else:
                        location = u''

                    if len(signature_list) > 3:
                        raw_date = time.strptime(_clean(signature_list[3]), '%d.%m.%Y')
                        date = datetime.date.fromtimestamp(time.mktime(raw_date))
                    else:
                        date = datetime.date.fromtimestamp(0)

                    signatures.append({
                        'full_name': full_name,
                        'postal_code': postal_code,
                        'location': location,
                        'date': date
                    })

            return signatures
