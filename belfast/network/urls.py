from django.conf.urls import patterns, include, url
from belfast.network import views

urlpatterns = patterns('',
    url(r'^$', views.force_graph, name='force-graph'),
    url(r'^chord/$', views.chord_diagram, name='chord'),
    url(r'^(?P<mode>full|adjacency).json$', views.full_js, name='js'),
#    url(r'^adjacency.json$', views.adjacency_js, name='adjacency-js'),
    url(r'^full.gexf$', views.full_gexf, name='full-gexf'),
    url(r'^belfast-group/$', views.group_people, name='bg'),
    url(r'^belfast-group.json$', views.group_people_js, name='bg-js'),
)
