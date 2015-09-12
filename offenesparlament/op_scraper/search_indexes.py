from haystack import indexes

from op_scraper.models import Person, Law


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    source_link = indexes.CharField(model_attr='source_link')
    internal_link = indexes.CharField(model_attr='url')

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
    llps = indexes.MultiValueField(model_attr='llps_roman', faceted=True)

    def get_model(self):
        return Person


class LawIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    internal_link = indexes.CharField(model_attr='url')
    title = indexes.CharField(model_attr='title')
    description = indexes.CharField(model_attr='description')
    category = indexes.CharField(model_attr='category__title', faceted=True)
    keywords = indexes.MultiValueField(
        model_attr='keyword_titles', faceted=True)
    llp = indexes.CharField(model_attr='llp_roman', faceted=True)

    def get_model(self):
        return Law
