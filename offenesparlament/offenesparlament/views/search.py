import datetime
import json
from haystack.generic_views import SearchView
from django.http import HttpResponse

from haystack.query import SearchQuerySet

from op_scraper.models import Person, Law

class QuerySetEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
            return obj.isoformat()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class JsonSearchView(SearchView):

    """Base SearchView that returns json-data"""

    search_model = None
    facet_fields = ['party']

    def __init__(self, search_model=None):
        super(JsonSearchView, self).__init__()
        if search_model:
            self.search_model = search_model

    def extract_query_args(self, request):
        """
        Extract the query arguments from request.GET
        """
        query_args = {
            'facet_filters': {}
        }
        # Do we have a query or are we just getting all of them?
        if 'q' in request.GET and request.GET['q']:
            query_args['q'] = request.GET['q']

        if 'only_facets' in request.GET:
            query_args['only_facets'] = True

        for facet_field in self.facet_fields:
            if facet_field in request.GET and request.GET[facet_field]:
                query_args['facet_filters'][
                    facet_field] = request.GET[facet_field]

        return query_args

    def get(self, request, *args, **kwargs):

        query_args = self.extract_query_args(request)
        (result, facet_counts) = self.get_queryset(query_args)

        # combine results and facets
        result_list = [sr.get_stored_fields() for sr in result]
        result = {
            'result': result_list,
            'facets': facet_counts
        }

        json_result = json.dumps(result, cls=QuerySetEncoder)

        return HttpResponse(json_result, content_type='application/json')

    def get_queryset(self, query_args):
        # Create new queryset
        qs = SearchQuerySet()

        # Are we searching all models or just a specific one (depends on
        # parameter set in View instantiation)
        if self.search_model is not None:
            qs = qs.models(self.search_model)

        # Do we have a query or are we just getting all of them?
        if 'q' in query_args:
            qs = qs.auto_query(query_args['q'])

        # Filter by facets
        if query_args['facet_filters']:
            for facet_field in query_args['facet_filters'].keys():
                # We use narrow to limit the index entries beforehand, but
                # need to use filter afterwards to remove partly correct results
                # For instance, searching for Steyr (Oberoesterreich) yielded
                # everyone from Oberoesterreich until filtering by it again.
                qs = qs.narrow(u"{}:{}".format(
                    facet_field,
                    query_args['facet_filters'][facet_field])
                ).filter(
                    **{
                    facet_field: query_args['facet_filters'][facet_field]}
                )

        # Retrieve facets and facet_counts
        facet_counts = []
        if self.facet_fields:
            facets = qs
            for facet_field in self.facet_fields:
                facets = facets.facet(facet_field)
            facet_counts = facets.facet_counts()

        # Get results and return them
        if 'only_facets' in query_args:
            result = {}
        else:
            result = qs.all()

        return (result, facet_counts)

    def get_context_data(self, *args, **kwargs):
        context = super(JsonSearchView, self).get_context_data(*args, **kwargs)
        # do something
        return context


class PersonSearchView(JsonSearchView):

    """Search view for the Person model"""

    search_model = Person
    facet_fields = [
        'party',
        'birthplace',
        'deathplace',
        'occupation',
        'llps']


class LawSearchView(JsonSearchView):

    """Search view for the Law model"""

    search_model = Law
    facet_fields = [
        'llp',
        'category',
        'keywords'
    ]
