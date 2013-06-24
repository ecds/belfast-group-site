from django.conf.urls import patterns, include, url
from belfast.people import views

urlpatterns = patterns('',
    url(r'^$', views.list, name='list'),
    url(r'^(?P<id>[a-z0-9:_-]+)/$', views.profile, name='profile'),
    url(r'^(?P<id>[a-z0-9:_-]+)/ego.json$', views.egograph_js, name='egograph-js'),
    url(r'^(?P<id>[a-z0-9:_-]+)/ego-graph/$', views.egograph, name='egograph'),
)
