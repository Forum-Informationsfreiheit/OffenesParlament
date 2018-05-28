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

        hostname = request._request.META['HTTP_HOST']
        https = 'https://' if request._request.is_secure() else 'http://'
        for r in result_list:
            if 'api_url' in r:
                r['api_url'] = "{}{}{}".format(https,hostname,r['api_url'])


        self.paginate_queryset(result_list)
        self.paginator.count = qs.count()
        self.paginator.display_page_controls = True

        return self.get_paginated_response(result_list)

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

        qs = self.queryset

        filters = {k:v for k,v in request.GET.iteritems() if k not in ('limit','offset',)}
        if filters:
            qs = qs.filter(**filters)

        lower = offset
        upper = offset + limit
        if self.list_serializer_class is None:
            self.list_serializer_class = self.serializer_class

        qs = qs[lower:upper]

        serializer = self.list_serializer_class(
            qs,
            many=True,
            context={'request': request})

        result_list = serializer.data

        self.paginate_queryset(result_list)
        self.paginator.count = qs.count()
        self.paginator.display_page_controls = True

        return self.get_paginated_response(result_list)

    def retrieve(self, request, pk=None):
        result = get_object_or_404(self.queryset, pk=pk)
        serializer = self.serializer_class(
            result, context={'request': request})
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

# Auxiliary, non primary models
###
# These aren't loaded through ES since we don't have them indexed there


### MODEL: Category ###

