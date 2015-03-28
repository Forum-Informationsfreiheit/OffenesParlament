from django.contrib import admin
from op_scraper.models import *


@admin.register(Law)
class LawAdmin(admin.ModelAdmin):
    list_display = ('title', 'legislative_period', 'parl_id', 'category')
    pass


@admin.register(Person)
class PersonAdmint(admin.ModelAdmin):
    filter_horizontal = ('mandates',)

admin.site.register(Phase)
admin.site.register(Entity)
admin.site.register(Document)
admin.site.register(PressRelease)
admin.site.register(Category)
admin.site.register(Keyword)
admin.site.register(Step)
admin.site.register(Opinion)
admin.site.register(Party)
admin.site.register(Function)
admin.site.register(Mandate)
