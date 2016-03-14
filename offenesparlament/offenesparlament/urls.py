from django.conf.urls import patterns, include, url
from django.contrib import admin
from offenesparlament.views import base_views
from offenesparlament.views import subscriptions
from op_scraper import admin_views
from django.conf import settings
from offenesparlament.views import search
from op_scraper.models import Law, Debate, Person

urlpatterns = patterns(
    '',
    url(r'^$', base_views.index, name='home'),
    url(r'^wir/$', base_views.about, name='about'),
    url(r'^abos/$', base_views.subscriptions, name='subscriptions'),
    url(r'^personen/$', base_views.person_list, name='person_list'),
    url(r'^personen/(?P<parl_id>.{1,60})/(?P<name>.+)/$',
        base_views.person_detail, name='person_detail'),
    url(r'^personen/(?P<ggp>[XVIMCD]{1,})/$',
        base_views.person_list_with_ggp, name='person_list_with_ggp'),
    url(r'^gesetze(?:/(?P<ggp>[XVIMCD]{1,}))?/(?P<inq_id>[J|M|A|B|P|E|U|R|\-]+\_+.+)/$',
        base_views.inquiry_detail),
    url(r'^gesetze/$', base_views.gesetze_list, name='laws_list'),
    url(r'^gesetze/(?P<ggp>[XVIMCD]{1,})/$',
        base_views.gesetze_list_with_ggp, name='laws_list_with_ggp'),
    url(r'^gesetze/(?P<ggp>[XVIMCD]{1,})/(?P<parl_id>.{1,60})/$',
        base_views.gesetz_detail, name='gesetz_detail'),
    url(r'^gesetze/(?P<parl_id>.{1,60})/$',
        base_views.gesetz_detail, name='gesetz_detail'),
    url(r'^schlagworte/$', base_views.keyword_list, name='keyword_list'),
    url(r'^schlagworte/(?P<ggp>[XVIMCD]{1,})/$',
        base_views.keyword_list_with_ggp, name='keyword_list_with_ggp'),
    url(r'^schlagworte/(?P<keyword>.+)/$',
        base_views.keyword_detail, name='keyword_detail'),

    url(r'^suche/(.*)/?$', base_views.generic_search_view, name='generic_search_view'),

    # Search Urls
    url(r'^search/?$',
        search.JsonSearchView.as_view()),
    url(r'^personen/search/?$',
        search.PersonSearchView.as_view(search_model=Person)),
    url(r'^gesetze/search/?$',
        search.LawSearchView.as_view(search_model=Law)),
    url(r'^debatten/search/?$',
        search.DebateSearchView.as_view(search_model=Debate)),

    # Subscription URLS

    # Verify a new subscription
    url(r'^verify/(?P<email>.+)/(?P<key>.+)/?$',
        subscriptions.verify,
        name='verify'),

    # Subscribe to a searchable page and start verification
    url(r'^subscribe/?$',
        subscriptions.subscribe),

    # Unsubscribe from a certain subscription
    url(r'^unsubscribe/(?P<email>.+)/(?P<key>.+)/?$',
        subscriptions.unsubscribe,
        name='unsubscribe'),

    # List emails subscriptions
    url(r'^list/(?P<email>.+)/(?P<key>.+)/?$',
        subscriptions.list,
        name='list'),


    # Resend list hashkey for email
    url(r'^list/(?P<email>.+)/?$',
        subscriptions.list,
        name='list'),



    url(r'^grappelli/', include('grappelli.urls')),  # grappelli URLS
    url(r'^admin/scrape/(?P<spider_name>.{1,30})',
        admin_views.trigger_scrape, name='scrape_llp'),
    url(r'^admin/elastic/update',
        admin_views.trigger_reindex, name='update_index'),
    url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