class CategorySerializer(DynamicFieldsModelSerializer):
    """
    The category of a law (and all its sub-forms like pre-laws or inquiries) or
    of an opinion.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Category-detail")

    class Meta:
        model = Category
        fields = ('pk', 'title', 'api_url')


class CategoryViewSet(PaginatedFilteredViewSet):
    """
    The category of a law (and all its sub-forms like pre-laws or inquiries) or
    of an opinion.
    """
    model = Category
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

### MODEL: Keyword ###


class KeywordSerializer(DynamicFieldsModelSerializer):
    """
    Keywords are assigned to laws and opinions.
    """
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Keyword-detail")

    class Meta:
        model = Keyword
        fields = ('pk', 'title', 'api_url')


class KeywordViewSet(PaginatedFilteredViewSet):
    """
    Keywords are assigned to laws and opinions.
    """
    model = Keyword
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer

### MODEL: LegislativePeriod ###


class LegislativePeriodSerializer(DynamicFieldsModelSerializer):
    """
    Legislative periods are needed to identify laws beyond their parl_id
    (which alone isn't unique) and, generally run from election to election.

    LLPs are denoted both with a roman numeral and an arabic one; this is
    inconsistently handled at the official parliament website as well.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:LegislativePeriod-detail")

    class Meta:
        model = LegislativePeriod
        fields = ('pk', 'roman_numeral', 'number',
                  'start_date', 'end_date', 'api_url')


class LegislativePeriodViewSet(PaginatedFilteredViewSet):
    """
    Legislative periods are needed to identify laws beyond their parl_id
    (which alone isn't unique) and, generally run from election to election.

    LLPs are denoted both with a roman numeral and an arabic one; this is
    inconsistently handled at the official parliament website as well.
    """
    model = LegislativePeriod
    queryset = LegislativePeriod.objects.all()
    serializer_class = LegislativePeriodSerializer

### MODEL: Document ###


class DocumentSerializer(DynamicFieldsModelSerializer):
    """
    Documents can be assigned to a number of objects and represent downloadable
    resources., often PDF or Word documents.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Document-detail")

    class Meta:
        model = Document
        fields = ('pk', 'title', 'pdf_link', 'html_link',
                  'stripped_html', 'api_url')


class DocumentViewSet(PaginatedFilteredViewSet):
    """
    Documents can be assigned to a number of objects and represent downloadable
    resources., often PDF or Word documents.
    """

    model = Document
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer

### MODEL: Function ###


class FunctionSerializer(DynamicFieldsModelSerializer):
    """
    A function represents the generic position that a mandate can fill.

    Functions, like "Abgeordnete(r) zum Bundesrat" or "Vorsitzende" are not
    assigned per se to people, but must be encapsulated within a mandate (with
    a start- and end-date).
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Function-detail")

    class Meta:
        model = Function
        fields = ('pk', 'title', 'short', 'api_url')


class FunctionViewSet(PaginatedFilteredViewSet):
    """
    A function represents the generic position that a mandate can fill.

    Functions, like "Abgeordnete(r) zum Bundesrat" or "Vorsitzende" are not
    assigned per se to people, but must be encapsulated within a mandate (with
    a start- and end-date).
    """
    model = Function
    queryset = Function.objects.all()
    serializer_class = FunctionSerializer

### MODEL: Party ###


class PartySerializer(DynamicFieldsModelSerializer):
    """
    A political party. While the titles of a single party might have changed
    over time (which is reflected in the array of titles collected for that
    party), the short form stays unique.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Party-detail")

    class Meta:
        model = Party
        fields = ('pk', 'short', 'titles', 'api_url')


class PartyViewSet(PaginatedFilteredViewSet):
    """
    A political party. While the titles of a single party might have changed
    over time (which is reflected in the array of titles collected for that
    party), the short form stays unique.
    """
    model = Party
    queryset = Party.objects.all()
    serializer_class = PartySerializer

### MODEL: State ###


class StateSerializer(DynamicFieldsModelSerializer):
    """
    An electoral district or state an official can be elected in. Due to
    inconsistencies on the official parliament webpage, titles of legislative
    periods show up in this list as well.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:State-detail")

    class Meta:
        model = State
        fields = ('pk', 'name', 'title', 'api_url')


class StateViewSet(PaginatedFilteredViewSet):
    """
    An electoral district or state an official can be elected in. Due to
    inconsistencies on the official parliament webpage, titles of legislative
    periods show up in this list as well.
    """
    model = State
    queryset = State.objects.all()
    serializer_class = StateSerializer


### MODEL: Administration ###

class AdministrationSerializer(DynamicFieldsModelSerializer):
    """
    An administration in the Austrian government, usually runs from
    election to election. This is necesary for those Persons that aren't
    elected officials, but rather put in their office by the winning parties
    after elections.
    """

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Administration-detail")

    class Meta:
        model = Administration
        fields = ('pk', 'title', 'start_date', 'end_date', 'api_url')


class AdministrationViewSet(PaginatedFilteredViewSet):
    """
    An administration in the Austrian government, usually runs from
    election to election. This is necesary for those Persons that aren't
    elected officials, but rather put in their office by the winning parties
    after elections.
    """
    model = Administration
    queryset = Administration.objects.all()
    serializer_class = AdministrationSerializer

### MODEL: DebateStatement ###


class DebatePersonSerializer(DynamicFieldsModelSerializer):
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Person-detail")

    class Meta:
        model = Person
        fields = ('pk','parl_id','full_name','api_url',)

class DebateStatementSerializer(DynamicFieldsModelSerializer):
    """
    A debate statement is part of a debate should usually contain speech by
    only one speaker.
    """

    debate_id = serializers.IntegerField(read_only=True)
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:DebateStatement-detail")
    person = DebatePersonSerializer()

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
            'debate_id',
            'api_url',
            'person',
        )


class DebateStatementViewSet(PaginatedFilteredViewSet):
    """
    A debate statement is part of a debate should usually contain speech by
    only one speaker.
    """
    model = DebateStatement
    queryset = DebateStatement.objects.all()
    serializer_class = DebateStatementSerializer


### MODEL: Debate ###

class DebateSerializer(DynamicFieldsModelSerializer):
    """
    A parliamentary debate (either in the Nationalrat or the Bundesrat).

    It is comprised of debate statements (shown only in the debate detail view
    for brevity and performance reasons).
    """

    llp = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    debate_statements = DebateStatementSerializer(required=False, many=True)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Debate-detail")

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
            'api_url'
        )


