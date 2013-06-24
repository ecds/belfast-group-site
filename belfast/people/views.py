from django.shortcuts import render
from django.http import Http404, HttpResponse
import json
from networkx.readwrite import json_graph
import rdflib

from belfast import rdfns
from belfast.util import rdf_data
from belfast.people.models import RdfPerson, BelfastGroup


def list(request):
    # display a list of people one remove from belfast group
    results = BelfastGroup.connected_people
    return render(request, 'people/list.html',
                  {'people': results})


def init_person(id):
    # consolidate common person lookup logic for single-person/profile views
    person = None
    try:
        idtype, idnum = id.split(':')
    except:
        raise Http404

    if idtype == 'viaf':
        uri = 'http://viaf.org/viaf/%s/' % idnum
        # NOTE: trailing slash not actually canonical, but is in current test data
        graph = rdf_data()
        if (rdflib.URIRef(uri), rdflib.RDF.type, rdfns.SCHEMA_ORG.Person) in graph:
            person = RdfPerson(graph, rdflib.URIRef(uri))

    # anything else not found for now
    if person is None:
        raise Http404

    return person


def profile(request, id):
    person = init_person(id)
    return render(request, 'people/profile.html', {'person': person})


def egograph_js(request, id):
    person = init_person(id)
    graph = person.ego_graph()
    types = ['Person', 'Organization', 'Place']

    for n in graph.nodes():
        if 'type' not in graph.node[n] or graph.node[n]['type'] not in types:
            graph.remove_node(n)

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


def egograph(request, id):
    person = init_person(id)
    return render(request, 'people/ego_graph.html', {'person': person})
