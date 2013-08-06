from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.http import last_modified
import json
import logging
from networkx.readwrite import json_graph, gexf
import rdflib
from StringIO import StringIO

from belfast.util import network_data, rdf_data,  \
    rdf_data_lastmodified, network_data_lastmodified
from belfast.rdfns import BELFAST_GROUP_URI
from belfast.groupsheets.models import RdfGroupSheet
from belfast.people.models import RdfOrganization


logger = logging.getLogger(__name__)


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


def _network_graph():
    graph = network_data().copy()   # don't modify the original network

    rdfgraph = rdf_data()
    # filter graph by type of node
    types = ['Person', 'Organization', 'Place', 'BelfastGroupSheet']
    zeroes = 0
    for n in graph.nodes():
        if 'type' not in graph.node[n] or \
           graph.node[n]['type'] not in types:
            graph.remove_node(n)
            continue

        # use groupsheets to infer a connection between the author
        # of the groupsheet and the group itself
        if graph.node[n]['type'] == 'BelfastGroupSheet':

            sheet = RdfGroupSheet(rdfgraph, rdflib.URIRef(n))
            # FIXME: error handling when author is not in the graph?
            # should probably at least log this...
            if sheet.author and unicode(sheet.author.identifier) in graph:
                graph.add_edge(unicode(sheet.author.identifier),
                               BELFAST_GROUP_URI, weight=4)

            # remove the groupsheet itself from the network, to avoid
            # cluttering up the graph with too much information
            #graph.add_edge(n, BELFAST_GROUP_URI, weight=5)
            graph.remove_node(n)

    # AFTER filtering by type, filter out 0-degree nodes
    for n in graph.nodes():
        if len(graph.in_edges(n)) == 0 and len(graph.out_edges(n)) == 0:
            zeroes += 1
            graph.remove_node(n)

    logger.info('removed %d zero-degree nodes' % zeroes)

    return graph


@last_modified(rdf_nx_lastmod)
def full_js(request):
    graph = _network_graph()
    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')

@last_modified(rdf_nx_lastmod)
def full_gexf(request):
    # generate same network graph as gexf for download/use in tools like gephi
    graph = _network_graph()
    buf = StringIO()
    gexf.write_gexf(graph, buf)
    response = HttpResponse(buf.getvalue(), content_type='application/gexf+xml')
    response['Content-Disposition'] = 'attachment; filename=belfastgroup.gexf'
    return response

@last_modified(rdf_nx_lastmod)
def full(request):
    return render(request, 'network/graph.html')

@last_modified(rdf_nx_lastmod)
def group_people(request):
    return render(request, 'network/bg.html',
                  {'bg_uri': BELFAST_GROUP_URI})

@last_modified(rdf_nx_lastmod)
def group_people_js(request):
    belfast_group = RdfOrganization(network_data().copy(), BELFAST_GROUP_URI)
    ego_graph = belfast_group.ego_graph(radius=1, types=['Person'])
    data = json_graph.node_link_data(ego_graph)
    return HttpResponse(json.dumps(data), content_type='application/json')