class DebateListSerializer(DynamicFieldsModelSerializer):
    """
    A parliamentary debate (either in the Nationalrat or the Bundesrat).

    It is comprised of debate statements (shown only in the debate detail view
    for brevity and performance reasons).
    """
    llp = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Debate-detail")

    class Meta:
        model = Debate
        fields = (
            'pk',
            'api_url',
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
    A parliamentary debate (either in the Nationalrat or the Bundesrat).

    It is comprised of debate statements (shown only in the debate detail view
    for brevity and performance reasons).
    """
    model = Debate
    queryset = Debate.objects.all()
    serializer_class = DebateSerializer
    list_serializer_class = DebateListSerializer


### MODEL: Mandate ###

class MandateSerializer(DynamicFieldsModelSerializer):
    """
    A mandate is a persons function, delimited with a start- and end-date.

    It can either retain it's start- and end-time from itself or the
    legislative period it is granted for.

    For mandates acquired through election, the state can be defined.
    For mandates granted by an administration, that administration is
    defined.
    """
    function = FunctionSerializer()
    party = PartySerializer(fields=('pk', 'short'))
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    state = StateSerializer()
    administration = AdministrationSerializer()

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Mandate-detail")

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
            'administration',
            'api_url'
        )


class MandateViewSet(PaginatedFilteredViewSet):
    """
    A mandate is a persons function, delimited with a start- and end-date.

    It can either retain it's start- and end-time from itself or the
    legislative period it is granted for.

    For mandates acquired through election, the state can be defined.
    For mandates granted by an administration, that administration is
    defined.
    """
    model = Mandate
    queryset = Mandate.objects.all()
    serializer_class = MandateSerializer

### MODEL: Phase ###

class PhaseSerializer(DynamicFieldsModelSerializer):
    """
    Phases group law steps.

    A Phase defines a series of steps that belong to the same process,
    for instance a law being brought to, discussed, and passed through a
    comittee.
    """
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Phase-detail")

    class Meta:
        model = Phase
        fields = (
            'pk',
            'title',
            'api_url'
        )

class PhaseViewSet(PaginatedFilteredViewSet):
    """
    Phases group law steps.

    A Phase defines a series of steps that belong to the same process,
    for instance a law being brought to, discussed, and passed through a
    comittee.
    """

    model = Phase
    queryset = Phase.objects.all()
    serializer_class = PhaseSerializer


### MODEL: Step ###

class StepSerializer(DynamicFieldsModelSerializer):
    """
    Laws undergo steps as they move through the legislative process.
    Each step is part of one phase.
    """
    phase = PhaseSerializer(required=False)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Step-detail")

    class Meta:
        model = Step
        fields = (
            'pk',
            'title',
            'date',
            'sortkey',
            'protocol_url',
            'source_link',
            'phase',
            'api_url'
        )


class StepViewSet(PaginatedFilteredViewSet):
    """
    Laws undergo steps as they move through the legislative process.
    Each step is part of one phase.
    """
    model = Step
    queryset = Step.objects.all()
    serializer_class = StepSerializer


### MODEL: Entity ###

class EntitySerializer(DynamicFieldsModelSerializer):
    """
    Entities are external actors (persons or organisations) that aren't part
    of the normal parliamentary process. They come into play when
    the general public is being asked to give an opinion on a proposed
    law ('Begutachtungsverfahren').

    Given the shoddy implementation of how these entities are described on
    the official parliament website, these data need to be taken with a grain
    of salt and most likely contain errors or incomplete data.
    """
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Entity-detail")

    class Meta:
        model = Entity
        fields = (
            'pk',
            'title',
            'title_detail',
            'email',
            'phone',
            'api_url')

class EntityViewSet(PaginatedFilteredViewSet):
    """
    Entities are external actors (persons or organisations) that aren't part
    of the normal parliamentary process. They come into play when
    the general public is being asked to give an opinion on a proposed
    law ('Begutachtungsverfahren').

    Given the shoddy implementation of how these entities are described on
    the official parliament website, these data need to be taken with a grain
    of salt and most likely contain errors or incomplete data.
    """
    model = Entity
    queryset = Entity.objects.all()
    serializer_class = EntitySerializer


### MODEL: Opinion ###

class OpinionSerializer(DynamicFieldsModelSerializer):
    """
    Opinions are being given by entities as part of the "Begutachtungsverfahren"
    for proposed laws.

    Among other things, they can be assigned documents, keywords and a category
    and must always refer to the entity that gave the opinion.
    """
    documents = DocumentSerializer(required=False, many=True)
    category = CategorySerializer(required=False)
    keywords = KeywordSerializer(required=False, many=True)
    entity = EntitySerializer()

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Opinion-detail")

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
            'api_url'
        )


class OpinionViewSet(PaginatedFilteredViewSet):
    """
    Opinions are being given by entities as part of the "Begutachtungsverfahren"
    for proposed laws.

    Among other things, they can be assigned documents, keywords and a category
    and must always refer to the entity that gave the opinion.
    """
    model = Opinion
    queryset = Opinion.objects.all()
    serializer_class = OpinionSerializer

# Primary Models Person, Law and Debaite
###
# ViewSet loads the result content through ES instead of through the DjangoDB

### MODEL: Keyword ###


class LawSerializer(DynamicFieldsModelSerializer):
    """
    Laws represent any matter of legislation or discussion in the Nationalrat or
    Bundesrat ("Verhandlungssache"). There are multiple sub-types of laws
    (such as inquiries), which can be determined through a laws category.
    """
    category = CategorySerializer(required=False)
    keywords = KeywordSerializer(required=False, many=True)
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    documents = DocumentSerializer(required=False, many=True)
    references_id = serializers.IntegerField(read_only=True)
    slug = serializers.CharField(read_only=True)
    steps = StepSerializer(required=False, many=True)
    opinions = OpinionSerializer(required=False, many=True)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Law-detail")

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
            'api_url'
        )


class LawViewSet(ESViewSet):
    """
    Laws represent any matter of legislation or discussion in the Nationalrat or
    Bundesrat ("Verhandlungssache"). There are multiple sub-types of laws
    (such as inquiries), which can be determined through a laws category.
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
        'internal_link',
        'api_url')

