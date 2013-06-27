from django.shortcuts import render
from django.http import HttpResponse
import json
from networkx.readwrite import json_graph

from belfast.util import network_data


def full_js(request):
    graph = network_data()
    # filter graph by type of node
    types=['Person', 'Organization', 'Place', 'BelfastGroupSheet']
    for n in graph.nodes():
        if 'type' not in graph.node[n] or \
           graph.node[n]['type'] not in types:
           graph.remove_node(n)

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


def full(request):
    return render(request, 'network/graph.html')
