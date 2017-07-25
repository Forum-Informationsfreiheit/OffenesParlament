from django.conf.urls import url, include
from django.shortcuts import get_object_or_404
from op_scraper.models import *
from rest_framework import routers, serializers, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response



# ViewSets define the view behavior.
class ESViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for listing or retrieving users.
    """
    model = None
    serializer = None
    def list(self, request):
        limit = int(request.GET['limit']) if 'limit' in request.GET else 100
        offset = int(request.GET['offset']) if 'offset' in request.GET else 0
        lower = offset
        upper = offset+limit

        from haystack.query import SearchQuerySet
        # Create new queryset
        qs = SearchQuerySet()
        qs = qs.models(self.model)
        result_list = []
        for sr in qs.values(*self.fields)[lower:upper]:
            result_list.append(sr)

        return Response(result_list)

    def retrieve(self, request, pk=None):
        queryset = self.model.objects.all()
        obj = get_object_or_404(queryset, pk=pk)
        serializer = self.serializer(obj, context={'request': request})
        return Response(serializer.data)



# Serializers define the API representation.
class CategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Category
        fields = ('pk', 'title')

class CategoryViewSet(ESViewSet):
    model = Category
    queryset = Category.objects.all()
    serializer = CategorySerializer
    fields = ('pk','title')

# Serializers define the API representation.
class PersonSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Person
        fields = (
            'parl_id',
            'full_name',
            'reversed_name',
            'birthdate',
            'birthplace',
            'deathdate',
            'deathplace',
            'occupation')

class PersonViewSet(ESViewSet):
    model = Person
    queryset = Person.objects.all()
    serializer = PersonSerializer
    fields = (
            'parl_id',
            'full_name',
            'birthdate',
            'birthplace',
            'occupation')


# Serializers define the API representation.
class LawSerializer(serializers.HyperlinkedModelSerializer):
    category = CategorySerializer(required=False)
    class Meta:
        model = Law
        fields = (
            'title',
            'status',
            'source_link',
            'parl_id',
            'description',
            'category',
            # 'keywords',
            # 'press_releases',
            # 'documents',
            # 'legislative_period',
            # 'references'
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
            'pk')


# Serializers define the API representation.
class DebateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Debate
        fields = (
            'parl_id',
            'full_name',
            'reversed_name',
            'birthdate',
            'birthplace',
            'deathdate',
            'deathplace',
            'occupation')


class DebateViewSet(ESViewSet):
    model = Debate
    queryset = Debate.objects.all()
    serializer = DebateSerializer
    fields = (
            'parl_id',
            'full_name',
            'birthdate',
            'birthplace',
            'occupation')



# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'category', CategoryViewSet, base_name="Category")
router.register(r'persons', PersonViewSet, base_name="Person")
router.register(r'laws', LawViewSet, base_name="Law")
router.register(r'debates', DebateViewSet, base_name="Debate")