### MODEL: Person ###

class PersonSerializer(DynamicFieldsModelSerializer):
    """
    A person can either be holding mandate(s) for the Nationalrat or the
    Bundesrat, or be an appointed official for an administration.
    """

    mandate_set = MandateSerializer(
        many=True
        #,fields=('pk',)
    )
    latest_mandate = MandateSerializer()
    debate_statements = DebateStatementSerializer(many=True)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Person-detail")

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
            'mandate_set',
            'latest_mandate',
            'debate_statements',
            'api_url'
        )


class PersonViewSet(ESViewSet):
    """
    A person can either be holding mandate(s) for the Nationalrat or the
    Bundesrat, or be an appointed official for an administration.
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
        'llps_numeric',
        'api_url')


### MODEL: ComiteeMeeting ###

class ComitteeMeetingSerializer(DynamicFieldsModelSerializer):
    """
    Comitee meetings ('Sitzung') happen on a given date and follow an agenda.
    """
    comittee_id = serializers.IntegerField(read_only=True)
    agenda = DocumentSerializer()

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:ComitteeMeeting-detail")

    class Meta:
        model = ComitteeMeeting
        fields = (
            'pk',
            'number',
            'date',
            'comittee_id',
            'agenda',
            'api_url'
        )


class ComitteeMeetingViewSet(PaginatedFilteredViewSet):
    """
    Comitee meetings ('Sitzung') happen on a given date and follow an agenda.
    """
    model = ComitteeMeeting
    queryset = ComitteeMeeting.objects.all()
    serializer_class = ComitteeMeetingSerializer

### MODEL: Keyword ###


class ComitteeMembershipSerializer(DynamicFieldsModelSerializer):
    """
    A comittee membership declares which Persons hold positions within the
    referenced comittee.
    """
    comittee_id = serializers.IntegerField(read_only=True)
    function = FunctionSerializer()
    person = PersonSerializer(fields=('pk', 'parl_id', 'full_name'))

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:ComitteeMembership-detail")

    class Meta:
        model = ComitteeMembership
        fields = (
            'pk',
            'date_from',
            'date_to',
            'comittee_id',
            'person',
            'function',
            'api_url'
        )


class ComitteeMembershipViewSet(PaginatedFilteredViewSet):
    """
    A comittee membership declares which Persons hold positions within the
    referenced comittee.
    """
    model = ComitteeMembership
    queryset = ComitteeMembership.objects.all()
    serializer_class = ComitteeMembershipSerializer


### MODEL: Comitee ###

class ComitteeSerializer(DynamicFieldsModelSerializer):
    """
    A parliamentary comittee, usually with a limited area of responsibility.

    Has a list of members and meetings with agendas.
    """
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    laws = LawSerializer(many=True, fields=('pk', 'parl_id', 'title'))
    parent_comittee_id = serializers.IntegerField(read_only=True)
    comittee_meetings = ComitteeMeetingSerializer(many=True)
    comittee_members = ComitteeMembershipSerializer(many=True)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Comittee-detail")

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
            'comittee_members',
            'api_url'
        )


class ComitteeListSerializer(DynamicFieldsModelSerializer):
    """
    A parliamentary comittee, usually with a limited area of responsibility.

    Has a list of members and meetings with agendas.
    """
    legislative_period = LegislativePeriodSerializer(
        required=True, fields=('pk', 'roman_numeral', 'number'))
    laws = LawSerializer(many=True, fields=('pk', 'parl_id', 'title'))
    parent_comittee_id = serializers.IntegerField(read_only=True)

    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:Comittee-detail")

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
            'api_url'
        )


class ComitteeViewSet(PaginatedFilteredViewSet):
    """
    A parliamentary comittee, usually with a limited area of responsibility.

    Has a list of members and meetings with agendas.
    """
    queryset = Comittee.objects.all()
    serializer_class = ComitteeSerializer
    list_serializer_class = ComitteeListSerializer

### MODEL: Keyword ###


class ComitteeAgendaTopicSerializer(DynamicFieldsModelSerializer):
    """
    Agenda topics define the talking points ('Tagesordnung') for a given
    comittee meeting.
    """
    meeting = ComitteeMeetingSerializer(required=True)
    law = LawSerializer(fields=('pk', 'parl_id', 'title'))
    api_url = serializers.HyperlinkedIdentityField(
        view_name="op_api:ComitteeAgendaTopic-detail")

    class Meta:
        model = ComitteeAgendaTopic
        fields = (
            'pk',
            'number',
            'text',
            'comment',
            'meeting',
            'law',
            'api_url'
        )


class ComitteeAgendaTopicViewSet(PaginatedFilteredViewSet):
    """
    Agenda topics define the 'Tagesordnung' for a given comittee meeting.
    """

    model = ComitteeAgendaTopic
    queryset = ComitteeAgendaTopic.objects.all()
    serializer_class = ComitteeAgendaTopicSerializer


# Routing definition for API viewsets
###
# Routers provide an easy way of automatically determining the URL conf.

class OffenesparlamentAPI(routers.APIRootView):
    """
    The OffenesParlament (read-only) API exposes the following endpoints. Click through to them to discover details on how they work.
    """
    pass

class MyDefaultRouter(routers.DefaultRouter):
     APIRootView = OffenesparlamentAPI

router = MyDefaultRouter()
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
router.register(r'state', StateViewSet, base_name="State")
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
