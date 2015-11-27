from haystack.backends.elasticsearch_backend import ElasticsearchSearchBackend
from haystack.backends.elasticsearch_backend import ElasticsearchSearchQuery
from haystack.backends import BaseEngine


class FuzzyElasticsearchSearchBackend(ElasticsearchSearchBackend):

    """
    Custom ES Backend that fuzzyfies the Haystack default query_string queries
    """

    def build_search_kwargs(self, query_string, **kwargs):
        fuzzy = kwargs.pop('fuzzy', True)
        fuzzy_field = kwargs.pop('min_similarity', '')
        search_kwargs = super(FuzzyElasticsearchSearchBackend, self).build_search_kwargs(
            query_string, **kwargs)
        if fuzzy and 'query_string' in search_kwargs['query']['filtered']['query']:
            try:
                # fuzzyfy query strings
                query_string = search_kwargs['query'][
                    'filtered']['query']['query_string']['query']
                query_string = u'({}~)'.format(
                    query_string[1:-1].replace(' ', '~ '))
                search_kwargs['query']['filtered']['query'][
                    'query_string']['query'] = query_string
            except:
                # something went wrong, maybe we don't have a query_string
                # query after all?
                pass
        return search_kwargs


class FuzzyElasticsearchSearchEngine(BaseEngine):

    """
    Custom ES Engine that allows fuzzy search
    """
    backend = FuzzyElasticsearchSearchBackend
    query = ElasticsearchSearchQuery
