Django Admin Interface
~~~~~~~~~~~~~~~~~~~~~~

The Django Administration Interface has been extended with a few vital functions to make maintainance easier.

Besides the usual CRUD-Interfaces, which should only be used for debugging purposes, given that the site's entire data should be automatically scraped from the parliament website, a new block called `Scraping Management` has been added, which allows manually triggering one of the following spiders:

#. Legislative Periods
#. Persons
#. Pre-Laws
#. Laws

The order of the scrapers above represents their dependencies on each other; for instance, scanning laws includes votes and speeches by Persons, and relies on the Person in question having been scraped before. To be sure, the order above should be maintained in all scraping processes.

Import-Export
=============

To allow import-export, the `import_export` django module is being used, overwriting the ``templates/admin/changelist.html`` admin template to be compatible with `django_reversion`.