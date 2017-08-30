# -*- coding: UTF-8 -*-
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

class PaginatedFilteredViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = None
    list_serializer_class = None

    def list(self, request):
        limit = int(request.GET['limit']) if 'limit' in request.GET else 100
        offset = int(request.GET['offset']) if 'offset' in request.GET else 0

        lower = offset
        upper = offset + limit
        if self.list_serializer_class is None:
            self.list_serializer_class = self.serializer_class

        serializer = self.list_serializer_class(
            self.queryset[lower:upper],
            many=True,
            context={'request': request})

        result_list = serializer.data

        self.paginate_queryset(result_list)
        self.paginator.count = self.queryset.count()
        self.paginator.display_page_controls = True

        return self.get_paginated_response(result_list)

    def retrieve(self, request, pk=None):
        result = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(result)
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

class CategoryViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all categories.
    """
    model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class KeywordSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Keyword
        fields = ('pk', 'title')

class KeywordViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all keywords.
    """
    model = Keyword
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class LegislativePeriodSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = LegislativePeriod
        fields = ('pk', 'roman_numeral', 'number', 'start_date', 'end_date')


class LegislativePeriodViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all legislative periods.

    Phases group law steps.
    """
    model = LegislativePeriod
    queryset = LegislativePeriod.objects.all()
    serializer_class = LegislativePeriodSerializer


class DocumentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Document
        fields = ('pk', 'title', 'pdf_link', 'html_link', 'stripped_html')


class DocumentViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all documents.
    """
    model = Document
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer


class FunctionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Function
        fields = ('pk', 'title', 'short')


class FunctionViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all political functions that persons can have in the form
    of mandates.
    """
    model = Function
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer


class PartySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Party
        fields = ('pk', 'short', 'titles')


class PartyViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all parties, including their different names at different
    times.
    """
    model = Party
    queryset = Party.objects.all()
    serializer_class = PartySerializer


class StateSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = State
        fields = ('pk', 'name', 'title')


class StateViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all states or electoral districts
    """
    model = State
    queryset = State.objects.all()
    serializer_class = StateSerializer


class AdministrationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Administration
        fields = ('pk', 'title', 'start_date', 'end_date')


class AdministrationViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all administrations since the second republic.
    """
    model = Administration
    queryset = Administration.objects.all()
    serializer_class = AdministrationSerializer

class DebateStatementSerializer(DynamicFieldsModelSerializer):
    debate_id = serializers.IntegerField(read_only=True)
    class Meta:
        model = DebateStatement
        fields = (
            'pk',
            'date',
            'date_end',
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
            'debate_id'
        )


class DebateStatementViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all debate statements.
    """
    model = DebateStatement
    queryset = DebateStatement.objects.all()
    serializer_class = DebateStatementSerializer

class DebateSerializer(DynamicFieldsModelSerializer):
    llp = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    debate_statements = DebateStatementSerializer(required=False, many=True)

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
            'llp',
            'debate_statements',
        )

class DebateListSerializer(DynamicFieldsModelSerializer):
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
            'llp',
        )

class DebateViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all debates, with their debate statements, where existing.
    """
    model = Debate
    queryset = Debate.objects.all()
    serializer_class = DebateSerializer
    list_serializer_class = DebateListSerializer

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


class MandateViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all mandates.

    A mandate is a persons function, delimited with a start- and end-date.
    """
    model = Mandate
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer
    pagination_class = LargeResultsSetPagination

class PhaseSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Phase
        fields = (
            'pk',
            'title'
        )

class PhaseViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all phases.

    Phases group law steps.
    """
    model = Phase
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer

class StepSerializer(DynamicFieldsModelSerializer):

    phase = PhaseSerializer(required=False)

    class Meta:
        model = Step
        fields = (
            'pk',
            'title',
            'date',
            'sortkey',
            'protocol_url',
            'source_link',
            'phase'
        )


class StepViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all steps.

    Laws undergo steps as they move through the legislative process.
    Each step is part of one phase.
    """
    model = Step
    queryset = Step.objects.all()
    serializer_class = StepSerializer

class EntitySerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = Entity
        fields = (
            'pk',
            'title',
            'title_detail',
            'email',
            'phone')


class EntityViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all entities.

    An entity is a person or organisation that has at some point given an
    opinion (Stellungnahme) about a propsed law.
    """
    model = Entity
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer

class OpinionSerializer(DynamicFieldsModelSerializer):

    documents = DocumentSerializer(required=False, many=True)
    category = CategorySerializer(required=False)
    keywords = KeywordSerializer(required=False, many=True)
    entity = EntitySerializer()

    class Meta:
        model = Opinion
        fields = (
            'pk',
            'parl_id',
            'date',
            'description',
            'source_link',
            'documents',
            'category',
            'keywords',
            'entity',
        )

class OpinionViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all opinions ('Stellungnahmen') for Pre-Laws (Ministerialentwürfe, etc.)
    """
    model = Opinion
    queryset = Opinion.objects.all()
    serializer_class = OpinionSerializer

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
    steps = StepSerializer(required=False, many=True)
    opinions = OpinionSerializer(required=False, many=True)

    class Meta:
        model = Law
        fields = (
            'pk',
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
            'slug',
            'steps',
            'opinions',
        )


class LawViewSet(ESViewSet):
    """
    Return a list of all laws.
    """
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
    Return a list of all persons.
    """
    model = Person
    queryset = Person.objects.all()
    serializer = PersonSerializer
    fields = (
        'parl_id',
        'full_name',
        'birthdate',
        'birthplace',
        'occupation',
        'ts',
        'deathdate',
        'deathplace',
        'party',
        'llps',
        'llps_numeric')


class ComitteeMeetingSerializer(DynamicFieldsModelSerializer):

    comittee_id = serializers.IntegerField(read_only=True)
    agenda = DocumentSerializer()

    class Meta:
        model = ComitteeMeeting
        fields = (
            'pk',
            'number',
            'date',
            'comittee_id',
            'agenda',
        )

class ComitteeMeetingViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all comittee meetings + their agendas
    """
    model = ComitteeMeeting
    queryset = ComitteeMeeting.objects.all()
    serializer_class = ComitteeMeetingSerializer

class ComitteeMembershipSerializer(DynamicFieldsModelSerializer):

    comittee_id = serializers.IntegerField(read_only=True)
    function = FunctionSerializer()
    person = PersonSerializer(fields=('pk', 'parl_id', 'full_name'))

    class Meta:
        model = ComitteeMembership
        fields = (
            'pk',
            'date_from',
            'date_to',
            'comittee_id',
            'person',
            'function',
        )

class ComitteeMembershipViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all comittee meetings + their agendas
    """
    model = ComitteeMembership
    queryset = ComitteeMembership.objects.all()
    serializer_class = ComitteeMembershipSerializer


class ComitteeSerializer(DynamicFieldsModelSerializer):

    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    laws = LawSerializer(many=True, fields=('pk', 'parl_id', 'title'))
    parent_comittee_id = serializers.IntegerField(read_only=True)
    comittee_meetings = ComitteeMeetingSerializer(many=True)
    comittee_members = ComitteeMembershipSerializer(many=True)

    class Meta:
        model = Comittee
        fields = (
            'pk',
            'parl_id',
            'name',
            'source_link',
            'nrbr',
            'description',
            'active',
            'legislative_period',
            'laws',
            'parent_comittee_id',
            'comittee_meetings',
            'comittee_members'
        )

class ComitteeListSerializer(DynamicFieldsModelSerializer):

    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    laws = LawSerializer(many=True, fields=('pk', 'parl_id', 'title'))
    parent_comittee_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comittee
        fields = (
            'pk',
            'parl_id',
            'name',
            'source_link',
            'nrbr',
            'description',
            'active',
            'legislative_period',
            'laws',
            'parent_comittee_id',
        )



class ComitteeViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all comittees
    """
    queryset = Comittee.objects.all()
    serializer_class = ComitteeSerializer
    list_serializer_class = ComitteeListSerializer

class ComitteeAgendaTopicSerializer(DynamicFieldsModelSerializer):

    meeting = ComitteeMeetingSerializer(required=True)
    law = LawSerializer(fields=('pk', 'parl_id', 'title'))
    class Meta:
        model = ComitteeAgendaTopic
        fields = (
            'pk',
            'number',
            'text',
            'comment',
            'meeting',
            'law'
        )

class ComitteeAgendaTopicViewSet(PaginatedFilteredViewSet):
    """
    Return a list of all comittee meetings + their agendas
    """
    model = ComitteeAgendaTopic
    queryset = ComitteeAgendaTopic.objects.all()
    serializer_class = ComitteeAgendaTopicSerializer



# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'persons', PersonViewSet, base_name="Person")
router.register(r'laws', LawViewSet, base_name="Law")
router.register(r'debates', DebateViewSet, base_name="Debate")

router.register(r'categories', CategoryViewSet, base_name="Category")
router.register(r'keywords', KeywordViewSet, base_name="Keyword")
router.register(r'phases', PhaseViewSet, base_name="Phase")
router.register(r'steps', StepViewSet, base_name="Step")
router.register(r'entities', EntityViewSet, base_name="Entity")
router.register(r'opinions', OpinionViewSet, base_name="Opinion")
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
router.register(r'comittees', ComitteeViewSet,
                base_name="Comittee")
router.register(r'comittee_meetings', ComitteeMeetingViewSet,
                base_name="ComitteeMeeting")
router.register(r'comittee_agenda_topic', ComitteeAgendaTopicViewSet,
                base_name="ComitteeAgendaTopic")
router.register(r'comittee_membership', ComitteeMembershipViewSet,
                base_name="ComitteeMembership")


