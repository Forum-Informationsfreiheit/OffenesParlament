from django.conf.urls import patterns, include, url
from django.contrib import admin
from . import views

urlpatterns = patterns('',
    # Examples:
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', views.index, name='home'),
    url(r'^parlamentarier/$', views.person_list, name='person_list'),
    url(r'^parlamentarier/(?P<parl_id>.{1,30})/(?P<name>.+)/$', views.person_detail, name='person_detail'),
    url(r'^admin/', include(admin.site.urls)),
)
