from django.contrib import admin
from django.db.models import Count
from op_scraper.models import *
import reversion


@admin.register(Law)
class LawAdmin(reversion.VersionAdmin):
    list_display = (
        'title', 'legislative_period', 'parl_id', 'category', 'references')
    list_filter = ('category', )
    search_fields = ('parl_id', 'title')
    pass


@admin.register(Person)
class PersonAdmin(reversion.VersionAdmin):
    filter_horizontal = ('mandates',)


@admin.register(Phase)
class PhaseAdmin(reversion.VersionAdmin):
    pass


@admin.register(Entity)
class EntityAdmin(reversion.VersionAdmin):
    list_display = ('title', 'show_op_count')
    search_fields = ('parl_id', 'title', 'title_detail')

    def get_queryset(self, request):
        return Entity.objects.annotate(op_count=Count('opinions'))

    def show_op_count(self, inst):
        return inst.op_count
    show_op_count.admin_order_field = 'op_count'
    pass


@admin.register(Document)
class DocumentAdmin(reversion.VersionAdmin):
    pass


@admin.register(PressRelease)
class PressReleaseAdmin(reversion.VersionAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(reversion.VersionAdmin):
    pass


@admin.register(Keyword)
class KeywordAdmin(reversion.VersionAdmin):
    pass


@admin.register(Step)
class StepAdmin(reversion.VersionAdmin):
    pass


@admin.register(Opinion)
class OpinionAdmin(reversion.VersionAdmin):
    pass


@admin.register(Party)
class PartyAdmin(reversion.VersionAdmin):
    pass


@admin.register(Function)
class FunctionAdmin(reversion.VersionAdmin):
    pass


@admin.register(Mandate)
class MandateAdmin(reversion.VersionAdmin):
    pass
