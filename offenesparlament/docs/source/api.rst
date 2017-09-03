API
===

This section describes implementation details for the API.

General & Structure
-------------------

The current implementation provides api access to the scraped data at `http://offenesparlament.at/api <http://offenesparlament.at/api/>`_.

While following general REST guidelines, this is a purely read-only, no-auth API and provides only minimal documentation and support.

Implementation
--------------

The implementation is done via the `Django Rest Framework <http://www.django-rest-framework.org/>`_. The relevant implementation can be found at ``offenesparlament/vies/api.py``.

Three custom base classes have been defined to extend the Django Rest Frameworks ``ReadOnlyModelViewSet`` and ``HyperlinkedModelSerializer`` respectively. The ``ESViewSet`` Class replaces the standard database querysets with ElasticSearch queries to retrieve list data for the two main models 'Person' and 'Law' via ES for performance reasons. The ``PaginatedFilteredViewSet`` class provides a way of returning paginated results and also allowing to filter the result fields based on different serializers for list and detail views. And finally, the ``DynamicFieldsModelSerializer`` class extends the ``HyperlinkedModelSerializer`` to provide hyperlinked urls in the results and also allow per-request filtering of result fields to limit large models in the list view.

All ViewSets and Serializers for the Django models are defined subsequently in the same file. They all take the following form::

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

Where necessary, a separate ListSerializer with different fieldsets or behaviour can be defined::

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

Finally, the internal routing mechanisms of the Django REST framework are defined at the bottom of the ``offenesparlament.views.api`` module by registering each viewset::

    router = routers.DefaultRouter()
    router.register(r'persons', PersonViewSet, base_name="Person")
    router.register(r'laws', LawViewSet, base_name="Law")
    router.register(r'debates', DebateViewSet, base_name="Debate")
    [...]

Caveats
-------

Performance: Currently, no performance improving measures beyond the use of ElasticSearch, where applicable, have been taken. Should the API proe to be too slow or overwhelm the server, request throttling should be employed. The Django REST Framework provides options for this.

Related api_urls for ElasticSearch-based viewsets must currently be index beforehand; deployment of the API thus requires a complete rebuilding of the index.