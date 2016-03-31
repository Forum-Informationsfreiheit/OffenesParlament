import haystack
from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from haystack.backends.elasticsearch_backend import ElasticsearchSearchQuery
from haystack.backends.elasticsearch_backend import FIELD_MAPPINGS
from haystack.backends import BaseEngine
from haystack.constants import DJANGO_CT, DJANGO_ID
from haystack.models import SearchResult

from elasticsearch.exceptions import NotFoundError
import elasticsearch


class FuzzyElasticsearchSearchBackend(ElasticsearchSearchBackend):

    """
    Custom ES Backend that fuzzyfies the Haystack default query_string queries
    """
    # Characters reserved by Elasticsearch for special use.
    # The '\\' must come first, so as not to overwrite the other slash replacements.
    # Specifically excludes '~' to allow fuzzy searching
    RESERVED_CHARACTERS = (
        '\\', '+', '-', '&&', '||', '!', '(', ')', '{', '}',
        '[', ']', '^', '"', '*', '?', ':', '/',
    )

    DEFAULT_FIELD_MAPPING = {
        'type': 'string',
        'analyzer': 'op_german'}

    # Overwrite default Haystack settings to add our custom, supershiny op_german
    # analyzer which can do both stemming _and_ asciifolding without blowing the
    # whole <insert profanity here>-index up
    DEFAULT_SETTINGS = {
        'settings': {
            "analysis": {
                "analyzer": {
                    "ngram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["haystack_ngram", "lowercase"]
                    },
                    "edgengram_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["haystack_edgengram", "lowercase"]
                    },
                    "op_german": {
                        "tokenizer":  "standard",
                        "filter": [
                            "lowercase",
                            "german_stop",
                            "german_normalization",
                            "german_stemmer",
                            "asciifolding"
                        ]
                    }
                },
                "tokenizer": {
                    "haystack_ngram_tokenizer": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                    "haystack_edgengram_tokenizer": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15,
                        "side": "front"
                    }
                },
                "filter": {
                    "haystack_ngram": {
                        "type": "nGram",
                        "min_gram": 3,
                        "max_gram": 15
                    },
                    "haystack_edgengram": {
                        "type": "edgeNGram",
                        "min_gram": 2,
                        "max_gram": 15
                    },
                    "german_stop": {
                        "type":       "stop",
                        "stopwords":  "_german_"
                    },
                    "german_stemmer": {
                        "type":       "stemmer",
                        "language":   "light_german"
                    }
                }
            }
        }
    }

    def build_schema(self, fields):
        content_field_name = ''
        mapping = {
            DJANGO_CT: {'type': 'string', 'index': 'not_analyzed', 'include_in_all': False},
            DJANGO_ID: {'type': 'string', 'index': 'not_analyzed', 'include_in_all': False},
        }

        for field_name, field_class in fields.items():
            field_mapping = FIELD_MAPPINGS.get(
                field_class.field_type, self.DEFAULT_FIELD_MAPPING).copy()
            if field_class.boost != 1.0:
                field_mapping['boost'] = field_class.boost

            if field_class.document is True:
                content_field_name = field_class.index_fieldname

            # Do this last to override `text` fields.
            if field_mapping['type'] == 'string':
                if field_class.indexed is False or hasattr(field_class, 'facet_for'):
                    field_mapping['index'] = 'not_analyzed'
                    del field_mapping['analyzer']

            # if field_name in ['llps', 'llps_exact']:
            #     field_mapping['index'] = 'not_analyzed'
            #     field_mapping['analyzer'] = 'german'

            # if field_name in ['text']:
            #     field_mapping['analyzer'] = 'german2'

            mapping[field_class.index_fieldname] = field_mapping

        return (content_field_name, mapping)


    # # <rant>
    # # Uncomment the following to drop to ipdb when there's errors when creating
    # # the index and mappings. This is direly needed because haystack is such a
    # # royal piece of crap. </rant>
    # def setup(self):
    #     """
    #     Defers loading until needed.
    #     """
    #     # Get the existing mapping & cache it. We'll compare it
    #     # during the ``update`` & if it doesn't match, we'll put the new
    #     # mapping.
    #     try:
    #         self.existing_mapping = self.conn.indices.get_mapping(
    #             index=self.index_name)
    #     except NotFoundError:
    #         pass
    #     except Exception:
    #         if not self.silently_fail:
    #             raise

    #     unified_index = haystack.connections[
    #         self.connection_alias].get_unified_index()
    #     self.content_field_name, field_mapping = self.build_schema(
    #         unified_index.all_searchfields())
    #     current_mapping = {
    #         'modelresult': {
    #             'properties': field_mapping,
    #         }
    #     }

    #     if current_mapping != self.existing_mapping:
    #         try:
    #             # Make sure the index is there first.
    #             self.conn.indices.create(
    #                 index=self.index_name, body=self.DEFAULT_SETTINGS)
    #             self.conn.indices.put_mapping(
    #                 index=self.index_name, doc_type='modelresult', body=current_mapping)
    #             self.existing_mapping = current_mapping
    #         except Exception as e:
    #             import ipdb
    #             ipdb.set_trace()

    #     self.setup_complete = True


class FuzzyElasticsearchSearchEngine(BaseEngine):

    """
    Custom ES Engine that allows fuzzy search
    """
    backend = FuzzyElasticsearchSearchBackend
    query = ElasticsearchSearchQuery
