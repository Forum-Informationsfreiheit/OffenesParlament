General Information
===================

This section outlines the general setup of OffenesParlament.at.

Structure - What is Where?
~~~~~~~~~~~~~~~~~~~~~~~~~~

OffenesParlament.at is a (set of) Django applications. It's roughly divided into
two parts: the `Scraping` part, which takes care of data aggregation and parsing of the website of the `Austrian Parliament <http://www.parlament.gv.at/>`_, and the `Presentation` part, which presents the collected data in the form of a searchable web application.

The `Scraping` part can be found in the subfolder ``offenesparlament/op_scraper``, wheras the `Presentation` part is largely gathered in the folder ``offenesparlament/offenesparlament``.

The search engine parts transcend each of those projects, with the search views being located in ``/offenesparlament/offenesparlament/search_views.py``, but the `search_indexes` being located in ``/offenesparlament/op_scraper/search_indexes.py``.

In future, the Email-Subscription service will also be located in both parts, given that we will have to offer a subscription logic in the webapp itself (with a set of views to faciliate that), but also trigger the sending of those emails via the scraper upon changing the database.

Frontend Code
-------------

All sources for the frontend code (JS and CSS) are located in
``client/`` and split between ``scripts`` and
``styles``. We use CoffeeScript and the React framework for client code. To
generate JS and CSS from the sources we use grunt (``Gruntfile.coffee`` is in
the root dir).

All generated files are put in ``offenesparlament/offenesparlament/static/`` by grunt.
