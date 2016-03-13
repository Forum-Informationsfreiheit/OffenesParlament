from haystack import indexes

from op_scraper.models import Person, Law, Debate
import json

# maintain list of which fields are json-content
JSON_FIELDS = {
    'person': ['mandates', 'statements', 'debate_statements'],
    'law': ['steps', 'opinions', 'documents'],
}


def extract_json_fields(result, type):
    for field in JSON_FIELDS[type]:
        try:
            result[field] = json.loads(result[field])
        except:
            # didn't work, maybe not json data after all? anywho, no harm done
            pass
    return result


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    FIELDSETS = {
        'all': ['text', 'ts', 'parl_id', 'source_link', 'internal_link', 'photo_link', 'photo_copyright', 'birthdate', 'deathdate', 'full_name', 'reversed_name', 'birthplace', 'deathplace', 'occupation', 'party', 'llps', 'llps_numeric', 'mandates', 'statements', 'debate_statements'],
        'list': ['text', 'ts', 'parl_id', 'source_link', 'internal_link', 'photo_link', 'photo_copyright', 'birthdate', 'deathdate', 'full_name', 'reversed_name', 'birthplace', 'deathplace', 'occupation', 'party', 'llps', 'llps_numeric'],
    }

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
    llps = indexes.MultiValueField(model_attr='llps_facet', faceted=True)
    llps_numeric = indexes.MultiValueField(
        model_attr='llps_facet_numeric', faceted=True)

    # Secondary Items
    mandates = indexes.CharField()
    statements = indexes.CharField()
    debate_statements = indexes.CharField()

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

    def prepare_debate_statements(self, obj):
        """
        Collects the object's statements's as json
        """
        return obj.debate_statements_json

    def get_model(self):
        return Person


class LawIndex(indexes.SearchIndex, indexes.Indexable):

    FIELDSETS = {
        'all': ['text', 'parl_id', 'ts', 'internal_link', 'title', 'description', 'category', 'llps', 'llps_numeric', 'steps', 'opinions', 'documents', 'keywords'],
        'list': ['text', 'parl_id', 'ts', 'internal_link', 'title', 'description', 'category', 'llps', 'llps_numeric', 'steps', 'opinions', 'documents', 'keywords'],
    }

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

    # Related, aggregated and Multi - Value Fields
    steps = indexes.CharField()
    opinions = indexes.CharField()
    documents = indexes.CharField()
    keywords = indexes.MultiValueField(
        model_attr='keyword_titles', faceted=True)

    def index_queryset(self, using=None):
        return self.get_model().objects\
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


class DebateIndex(indexes.SearchIndex, indexes.Indexable):
    FIELDSETS = {
        'all': ['text', 'date', 'title', 'debate_type', 'protocol_url', 'detail_url', 'nr', 'llp', 'statements'],
        'list': ['text', 'date', 'title', 'debate_type', 'protocol_url', 'detail_url', 'nr', 'llp'],
    }

    text = indexes.CharField(document=True, use_template=True)

    date = indexes.DateTimeField(model_attr='date', faceted=True)
    title = indexes.CharField(model_attr='title')
    debate_type = indexes.CharField(model_attr='debate_type', faceted=True)
    protocol_url = indexes.CharField(model_attr='protocol_url')
    detail_url = indexes.CharField(model_attr='detail_url')
    nr = indexes.IntegerField(model_attr='nr', null=True)
    llp = indexes.IntegerField(model_attr='llp__number', faceted=True)

    # soon
    # internal_link = indexes.CharField(model_attr=u'slug')

    # Related, aggregated and Multi - Value Fields
    statements = indexes.MultiValueField()

    def prepare_statements(self, obj):
        """
        Collects the object's statements's as json
        """
        return obj.statements_full_text

    def get_model(self):
        return Debate
