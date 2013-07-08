from django.conf.urls import patterns, include, url
from belfast.groupsheets import views

urlpatterns = patterns(
    '',
    url(r'^$', views.list, name='list'),
    url(r'^search/$', views.search, name='search'),
    url(r'^(?P<id>[a-z0-9_-]+)/$', views.view_sheet, name='view'),
    url(r'^xml/(?P<name>[-a-z0-9_.]+)/$', views.teixml, name='xml'),
)
