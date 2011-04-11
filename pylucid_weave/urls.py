#coding:utf-8

from django.conf.urls.defaults import patterns, url, include

from pylucid_weave.views import size_info, info_page

urlpatterns = patterns('',
    url(r'', include('weave.urls')),
    url(r'^size_info/(?P<username>.+)/$', size_info, name="sync-size_info"),
    url(r'^', info_page, name="sync-info_page"),
)
