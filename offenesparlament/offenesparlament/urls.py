from django.conf.urls import patterns, include, url
from django.contrib import admin
from . import views
from op_scraper import admin_views
from django.conf import settings

urlpatterns = patterns(
    '',
    url(r'^$', views.index, name='home'),
    url(r'^personen/$', views.person_list, name='person_list'),
    url(r'^personen/(?P<parl_id>.{1,30})/(?P<name>.+)/$',
        views.person_detail, name='person_detail'),
    url(r'^gesetze/$', views.gesetze_list, name='laws_list'),
    url(r'^gesetze/(?P<ggp>.{1,30})/(?P<parl_id>.{1,30})/$',
        views.gesetz_detail, name='gesetz_detail'),
    url(r'^search/', include('haystack.urls')),
    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/scrape/(?P<spider_name>.{1,30})',
        admin_views.trigger_llp_scrape, name='scrape_llp'),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
