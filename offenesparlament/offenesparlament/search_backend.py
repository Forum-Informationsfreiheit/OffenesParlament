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
        'analyzer': 'german2'}

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

            mapping[field_class.index_fieldname] = field_mapping

        return (content_field_name, mapping)


class FuzzyElasticsearchSearchEngine(BaseEngine):

    """
    Custom ES Engine that allows fuzzy search
    """
    backend = FuzzyElasticsearchSearchBackend
    query = ElasticsearchSearchQuery
