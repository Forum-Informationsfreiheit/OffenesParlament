from django.contrib import admin
from op_scraper.models import Phase
from op_scraper.models import Entity
from op_scraper.models import Document
from op_scraper.models import PressRelease
from op_scraper.models import Category
from op_scraper.models import Keyword
from op_scraper.models import Law
from op_scraper.models import Step
from op_scraper.models import Opinion


@admin.register(Law)
class LawAdmin(admin.ModelAdmin):
    list_display = ('legislative_period', 'parl_id', 'title')
    pass

admin.site.register(Phase)
admin.site.register(Entity)
admin.site.register(Document)
admin.site.register(PressRelease)
admin.site.register(Category)
admin.site.register(Keyword)
admin.site.register(Step)
admin.site.register(Opinion)
