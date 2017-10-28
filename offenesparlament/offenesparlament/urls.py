from django.conf.urls import patterns, include, url
from django.contrib import admin
from offenesparlament.views import base_views
from offenesparlament.views import subscriptions
from offenesparlament.views.api import router
from offenesparlament.views import commentedcontent
from op_scraper import admin_views
from django.conf import settings
from offenesparlament.views import search
from op_scraper.models import Law, Debate, Person

urlpatterns = patterns(
    '',
    url(r'^$', base_views.index, name='home'),
    url(r'^wir/$', base_views.about, name='about'),
    url(r'^wir/doku/$', base_views.docs, name='docs'),
    url(r'^personen/$', base_views.person_list, name='person_list'),
    url(r'^personen/(?P<parl_id>.{1,60})/(?P<name>.+)/$',
        base_views.person_detail, name='person_detail'),
    url(r'^personen/(?P<ggp>[XVIMCD]{1,})/$',
        base_views.person_list_with_ggp, name='person_list_with_ggp'),
    url(r'^gesetze(?:/(?P<ggp>[XVIMCD]{1,}))?/(?P<inq_id>[J|M|A|B|P|E|U|R|\-]+\_+.+)/$',
        base_views.inquiry_detail, name='inquiry_detail'),
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
    # url(r'^petitionen/$', base_views.petition_list, name='petition_list'),
    # url(r'^petitionen/(?P<ggp>[XVIMCD]{1,})/$', base_views.petition_list_with_ggp, name='petition_list_with_ggp'),
    url(r'^petitionen/(?P<ggp>[XVIMCD]{1,})/(?P<parl_id>.{1,60})/$',
        base_views.petition_detail, name='petition_detail'),
    url(r'^petitionen/(?P<parl_id>.{1,60})/$', base_views.petition_detail, name='petition_detail'),
    # url(r'^signatures/petitionen/(?P<ggp>[XVIMCD]{1,})/(?P<parl_id>.{1,60})/$',
    #     base_views.petition_signatures, name='petition_signatures'),
    # url(r'^generic_email/$', base_views.generic_email, name='generic_email'),
    url(r'^debatten/$', base_views.debate_list, name='debate_list'),
    url(r'^debatten/(?P<ggp>[XVIMCD]{1,})/$', base_views.debate_list_with_ggp, name='debate_list_with_ggp'),
    url(r'^debatten/(?P<ggp>[XVIMCD]{1,})/(?P<debate_type>[NBR]{2})/(?P<number>\d+)$', base_views.debate_detail, name='debate_detail'),
    url(r'^ausschuss/(?P<ggp>[XVIMCD]{1,})/(?P<parl_id>.{1,60})$', base_views.committee_detail, name='committee_detail'),
    url(r'^ausschuss/(?P<parl_id>.{1,60})$', base_views.committee_detail, name='committee_detail'),



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
    url(r'^verify/(?P<email>[^/]+)/(?P<key>[^/]+)/?$',
        subscriptions.verify,
        name='verify'),

    # Subscribe to a searchable page and start verification
    url(r'^subscribe/?$',
        subscriptions.subscribe),

    # Unsubscribe from a certain subscription
    url(r'^unsubscribe/(?P<email>[^/]+)/(?P<key>[^/]+)/?$',
        subscriptions.unsubscribe,
        name='unsubscribe'),

    # Show login form (only email address)
    url(r'^abos/$', subscriptions.login, name='subscriptions'),

    # login
    url(r'^abos/login/(?P<email>[^/]+)/(?P<key>[^/]+)/?$',
        subscriptions.login2, name='subscriptions_login2'),

    # List emails subscriptions
    url(r'^abos/list/?$',
        subscriptions.list,
        name='list_subscriptions'),


    # Resend list hashkey for email
    url(r'^abos/(?P<email>[^/]+)/?$',
        subscriptions.list,
        name='list_subscriptions'),

    # Resend list hashkey for email
    url(r'^abos/(?P<email>[^/]+)/?$',
        subscriptions.list,
        name='list_subscriptions'),

    # REST Api
    url(r'^api/', include(router.urls, namespace='op_api')),
    # url(r'^api/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^kommentiert/?$',
        base_views.kommentiert,
        name='commentedcontent_index'),
    url(r'^abos/kommentiert/new/?$',
        commentedcontent.CommentedContentCreate.as_view(),
        name='commentedcontent_create'),
    url(r'^abos/kommentiert/(?P<pk>.*)/edit/?$',
        commentedcontent.CommentedContentUpdate.as_view(),
        name='commentedcontent_update'),
    url(r'^abos/kommentiert/(?P<pk>.*)/delete/?$',
        commentedcontent.CommentedContentDelete.as_view(),
        name='commentedcontent_delete'),
    url(r'^abos/kommentiert/preview/?$',
        commentedcontent.preview,
        name='commentedcontent_preview'),

    url(r'^kommentiert/(?P<pk>[^/]*)/?$',
        commentedcontent.view,
        name='commentedcontent_view'),


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
                            (r'^media/(?P<path>.*)$', 'django.views.static.serve', {
                             'document_root': settings.MEDIA_ROOT}))
    urlpatterns += patterns('',
                            url(r'^__debug__/', include(debug_toolbar.urls)),
                            )
