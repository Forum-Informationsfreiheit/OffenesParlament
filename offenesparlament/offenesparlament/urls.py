from django.conf.urls import patterns, include, url
from django.contrib import admin
from . import views
from op_scraper import admin_views
from django.conf import settings
from offenesparlament.search_views import JsonSearchView, PersonSearchView, LawSearchView
from op_scraper.models import Person, Law

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='home'),
    url(r'^personen/$', views.person_list, name='person_list'),
    url(r'^personen/(?P<parl_id>.{1,30})/(?P<name>.+)/$',
        views.person_detail, name='person_detail'),
    url(r'^gesetze/$', views.gesetze_list, name='laws_list'),
    url(r'^gesetze/(?P<ggp>.{1,30})/(?P<parl_id>.{1,30})/$',
        views.gesetz_detail, name='gesetz_detail'),
    # Search Urls
    url(r'^search/?$',
        JsonSearchView.as_view()),
    url(r'^personen/search/?$',
        PersonSearchView.as_view()),
    url(r'^gesetze/search/?$',
        LawSearchView.as_view(search_model=Law)),
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/scrape/(?P<spider_name>.{1,30})',
        admin_views.trigger_llp_scrape, name='scrape_llp'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^docs/', include('sphinxdoc.urls')),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
