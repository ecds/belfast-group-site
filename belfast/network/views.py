from django.shortcuts import render
from django.http import HttpResponse
import json
from networkx.readwrite import json_graph
import rdflib

from belfast.util import network_data, rdf_data
from belfast.rdfns import BELFAST_GROUP_URI
from belfast.groupsheets.models import RdfGroupSheet


def full_js(request):
    graph = network_data()
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

    print 'removed %d zero-degree nodes' % zeroes

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


def full(request):
    return render(request, 'network/graph.html')
