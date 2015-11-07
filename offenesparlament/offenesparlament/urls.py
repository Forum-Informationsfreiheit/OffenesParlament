from django.conf.urls import patterns, include, url
from django.contrib import admin
from offenesparlament.views import base_views
from op_scraper import admin_views
from django.conf import settings
from offenesparlament.views import search
from op_scraper.models import Law

urlpatterns = patterns(
    '',
    url(r'^$', base_views.index, name='home'),
    url(r'^wir/$', base_views.about, name='about'),
    url(r'^personen/$', base_views.person_list, name='person_list'),
    url(r'^personen/(?P<parl_id>.{1,30})/(?P<name>.+)/$',
        base_views.person_detail, name='person_detail'),
    url(r'^gesetze/$', base_views.gesetze_list, name='laws_list'),
    url(r'^gesetze/(?P<ggp>.{1,30})/(?P<parl_id>.{1,30})/$',
        base_views.gesetz_detail, name='gesetz_detail'),
    url(r'^schlagworte/$', base_views.keyword_list, name='keyword_list'),
    url(r'^schlagworte/(?P<keyword>.+)/$',
        base_views.keyword_detail, name='keyword_detail'),

    # Search Urls
    url(r'^search/?$',
        search.JsonSearchView.as_view()),
    url(r'^personen/search/?$',
        search.PersonSearchView.as_view()),
    url(r'^gesetze/search/?$',
        search.LawSearchView.as_view(search_model=Law)),

    # Subscribe & verify Urls
    url(r'^verify/(?P<email>.+)/(?P<key>.+)/?$',
        base_views.verify,
        name='verify'),

    url(r'^subscribe/?$',
        base_views.subscribe),

    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/scrape/(?P<spider_name>.{1,30})',
        admin_views.trigger_scrape, name='scrape_llp'),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
