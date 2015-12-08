from django.contrib import admin
from django.db.models import Count
from op_scraper.models import *
import reversion
from import_export import resources
from import_export.admin import ImportExportMixin


class LawResource(resources.ModelResource):

    class Meta:
        model = Law


class BaseAdmin(ImportExportMixin, reversion.VersionAdmin):
    change_list_template = "admin/changelist.html"


@admin.register(Law)
class LawAdmin(BaseAdmin):
    list_display = (
        'title', 'legislative_period', 'parl_id', 'category', 'references')
    list_filter = ('category', 'legislative_period')
    search_fields = ('parl_id', 'title')
    resource_class = LawResource
    pass


@admin.register(Person)
class PersonAdmin(BaseAdmin):
    filter_horizontal = ('mandates',)
    search_fields = ('parl_id', 'full_name')


@admin.register(Statement)
class StatementAdmin(BaseAdmin):
    pass


@admin.register(Phase)
class PhaseAdmin(BaseAdmin):
    pass


@admin.register(LegislativePeriod)
class PhaseAdmin(BaseAdmin):
    pass


@admin.register(Entity)
class EntityAdmin(BaseAdmin):
    list_display = ('title', 'show_op_count')
    search_fields = ('title', 'title_detail', 'email')

    def get_queryset(self, request):
        return Entity.objects.annotate(op_count=Count('opinions'))

    def show_op_count(self, inst):
        return inst.op_count
    show_op_count.admin_order_field = 'op_count'
    pass


@admin.register(Document)
class DocumentAdmin(BaseAdmin):
    pass


@admin.register(PressRelease)
class PressReleaseAdmin(BaseAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(BaseAdmin):
    pass


@admin.register(Keyword)
class KeywordAdmin(BaseAdmin):
    pass


@admin.register(Step)
class StepAdmin(BaseAdmin):
    pass


@admin.register(Opinion)
class OpinionAdmin(BaseAdmin):
    pass


@admin.register(Party)
class PartyAdmin(BaseAdmin):
    pass


@admin.register(Function)
class FunctionAdmin(BaseAdmin):
    pass


@admin.register(Mandate)
class MandateAdmin(BaseAdmin):
    pass


@admin.register(Petition)
class PetitionAdmin(BaseAdmin):
    pass


@admin.register(DebateStatement)
class DebateStatementAdmin(BaseAdmin):
    list_display = (
        'doc_section', 'speaker_name',
        'text_type', 'speaker_role',
        'page_start', 'page_end', 'date')


@admin.register(Debate)
class DebateStatementAdmin(BaseAdmin):
    list_display = ('title', 'date', 'protocol_url')
