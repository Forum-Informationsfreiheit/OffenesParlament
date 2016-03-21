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
#. debates, at ``debatten/search``

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
    * ts: The timestamp that entry was last updaten (from the parlament site)

Laws
    * category: A law's category
    * keywords: A law's assigned keywords
    * llp: The legislative period of a law
    * ts: The timestamp that entry was last updaten (from the parlament site)

Debates
    * llp: The legislative period a debate fell into
    * debate_type: either NR or BR (Nationalrat/Bundesrat)
    * date: The date the debate happened

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

Facet Only Search
-----------------

Besides the normal, query-based search, it is possible to retrieve only the
facets (for and empty query, for instance). This is necessary to allow filling of
dropdown/selection boxes before the first search. A typical request might then
look like this::

  http://offenesparlament.vm:8000/personen/search?q=&only_facets=true

But this facet-only search also works with a query, should that be necessary::

  http://offenesparlament.vm:8000/personen/search?q=Mayer&only_facets=true

The result looks like the above-mentioned search result, but always contains an
empty list in the 'results' field.

Paging
------

In addition to the query arguments for filtering and facetting, the search views
also automatically limit the results to allow for smooth paging. Two parameters
govern this behaviour: `offset` and `limit`.

`Offset` returns search results from
the given integer on - so, for a search that produced 100 results, an offset
value of '20' would only return results 20 to 100.
If no `offset` value is given, the view assumes '0' and returns results
starting with the first one.

`Limit` restricts the amount of results per page; with the abovementioned
example and a `limit` value of '50', the query would only return results
20 through 70.
If no `limit` is given, the view assumes a default of 50 results. This can be
changed in the ``offenesparlament/constants.py`` file.

Fieldsets
---------

Given the amount of data in the index (particularly the debate statements),
returning the entirety of an object including all of it's fields is not
performant enough for long lists of results. To combat that issue, the concept
of predefined fieldsets has been introduced. Each index class now contains a
FIELDSET dictionary which defines the available fieldsets. The debate class, for
instance, contains the following fieldsets::

  FIELDSETS = {
        'all': ['text', 'date', 'title', 'debate_type', 'protocol_url', 'detail_url', 'nr', 'llp', 'statements'],
        'list': ['text', 'date', 'title', 'debate_type', 'protocol_url', 'detail_url', 'nr', 'llp'],
    }

The dictionary key describes the fieldset, and the value consists of a list of
all fields that should be returned when requesting that fieldset.

Per default, the search view only returns the 'list' fieldset; if a search
request must return all available data, the 'fieldset' parameter allows querying
the for a specific fielset fieldset::

  http://offenesparlament.vm:8000/personen/search?parl_id=PAD_65677&fieldset=all

Single Result Search
--------------------

The normal search will always be aimed at finding a list of entries that match
the query, but for the detail pages (and the subscriptions), a search mode that
returns exactly one result was needed. This view can be accessed by, instead of
adding in facet filters, filter by 'parl_id' (for persons) or by 'parl_id' and
'llp' for laws.

For instance, a typical request for a single person's data might look like this::

  http://offenesparlament.vm:8000/personen/search?parl_id=PAD_65677&detail=True

