from haystack import indexes

from op_scraper.models import Person, Law


class PersonIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    birthdate = indexes.DateTimeField(model_attr='birthdate', null=True)
    deathdate = indexes.DateTimeField(model_attr='deathdate', null=True)

    def get_model(self):
        return Person

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""

        return self.get_model().objects.all()


class LawIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        return Law

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""

        return self.get_model().objects.all()
