import sys
sys.path.append('../offenesparlament')
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'offenesparlament.settings'


from scrapy.contrib.djangoitem import DjangoItem
from op_scraper.models import Phase
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion

class PhaseItem(DjangoItem):
    django_model = Phase

class EntityItem(DjangoItem):
    django_model = Entity

class DocumentItem(DjangoItem):
    django_model = Document

class PressReleaseItem(DjangoItem):
    django_model = PressRelease

class CategoryItem(DjangoItem):
    django_model = Category

class KeywordItem(DjangoItem):
    django_model = Keyword

class LawItem(DjangoItem):
    django_model = Law

class StepItem(DjangoItem):
    django_model = Step

class OpinionItem(DjangoItem):
    django_model = Opinion