This would yield a result similar to the following::

  {
    "result":[
        {
            "debate_statements":"[]",
            "birthplace":" Kufstein (Tirol)",
            "deathdate":null,
            "statements":"            [
                {
                    \"law_id\":6814,
                    \"law_slug\":\"/gesetze/XXV/905_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2016-02-11\",
                    \"protocol_url\":null,
                    \"law\":\"Pflanzenschutzgesetz 2011,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7298,
                    \"law_slug\":\"/gesetze/XXV/81-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-01-31\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00826/SEITE_0026.html\",
                    \"law\":\"Bundesministeriengesetz 1986,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7285,
                    \"law_slug\":\"/gesetze/XXV/111-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-02-26\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00827/SEITE_0122.html\",
                    \"law\":\"Umweltvert\\u00e4glichkeitspr\\u00fcfungsgesetz 2000,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7268,
                    \"law_slug\":\"/gesetze/XXV/14_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-04-10\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00828/SEITE_0181.html\",
                    \"law\":\"26. StVO-Novelle\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7262,
                    \"law_slug\":\"/gesetze/XXV/113-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-04-10\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00828/SEITE_0185.html\",
                    \"law\":\"Kraftfahrgesetz 1967,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7259,
                    \"law_slug\":\"/gesetze/XXV/261-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-04-10\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00828/SEITE_0187.html\",
                    \"law\":\"SP-V-Gesetz-Novelle 2014\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7253,
                    \"law_slug\":\"/gesetze/XXV/5_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2014-05-15\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00829/SEITE_0128.html\",
                    \"law\":\"Internes Abkommen \\u00fcber die Finanzierung der vorgesehenen Hilfe der Europ\\u00e4ischen Union im Rahmen des AKP EU Partnerschaftsabkommens\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7252,
                    \"law_slug\":\"/gesetze/XXV/13_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2014-05-15\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00829/SEITE_0128.html\",
                    \"law\":\"Abkommen mit der Internationalen Organisation f\\u00fcr Migration \\u00fcber den rechtlichen Status der Organisation in \\u00d6sterreich und dem Sitz ihrer B\\u00fcros in Wien\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7251,
                    \"law_slug\":\"/gesetze/XXV/15_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2014-05-15\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00829/SEITE_0128.html\",
                    \"law\":\"Abkommen mit Zypern \\u00fcber die Verwendung von Flugh\\u00e4fen\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7247,
                    \"law_slug\":\"/gesetze/XXV/29_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2014-05-15\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00829/SEITE_0128.html\",
                    \"law\":\"Rahmenabkommen \\u00fcber Partnerschaft\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7245,
                    \"law_slug\":\"/gesetze/XXV/71_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2014-05-15\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00829/SEITE_0128.html\",
                    \"law\":\"Abkommen zur zweiten \\u00c4nderung des Partnerschaftsabkommens mit Afrika-,
                    Karibik- und Pazifik-Staaten und der EU samt Schlussakte einschlie\\u00dflich der dieser beigef\\u00fcgten Erkl\\u00e4rungen\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7238,
                    \"law_slug\":\"/gesetze/XXV/53_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-05-28\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00830/SEITE_0061.html\",
                    \"law\":\"Budgetbegleitgesetz 2014\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7235,
                    \"law_slug\":\"/gesetze/XXV/101_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-05-28\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00830/SEITE_0061.html\",
                    \"law\":\"Grunderwerbsteuergesetz 1987,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7234,
                    \"law_slug\":\"/gesetze/XXV/126_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-05-28\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00830/SEITE_0061.html\",
                    \"law\":\"Begr\\u00fcndung von Vorbelastungen durch die Bundesministerin f\\u00fcr Verkehr,
                    Innovation und Technologie\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7218,
                    \"law_slug\":\"/gesetze/XXV/142_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-06-26\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00831/SEITE_0043.html\",
                    \"law\":\"Marktordnungsgesetz 2007,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7143,
                    \"law_slug\":\"/gesetze/XXV/318_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-12-04\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00836/SEITE_0060.html\",
                    \"law\":\"Eisenbahngesetz 1957,
                    Unfalluntersuchungsgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7137,
                    \"law_slug\":\"/gesetze/XXV/295-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-12-04\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00836/SEITE_0065.html\",
                    \"law\":\"Stra\\u00dfenverkehrsordnung 1960,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7135,
                    \"law_slug\":\"/gesetze/XXV/721-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2014-12-04\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00836/SEITE_0065.html\",
                    \"law\":\"Kraftfahrgesetz 1967,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7100,
                    \"law_slug\":\"/gesetze/XXV/364_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-12-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00837/SEITE_0043.html\",
                    \"law\":\"Wehrgesetz 2001,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7096,
                    \"law_slug\":\"/gesetze/XXV/369_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-12-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00837/SEITE_0185.html\",
                    \"law\":\"Universit\\u00e4tsgesetz 2002,
                    Hochschulgesetz 2005,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7094,
                    \"law_slug\":\"/gesetze/XXV/371_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2014-12-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00837/SEITE_0078.html\",
                    \"law\":\"Chemikaliengesetz 1996,
                    Bundeskriminalamt-Gesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7080,
                    \"law_slug\":\"/gesetze/XXV/445_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-02-05\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00838/SEITE_0078.html\",
                    \"law\":\"Fortpflanzungsmedizinrechts-\\u00c4nderungsgesetz 2015\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":7032,
                    \"law_slug\":\"/gesetze/XXV/460_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-05-07\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00841/SEITE_0107.html\",
                    \"law\":\"Passagier- und Fahrgastrechteagenturgesetz\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7030,
                    \"law_slug\":\"/gesetze/XXV/510_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-05-07\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00841/SEITE_0098.html\",
                    \"law\":\"Kraftfahrliniengesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7029,
                    \"law_slug\":\"/gesetze/XXV/511_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-05-07\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00841/SEITE_0098.html\",
                    \"law\":\"\\u00d6ffentlicher Personennah- und Regionalverkehrsgesetz 1999,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7012,
                    \"law_slug\":\"/gesetze/XXV/584_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-06-03\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00842/SEITE_0083.html\",
                    \"law\":\"Bundesbahngesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":7007,
                    \"law_slug\":\"/gesetze/XXV/585_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-06-03\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00842/SEITE_0083.html\",
                    \"law\":\"Dienstrechts-Novelle 2015\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6978,
                    \"law_slug\":\"/gesetze/XXV/631_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-02\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00843/SEITE_0123.html\",
                    \"law\":\"F\\u00fchrerscheingesetz (16. FSG-Novelle)\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6977,
                    \"law_slug\":\"/gesetze/XXV/1185-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2015-07-02\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00843/SEITE_0117.html\",
                    \"law\":\"Kraftfahrgesetz 1967; \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6976,
                    \"law_slug\":\"/gesetze/XXV/1191-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2015-07-02\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00843/SEITE_0117.html\",
                    \"law\":\"Kraftfahrgesetz 1967; \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6959,
                    \"law_slug\":\"/gesetze/XXV/501_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Erkl\\u00e4rung \\u00fcber die Zur\\u00fcckziehung der \\u00f6sterreichischen Vorbehalte zu Art. 13,
                    15                    und 17 sowie der Erkl\\u00e4rungen zu Art. 38 des \\u00dcbereinkommens \\u00fcber die Rechte des Kindes\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6957,
                    \"law_slug\":\"/gesetze/XXV/530_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Gentechnikgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6952,
                    \"law_slug\":\"/gesetze/XXV/617_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"EZG-Novelle 2015\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6944,
                    \"law_slug\":\"/gesetze/XXV/673_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Gentechnik-Anbauverbots-Rahmengesetz; Sortenschutzgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6940,
                    \"law_slug\":\"/gesetze/XXV/680_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Marktordnungsgesetz 2007,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6932,
                    \"law_slug\":\"/gesetze/XXV/688_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Erbrechts-\\u00c4nderungsgesetz 2015\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6931,
                    \"law_slug\":\"/gesetze/XXV/689_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Strafrechts\\u00e4nderungsgesetz 2015\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6928,
                    \"law_slug\":\"/gesetze/XXV/693_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"In Doha beschlossene \\u00c4nderung des Protokolls von Kyoto zum Rahmen\\u00fcbereinkommen der Vereinten Nationen \\u00fcber Klima\\u00e4nderungen\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6927,
                    \"law_slug\":\"/gesetze/XXV/694_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Vereinbarung zwischen der Europ\\u00e4ischen Union und ihren Mitgliedstaaten einerseits und Island andererseits \\u00fcber die Beteiligung Islands an der gemeinsamen Erf\\u00fcllung der Verpflichtungen der Europ\\u00e4ischen Union\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6925,
                    \"law_slug\":\"/gesetze/XXV/696_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Umweltinformationsgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6921,
                    \"law_slug\":\"/gesetze/XXV/1181-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2015-07-23\",
                    \"protocol_url\":null,
                    \"law\":\"Forstgesetz 1975; \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6912,
                    \"law_slug\":\"/gesetze/XXV/775_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-09-25\",
                    \"protocol_url\":null,
                    \"law\":\"27. StVO-Novelle\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6911,
                    \"law_slug\":\"/gesetze/XXV/1295-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2015-09-25\",
                    \"protocol_url\":null,
                    \"law\":\"Unterbringung und Aufteilung von hilfs- und schutzbed\\u00fcrftigen Fremden\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6910,
                    \"law_slug\":\"/gesetze/XXV/1296-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2015-09-25\",
                    \"protocol_url\":null,
                    \"law\":\"Fremdenpolizeigesetz 2005; \\u00c4nderung\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6887,
                    \"law_slug\":\"/gesetze/XXV/799_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2015-10-29\",
                    \"protocol_url\":null,
                    \"law\":\"halbt\\u00e4gig kostenlose und verpflichtende fr\\u00fche F\\u00f6rderung in institutionellen Kinderbildungs- und -betreuungseinrichtungen\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":6872,
                    \"law_slug\":\"/gesetze/XXV/823_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-11-19\",
                    \"protocol_url\":null,
                    \"law\":\"Strahlenschutzgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6858,
                    \"law_slug\":\"/gesetze/XXV/821_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-12-03\",
                    \"protocol_url\":null,
                    \"law\":\"Budgetbegleitgesetz 2016\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6857,
                    \"law_slug\":\"/gesetze/XXV/846_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2015-12-03\",
                    \"protocol_url\":null,
                    \"law\":\"Begr\\u00fcndung von Vorbelastungen durch den Bundesminister f\\u00fcr Verkehr,
                    Innovation und Technologie\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":6856,
                    \"law_slug\":\"/gesetze/XXV/883_d.B./\",
                    \"law_category\":\"Bericht und Antrag\",
                    \"date\":\"2015-12-03\",
                    \"protocol_url\":null,
                    \"law\":\"Rechnungshofgesetz 1948,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5778,
                    \"law_slug\":\"/gesetze/XXIV/2201_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0126.html\",
                    \"law\":\"\\u00dcbereinkommen \\u00fcber das Europ\\u00e4ische Forstinstitut\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5776,
                    \"law_slug\":\"/gesetze/XXIV/2252_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0114.html\",
                    \"law\":\"Umweltvertr\\u00e4glichkeitspr\\u00fcfungsgesetz 2000,
                    \\u00c4nderung; Bundesgesetz \\u00fcber den Umweltsenat,
                    Aufhebung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5773,
                    \"law_slug\":\"/gesetze/XXIV/2290_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0114.html\",
                    \"law\":\"Verwaltungsgerichtsbarkeits-Anpassungsgesetz \\u2013 Umwelt,
                    Abfall,
                    Wasser\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5772,
                    \"law_slug\":\"/gesetze/XXIV/2291_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0126.html\",
                    \"law\":\"Verwaltungsgerichtsbarkeits-Anpassungsgesetz-BMLFUW \\u2013 Land- und Forstwirtschaft\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5771,
                    \"law_slug\":\"/gesetze/XXIV/2292_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0114.html\",
                    \"law\":\"Umweltrechtsanpassungsgesetz 2013\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5770,
                    \"law_slug\":\"/gesetze/XXIV/2293_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0114.html\",
                    \"law\":\"AWG-Novelle Industrieemissionen,
                    Altlastensanierungsgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5768,
                    \"law_slug\":\"/gesetze/XXIV/2295_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0105.html\",
                    \"law\":\"Klimaschutzgesetz,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5766,
                    \"law_slug\":\"/gesetze/XXIV/2297_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-06\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00821/SEITE_0126.html\",
                    \"law\":\"Agrarrechts\\u00e4nderungsgesetz 2013\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5746,
                    \"law_slug\":\"/gesetze/XXIV/2321_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-26\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00822/SEITE_0204.html\",
                    \"law\":\"Emissionsschutzgesetz f\\u00fcr Kesselanlagen\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5741,
                    \"law_slug\":\"/gesetze/XXIV/2337_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-06-26\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00822/SEITE_0204.html\",
                    \"law\":\"Gewerbeordnung 1994,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5728,
                    \"law_slug\":\"/gesetze/XXIV/2316-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2013-06-26\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00822/SEITE_0174.html\",
                    \"law\":\"Nachhaltigkeit,
                    den Tierschutz,
                    den umfassenden Umweltschutz,
                    die Sicherstellung der Wasser- und Lebensmittelversorgung und die Forschung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5691,
                    \"law_slug\":\"/gesetze/XXIV/2361_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2013-07-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00823/SEITE_0087.html\",
                    \"law\":\"2. Vereinbarung gem\\u00e4\\u00df Artikel 15a B-VG \\u00fcber Vorhaben des Hochwasserschutzes im Bereich der \\u00f6sterreichischen Donau\",
                    \"type\":\"Pro\"
                },
                {
                    \"law_id\":5671,
                    \"law_slug\":\"/gesetze/XXIV/2408_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Bundes(verfassungs)gesetz\",
                    \"date\":\"2013-07-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00823/SEITE_0201.html\",
                    \"law\":\"AWG-Novelle Verpackung,
                    \\u00c4nderung\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5651,
                    \"law_slug\":\"/gesetze/XXIV/2447_d.B./\",
                    \"law_category\":                    \"Regierungsvorlage:Staatsvertrag\",
                    \"date\":\"2013-07-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00823/SEITE_0239.html\",
                    \"law\":\"\\u00dcbereinkommen \\u00fcber ein Einheitliches Patentgericht\",
                    \"type\":\"Contra\"
                },
                {
                    \"law_id\":5644,
                    \"law_slug\":\"/gesetze/XXIV/2323-A/\",
                    \"law_category\":\"Selbst\\u00e4ndiger Antrag\",
                    \"date\":\"2013-07-18\",
                    \"protocol_url\":\"/PAKT/VHG/BR/BRSITZ/BRSITZ_00823/SEITE_0117.html\",
                    \"law\":\"Elektrizit\\u00e4tswirtschafts- und -organisationsgesetz 2010,
                    Gaswirtschaftsgesetz 2011,
                    Energie-Control-Gesetz,
                    \\u00c4nderung\",
                    \"type\":\"Pro\"
                }
            ]            ",
  "            text":"PAD_65677\nMag. Nicole Schreyer\nSchreyer Nicole, Mag.\n Kufstein (Tirol)\n\n Biologin",
              "mandates":"[{\"function\": {\"short\": \"\", \"title\": \"Abgeordnete(r) zum Bundesrat\"}, \"end_date\": \"2013-10-28\", \"llp\": \"XXIV (2008-10-28 - 2013-10-28)\", \"state\": {\"name\": \"T\", \"title\": \"7 Tirol\"}, \"party\": {\"name\": \"T\", \"title\": \"7 Tirol\"}, \"start_date\": \"2008-10-28\"}, {\"function\": {\"short\": \"\", \"title\": \"Abgeordnete(r) zum Bundesrat\"}, \"end_date\": null, \"llp\": \"XXV (seit 2013-10-29)\", \"state\": {\"name\": \"T\", \"title\": \"7 Tirol\"}, \"party\": {\"name\": \"T\", \"title\": \"7 Tirol\"}, \"start_date\": \"2013-10-29\"}]",
              "ts":"2016-02-12T02:15:00",
              "birthdate":"1977-02-05T00:00:00",
              "reversed_name":"Schreyer Nicole, Mag.",
              "photo_copyright":"© Parlamentsdirektion / Photo Simonis",
              "llps_numeric":[
                  25,
                  24
              ],
              "deathplace":"",
              "full_name":"Mag. Nicole Schreyer",
              "source_link":"http://www.parlament.gv.at/WWER/PAD_65677/index.shtml",
              "party":"Grüne",
              "llps":"['aktuell seit 2013-10-29 (XXV)', '2008-10-28 - 2013-10-28 (XXIV)']",
              "internal_link":"/personen/PAD_65677/Mag-Nicole-Schreyer/",
              "photo_link":"http://www.parlament.gv.at/WWER/PAD_65677/6020956_180.jpg",
              "parl_id":"PAD_65677",
              "occupation":" Biologin"
          }
      ]
  }


Indices
=======

WARNING: Currently, only three seperate indices exist, one for the Laws, one for the Persons and one for the Debates. These are subject to heavy development in the future and will change a lot still, so this documentation will remain mostly blank for now.

The indices are defined in ``op_scraper/search_indexes.py``. Each index contains a `text` field, which aggregates the objects' data into a single, text-based field, which Haystack uses as the default search field. The exact makeup of this field is defined in `templates`, located at ``offenesparlament/templates/search/indexes/op_scraper/*_text.html``.
