#coding:utf-8

from django.conf.urls.defaults import patterns, url, include

from pylucid_weave.views import info_page

urlpatterns = patterns('',
    url(r'', include('weave.urls')),
    url(r'^', info_page, name="weave-info_page"),
)
