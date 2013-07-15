from django.conf.urls import patterns, include, url
from belfast.network import views

urlpatterns = patterns('',
    url(r'^$', views.full, name='full'),
    url(r'^full.json$', views.full_js, name='full-js'),
    url(r'^full.gexf$', views.full_gexf, name='full-gexf'),
    url(r'^belfast-group/$', views.group_people, name='bg'),
    url(r'^belfast-group.json$', views.group_people_js, name='bg-js'),
)
