from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from belfast.network import views

urlpatterns = patterns('',
    url(r'^$', views.overview, name='overview'),
    url(r'^full/$', views.force_graph, name='force-graph'),
    url(r'^chord/$', views.chord_diagram, name='chord'),
    url(r'^(?P<mode>full|adjacency).json$', views.full_js, name='js'),
#    url(r'^adjacency.json$', views.adjacency_js, name='adjacency-js'),

    url(r'^belfast-group/$', views.group_people, name='bg'),
    url(r'^belfast-group.json$',
        views.group_people_js, {'output': 'full'}, name='bg-js'),
    url(r'^belfast-group_matrix.json$',
        views.group_people_js, {'output': 'adjacency'}, name='bg-js-matrix'),
    url(r'^belfast-group/groupsheets/$', views.group_people,
        {'mode': 'groupsheet-model'}, name='bg-gs'),
    url(r'^belfast-group/groupsheets.json$', views.group_people_js,
        {'mode': 'groupsheet-model'}, name='bg-gs-js'),
    url(r'^map/$', views.map, name='map'),
    url(r'^map.json$', views.map_js, name='map-js'),
    url(r'^node/$', views.node_info, name='node-info'),

    # network data in GEXF format
    url(r'^(?P<mode>all|group-people|groupsheets).gexf$', views.gexf_content, name='gexf'),
)
