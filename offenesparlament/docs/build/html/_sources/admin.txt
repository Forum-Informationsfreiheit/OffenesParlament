Django Admin Interface
~~~~~~~~~~~~~~~~~~~~~~

The Django Administration Interface has been extended with a few vital functions to make maintainance easier.

Manually trigger scraping
=========================

Besides the usual CRUD-Interfaces, which should only be used for debugging purposes, given that the site's entire data should be automatically scraped from the parliament website, a new block called `Scraping Management` has been added, which allows manually triggering one of the following spiders:

#. Legislative Periods
#. Persons
#. Administrations
#. Pre-Laws
#. Laws

The order of the scrapers above represents their dependencies on each other; for instance, scanning laws includes votes and speeches by Persons, and relies on the Person in question having been scraped before. To be sure, the order above should be maintained in all scraping processes.

Behind the scenes, the scraping view `offenesparlament.op_scraper.admin_views.trigger_scrape` calls the celery task `offenesparlament.op_scraper.tasks.scrape`, which in turn finds and executes the requested scraper, but wraps this in a `django-reversion` block to create new revisions of all affected database objects.

Import-Export
=============

To allow import-export, the `import_export` django module is being used, overwriting the ``templates/admin/changelist.html`` admin template to be compatible with `django_reversion`.