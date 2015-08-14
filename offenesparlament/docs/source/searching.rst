Search Provider: Haystack, Elasticsearch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This section describes the search and indexing implementation.

Basics
======

The current application relies on `Django Haystack <http://haystacksearch.org/>`_, a high-level framework brokering between Django and a search backend. This search backend is currently `ElasticSearch <https://www.elastic.co/>`_, but could be interchanged for `Apache SOLR <http://lucene.apache.org/solr/>`_, should the need arise.

Re-Indexing
===========

For now, reindexing (or updating the index, for that matter), is only done manually. To have all data indexed, just run::

    python manage.py rebuild_index

for a full rebuild (wipes the indices first), or::

    python manage.py update_index

to perform a simple update. For this to succeed, make sure ElasticSearch is up and running.

SearchViews
===========

Searching is split between different contexts, represented by different Django views (cf. ``offenesparlament/search_views.py``):

#. Main Search (all indices), at ``/search``
#. Persons, at ``personen/search``
#. Laws, at ``gesetze/search``

Each view determines the available `facets` - for instance, the `Person` view returns, among others, faceting information for the person's `party` in it's results.

The views all inherit from ``JsonSearchView``, an adaptation of Haystack's ``SearchView`` that, instead of rendering a template, returns JSON data to be processed by the frontend.

Each accepts a query parameter, `q`, and a list of `facet filters`, named like the facets available for that view:

Main Search
    * No Facets

Persons
    * party: A person's party, for instance, SPÖ
    * birthplace: A persons birthplace
    * deathplace: A persons deathplace
    * occupation: A persons occupation
    * llps: The legislative period(s) a person was/is active during

Laws
    * category: A law's category
    * keywords: A law's assigned keywords
    * llp: The legislative period of a law

Each of the facet filters means each resulting entry must `contain` the term, but it is not specifiying exact searches; for instance, filtering fields that might contain multiple entries like a person's active legislative periods, for instance, will return all persons that have the period in question `in` their list, not just persons whose list contains `only` the period in question.

The query parameter searches in the index's `text` field - an aggregate field containing most of the other fields to allow more specific searches.

All parameters have to be supplied as GET-Parameters. A typical request might look like this::

  http://offenesparlament.vm:8000/personen/search?q=Franz&llps=XXIV&party=SP%C3%96

and would return the following JSON data::

  {
     "facets":{
        "fields":{
           "party":[
              [
                 "SP\u00d6",
                 2
              ]
           ],
           "birthplace":[
              [
                 " Wien",
                 1
              ],
              [
                 " Wels",
                 1
              ]
           ],
           "llps":[
              [
                 "XXIV",
                 2
              ],
              [
                 "XXIII",
                 2
              ],
              [
                 "XXV",
                 1
              ],
              [
                 "XXII",
                 1
              ],
              [
                 "XXI",
                 1
              ],
              [
                 "XX",
                 1
              ]
           ],
           "deathplace":[
              [
                 "",
                 2
              ]
           ],
           "occupation":[
              [
                 " Kaufmann",
                 1
              ],
              [
                 " Elektromechaniker",
                 1
              ]
           ]
        },
        "dates":{

        },
        "queries":{

        }
     },
     "result":[
        {
           "birthplace":" Wien",
           "party_exact":"SP\u00d6",
           "llps_exact":[
              "XXIV",
              "XXIII",
              "XXII",
              "XXI",
              "XX"
           ],
           "text":"PAD_03599\nFranz Riepl\nRiepl Franz\n Wien\n\n Elektromechaniker",
           "birthdate":"1949-03-23T00:00:00",
           "llps":[
              "XXIV",
              "XXIII",
              "XXII",
              "XXI",
              "XX"
           ],
           "deathdate":null,
           "deathplace":"",
           "full_name":"Franz Riepl",
           "occupation_exact":" Elektromechaniker",
           "party":"SP\u00d6",
           "deathplace_exact":"",
           "birthplace_exact":" Wien",
           "reversed_name":"Riepl Franz",
           "source_link":"http://www.parlament.gv.at/WWER/PAD_03599/index.shtml",
           "occupation":" Elektromechaniker"
        },
        {
           "birthplace":" Wels",
           "party_exact":"SP\u00d6",
           "llps_exact":[
              "XXIV",
              "XXIII",
              "XXV"
           ],
           "text":"PAD_35495\nFranz Kirchgatterer\nKirchgatterer Franz\n Wels\n\n Kaufmann",
           "birthdate":"1953-09-24T00:00:00",
           "llps":[
              "XXIV",
              "XXIII",
              "XXV"
           ],
           "deathdate":null,
           "deathplace":"",
           "full_name":"Franz Kirchgatterer",
           "occupation_exact":" Kaufmann",
           "party":"SP\u00d6",
           "deathplace_exact":"",
           "birthplace_exact":" Wels",
           "reversed_name":"Kirchgatterer Franz",
           "source_link":"http://www.parlament.gv.at/WWER/PAD_35495/index.shtml",
           "occupation":" Kaufmann"
        }
     ]
  }

Indices
=======

WARNING: Currently, only two seperate indices exist, one for the Laws and one for the Persons. These are subject to heavy development in the future and will change a lot still, so this documentation will remain mostly blank for now.

The indices are defined in ``op_scraper/search_indexes.py``. Each index contains a `text` field, which aggregates the objects' data into a single, text-based field, which Haystack uses as the default search field. The exact makeup of this field is defined in `templates`, located at ``offenesparlament/templates/search/indexes/op_scraper/*_text.html``.
