Scraping: Scrapy Spiders and Extractors
=======================================

This section describes the scraping setup and processes.

Structure
~~~~~~~~~

The scraper is located in the subfolder ``/offenesparlament/op_scraper``. It contains the
Django models (cf. ``/offenesparlament/op_scraper/models.py``), some `admin views` and `admin dashboard` adaptations, as well as the `Austrian Parliament <http://www.parlament.gv.at/>`_ scaper itself, situated at ``/offenesparlament/op_scraper/scraper/parlament``.

A scrapy scraper consists of a set of `spiders` - a single process capable of scanning, parsing and in injecting data from a website into a database. Currently, the following spiders exist:

* **laws_initiatives**: Scrapes the Laws and Government Initiatives as found on `this page <http://www.parlament.gv.at/PAKT/RGES/>`_
* **pre_laws**: Scrapes laws that are still in the pre-parliamentary process, as shown on `this list <http://www.parlament.gv.at/PAKT/MESN/>`_
* **llp**: Scrapes the list of available legislative periods
* **persons**: Scans 'Parlamentarier' as found `here <http://www.parlament.gv.at/WWER/SUCHE/>`_
* **administrations**: A secondary spider that also scans Persons, this time focused on their mandates as part of specific administrations, as shown `in here <http://www.parlament.gv.at/WWER/BREG/REG/>`_
* **statements**: Scrapes Debates and DebateStatements. Requires `llp` and `persons` for lookup.

Each of those spiders inherits from `BaseSpider` (cf. ``/offenesparlament/op_scraper/scraper/parlament/spiders/__init__.py``), which offers some generic methods to be used by different spiders.

Besides the spiders themselves, which handle getting the response from the subsite of `parlament.gv.at` and creating the django objects based on the scraped data, the `Extractors` (to be found at ``/offenesparlament/op_scraper/scraper/parlament/resources/extractors``) do the actual heavy lifting of translating the raw html data into meaningful, structured data (mostly in the form of dictionaries and lists) by using XPATH expressions.

Spiders
*******

Spiders are the managing part of the scraping process. At the bare minimum, a spider consists of an Constructor (the `__init__` method), which is responsible for populating the ``self.start_urls`` list with all the web-adresses to be scanned, as well as a parse method, which gets to be called with the response from each of the entries in the ``self.start_urls`` list. Furthermore, each spider **must** have a member variable ``name`` set, which will identify it for the command line calls.

The following is a simple example or code skeleton of a spider::

    # -*- coding: utf-8 -*-
    from parlament.settings import BASE_HOST
    from parlament.spiders import BaseSpider
    from parlament.resources.extractors.example import EXAMPLE_EXTRACTOR
    from ansicolor import green

    from op_scraper.models import ExampleObject


    class ExampleSpider(BaseSpider):
        BASE_URL = "{}/{}".format(BASE_HOST, "/WWER/PARL/")

        name = "example"

        def __init__(self, **kw):
            super(ExampleSpider, self).__init__(**kw)

            self.start_urls = [self.BASE_URL]

        def parse(self, response):

            data_sets = EXAMPLE_EXTRACTOR.xt(response)

            for data_set in data_sets:
                item, created = ExampleObject.objects.update_or_create(
                    name=data_set['name'],
                    defaults=data_set
                )
                item.save()

                if created:
                    self.logger.info(u"Created ExampleObject {}".format(
                        green(u'[{}]'.format(data_set['name']))))
                else:
                    self.logger.info(u"Updated Legislative Period {}".format(
                        green(u"[{}]".format(data_set['name']))
                    ))

Not all database/django objects can be fully extracted through a single page.
For instance, the `Person` objects need to be discovered through one of the
abovementioned lists, but their details can only be extracted from a secondary
person detail page. To accomodate this, scrapy's callback functions can be used
like this person spider skeleton::

    def parse(self, response):

        # Parse person list
        # [...]

        callback_requests = []
        for p in person_list:
            # Create Detail Page request
            req = scrapy.Request(person_detail_page_url,
                                 callback=self.parse_person_detail)
            req.meta['person'] = {
                'reversed_name': p['reversed_name'],
                'source_link': p['source_link'],
                'parl_id': parl_id
            }
        callback_requests.append(req)

    return callback_requests

    def parse_person_detail(self, response):

        person = response.meta['person']

        # Parse Person detail page
        # [...]

In the above example, the spider will start making secondary requests to retrieve
the detail pages, and call the parse_person_detail with the responses. As shown above,
the request for the secondary page contains a member variable `meta` that can be
used to transfer already created data to the secondary response to continue working
with the same person and provide some continuity.

Saving/Updating the models
##########################

Currently, the spiders do not need to take care of versioning the changes they scrape;
since the page needs to be requested and scraped already to be able to determine
if there were any changes, the spiders should simply update existing objects or
create new ones where necessary. Since the OffenesParlament.at app also employs `django.reversion`
to version the changes to the database, it can be possible to trace changes to the objects
via versions rather than during the scraping process itself, although this is
not yet implemented due to the fact that the email-subscription service hasn't
been realized yet.

Keyword parameters
##################

To specify additional (optional) keyword parameters for the spiders,
the `__init__` method accepts a `kw` parameter, which contains a dictionary of
keys and values supplied from the commandline. For instance, the `laws_initiatives`
spider accepts an additional `llp` parameter::

    python manage.py scrape crawl -a llp=21 laws_initiatives

In the spider itself, this parameter can be extracted like this::

    def __init__(self, **kw):
        super(LawsInitiativesSpider, self).__init__(**kw)
        if 'llp' in kw:
            try:
                self.LLP = [int(kw['llp'])]
            except:
                pass
        # [...]

Extractors
**********

Extractors take over the heavy lifting - by translating the raw html source code they are
handed into organized data, ready for insertion into the database.

The simplest extractor just inherits from ``parlament.resources.extractors.SingleExtractor``, which provides an `xt` method and utilizes a simple class variable containing the XPath expression to extract, expecting it to evaluate to exactly one result. For instance, the `title` of a `law` detail page might be extracted by the following class::

    from parlament.resources.extractors import SingleExtractor

    class LAW:
        class TITLE(SingleExtractor):
            XPATH = '//*[@id="inhalt"]/text()'

Similarly, to simply extract a list of items based on an XPath expression, the following code could be used::

    class LAW:
        class KEYWORDS(MultiExtractor):
            XPATH = '//*[@id="schlagwortBox"]/ul//li/a/text()'

In reality, many of the extractors overwrite the `xt` method to implement more complex extractions.
