from django.conf.urls import url, include
from django.shortcuts import get_object_or_404
from op_scraper.models import *
from rest_framework import routers, serializers, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

##################
#  Base Classes  #
##################


class LargeResultsSetPagination(LimitOffsetPagination):
    default_limit = 100
    max_limit = 200


class ESViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    model = None
    serializer = None
    pagination_class = LargeResultsSetPagination

    def list(self, request):
        limit = int(request.GET['limit']) if 'limit' in request.GET else 100
        offset = int(request.GET['offset']) if 'offset' in request.GET else 0

        lower = offset
        upper = offset + limit

        from haystack.query import SearchQuerySet

        # Create new queryset
        qs = SearchQuerySet()
        qs = qs.models(self.model)
        result_list = []

        for sr in qs.values(*self.fields)[lower:upper]:
            result_list.append(sr)

        self.paginate_queryset(result_list)
        self.paginator.count = qs.count()
        self.paginator.display_page_controls = True

        return self.get_paginated_response(result_list)

        # return Response(result_list)

    def retrieve(self, request, pk=None):
        queryset = self.model.objects.all()
        obj = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer(obj, context={'request': request})
        return Response(serializer.data)


class DynamicFieldsModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Don't pass the 'fields' arg up to the superclass
        fields = kwargs.pop('fields', None)

        # Instantiate the superclass normally
        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument.
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

####################################
#  Model Serializers and Viewsets  #
####################################

### Auxiliary, non primary models
###
### These aren't loaded through ES since we don't have them indexed there


class CategorySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Category
        fields = ('pk', 'title')


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class KeywordSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Keyword
        fields = ('pk', 'title')


class KeywordViewSet(viewsets.ReadOnlyModelViewSet):
    model = Keyword
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class LegislativePeriodSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LegislativePeriod
        fields = ('pk', 'roman_numeral', 'number', 'start_date', 'end_date')


class LegislativePeriodViewSet(viewsets.ReadOnlyModelViewSet):
    model = LegislativePeriod
    queryset = LegislativePeriod.objects.all()
    serializer_class = LegislativePeriodSerializer


class DocumentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Document
        fields = ('pk', 'title', 'pdf_link', 'html_link', 'stripped_html')


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    model = Document
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class FunctionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Function
        fields = ('pk', 'title', 'short')


class FunctionViewSet(viewsets.ReadOnlyModelViewSet):
    model = Function
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer


class PartySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Party
        fields = ('pk', 'short', 'titles')


class PartyViewSet(viewsets.ReadOnlyModelViewSet):
    model = Party
    queryset = Party.objects.all()
    serializer_class = PartySerializer


class StateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = State
        fields = ('pk', 'name', 'title')


class StateViewSet(viewsets.ReadOnlyModelViewSet):
    model = State
    queryset = State.objects.all()
    serializer_class = StateSerializer


class AdministrationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Administration
        fields = ('pk', 'title', 'start_date', 'end_date')


class AdministrationViewSet(viewsets.ReadOnlyModelViewSet):
    model = Administration
    queryset = Administration.objects.all()
    serializer_class = AdministrationSerializer


class DebateSerializer(DynamicFieldsModelSerializer):
    llp = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))

    class Meta:
        model = Debate
        fields = (
            'pk',
            'date',
            'title',
            'debate_type',
            'protocol_url',
            'detail_url',
            'nr',
            'llp'
        )


class DebateViewSet(viewsets.ReadOnlyModelViewSet):
    model = Debate
    queryset = Debate.objects.all()
    serializer_class = DebateSerializer


class DebateStatementSerializer(DynamicFieldsModelSerializer):
    debate = DebateSerializer()

    class Meta:
        model = DebateStatement
        fields = (
            'pk',
            'date',
            'date_end',
            'debate',
            'index',
            'doc_section',
            'text_type',
            'speaker_role',
            'page_start',
            'page_end',
            'time_start',
            'time_end',
            'full_text',
            'raw_text',
            'annotated_text',
            'speaker_name',
        )


class DebateStatementViewSet(viewsets.ReadOnlyModelViewSet):
    model = DebateStatement
    queryset = DebateStatement.objects.all()
    serializer_class = DebateStatementSerializer


class MandateSerializer(DynamicFieldsModelSerializer):
    function = FunctionSerializer()
    party = PartySerializer(fields=('pk', 'short'))
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    state = StateSerializer()
    administration = AdministrationSerializer()

    class Meta:
        model = Mandate
        fields = (
            'pk',
            'function',
            'start_date',
            'end_date',
            'party',
            'legislative_period',
            'state',
            'administration'
        )


class MandateViewSet(viewsets.ReadOnlyModelViewSet):
    model = Mandate
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer
    pagination_class = LargeResultsSetPagination


### Primary Models Person, Law and Debaite
###
### ViewSet loads the result content through ES instead of through the DjangoDB

class LawSerializer(DynamicFieldsModelSerializer):
    category = CategorySerializer(required=False)
    keywords = KeywordSerializer(required=False, many=True)
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    documents = DocumentSerializer(required=False, many=True)
    references_id = serializers.IntegerField(read_only=True)
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Law
        fields = (
            'title',
            'status',
            'source_link',
            'parl_id',
            'description',
            'category',
            'keywords',
            'legislative_period',
            'documents',
            'references_id',
            'slug'
        )


class LawViewSet(ESViewSet):
    model = Law
    queryset = Law.objects.all()
    serializer = LawSerializer
    fields = (
        'title',
        'status',
        'source_link',
        'parl_id',
        'pk',
        'llps',
        'llps_numeric',
        'keywords',
        'category',
        'ts',
        'internal_link')


class PersonSerializer(DynamicFieldsModelSerializer):
    """
    Serializer class for Person object.
    """

    mandates = MandateSerializer(
        many=True
        #,fields=('pk',)
    )
    latest_mandate = MandateSerializer()
    debate_statements = DebateStatementSerializer(many=True)

    class Meta:
        model = Person
        fields = (
            'parl_id',
            'source_link',
            'photo_link',
            'photo_copyright',
            'full_name',
            'reversed_name',
            'birthdate',
            'birthplace',
            'deathdate',
            'deathplace',
            'occupation',
            '_slug',
            'mandates',
            'latest_mandate',
            'debate_statements'
        )


class PersonViewSet(ESViewSet):
    """

    """
    model = Person
    queryset = Person.objects.all()
    serializer = PersonSerializer
    fields = (
        'parl_id',
        'full_name',
        'birthdate',
        'birthplace',
        'occupation'
        'ts',
        'deathdate',
        'deathplace',
        'party',
        'llps',
        'llps_numeric')


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet, base_name="Person")
router.register(r'laws', LawViewSet, base_name="Law")
router.register(r'debates', DebateViewSet, base_name="Debate")

router.register(r'categories', CategoryViewSet, base_name="Category")
router.register(r'keywords', KeywordViewSet, base_name="Keyword")
router.register(r'documents', DocumentViewSet, base_name="Document")
router.register(r'functions', FunctionViewSet, base_name="Function")
router.register(r'mandates', MandateViewSet, base_name="Mandate")
router.register(r'parties', PartyViewSet, base_name="Party")
router.register(r'state', PartyViewSet, base_name="State")
router.register(r'administration', AdministrationViewSet,
                base_name="Administration")
router.register(r'legislative_periods', LegislativePeriodViewSet,
                base_name="LegislativePeriod")
router.register(r'debate_statements', DebateStatementViewSet,
                base_name="DebateStatement")
