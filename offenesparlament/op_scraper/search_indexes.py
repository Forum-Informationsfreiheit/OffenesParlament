from haystack import indexes

from op_scraper.models import Person, Law


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    ts = indexes.DateTimeField(model_attr='ts', faceted=True)
    parl_id = indexes.CharField(model_attr='parl_id')

    source_link = indexes.CharField(model_attr='source_link')
    internal_link = indexes.CharField(model_attr='slug')
    photo_link = indexes.CharField(model_attr='photo_link')
    photo_copyright = indexes.CharField(model_attr='photo_copyright')

    birthdate = indexes.DateTimeField(model_attr='birthdate', null=True)
    deathdate = indexes.DateTimeField(model_attr='deathdate', null=True)
    full_name = indexes.CharField(model_attr='full_name')
    reversed_name = indexes.CharField(model_attr='reversed_name')
    birthplace = indexes.CharField(
        model_attr='birthplace', faceted=True, null=True)
    deathplace = indexes.CharField(
        model_attr='deathplace', faceted=True, null=True)
    occupation = indexes.CharField(
        model_attr='occupation', faceted=True, null=True)
    party = indexes.CharField(model_attr='party', faceted=True, null=True)
    llps = indexes.CharField(model_attr='llps_facet', faceted=True)
    llps_numeric = indexes.MultiValueField(
        model_attr='llps_facet_numeric', faceted=True)

    # Secondary Items
    mandates = indexes.CharField()
    statements = indexes.CharField()

    def prepare_mandates(self, obj):
        """
        Collects the object's mandates as json
        """
        return obj.mandates_json

    def prepare_statements(self, obj):
        """
        Collects the object's statements's as json
        """
        return obj.statements_json

    def get_model(self):
        return Person


class LawIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    parl_id = indexes.CharField(model_attr='parl_id')
    ts = indexes.DateTimeField(model_attr='ts', faceted=True)

    internal_link = indexes.CharField(model_attr=u'slug')
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    category = indexes.CharField(
        model_attr='category__title', faceted=True, null=True)
    llps = indexes.MultiValueField(model_attr='llps_facet', faceted=True)
    llps_numeric = indexes.MultiValueField(
        model_attr='llps_facet_numeric', faceted=True)

    # Related, aggregated and Multi-Value Fields
    steps = indexes.CharField()
    opinions = indexes.CharField()
    documents = indexes.CharField()
    keywords = indexes.MultiValueField(
        model_attr='keyword_titles', faceted=True)

    def index_queryset(self, using=None):
        return self.get_model()\
            .objects.filter(petition__isnull=True)\
            .filter(inquiry__isnull=True)\
            .filter(inquiryresponse__isnull=True)

    def prepare_steps(self, obj):
        """
        Collects the object's step's as json
        """
        return obj.steps_by_phases_json()

    def prepare_opinions(self, obj):
        """
        Collects the object's opinions's id
        """
        return obj.opinions_json()

    def prepare_documents(self, obj):
        """
        Collects the object's documents's id
        """
        return obj.documents_json()

    def get_model(self):
        return Law
