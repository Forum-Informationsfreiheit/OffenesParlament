from django.contrib import admin
from op_scraper.models import *
import reversion


@admin.register(Law)
class LawAdmin(reversion.VersionAdmin):
    list_display = ('title', 'legislative_period', 'parl_id', 'category')
    pass


@admin.register(Person)
class PersonAdmin(reversion.VersionAdmin):
    filter_horizontal = ('mandates',)


@admin.register(Phase)
class PhaseAdmin(reversion.VersionAdmin):
    pass


@admin.register(Entity)
class EntityAdmin(reversion.VersionAdmin):
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
