from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
import json
from networkx.readwrite import json_graph
import rdflib

from belfast import rdfns
from belfast.util import rdf_data, rdf_data_lastmodified, \
    network_data_lastmodified
from belfast.people.models import RdfPerson, BelfastGroup
from belfast.groupsheets.models import get_rdf_groupsheets


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


@last_modified(rdf_lastmod)  # for now, list is based on rdf
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
        uri = 'http://viaf.org/viaf/%s' % idnum
        graph = rdf_data()
        if (rdflib.URIRef(uri), rdflib.RDF.type, rdfns.SCHEMA_ORG.Person) in graph:
            person = RdfPerson(graph, rdflib.URIRef(uri))

    # anything else not found for now
    if person is None:
        raise Http404

    return person


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def profile(request, id):
    person = init_person(id)
    groupsheets = get_rdf_groupsheets(author=str(person.identifier))
    return render(request, 'people/profile.html',
        {'person': person, 'groupsheets': groupsheets})


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def egograph_js(request, id):
    person = init_person(id)
    # TODO: possibly make ego-graph radius a parameter in future
    graph = person.ego_graph(radius=1,
                             types=['Person', 'Organization', 'Place'])

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf (?)
def egograph(request, id):
    person = init_person(id)
    return render(request, 'people/ego_graph.html', {'person': person})
