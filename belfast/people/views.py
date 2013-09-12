from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
import json
from networkx.readwrite import json_graph
import rdflib

from belfast import rdfns
from belfast.util import rdf_data, rdf_data_lastmodified, \
    network_data_lastmodified
from belfast.people.models import Person
from belfast.network.util import annotate_graph


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


@last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    # display a list of people one remove from belfast group
    people = Person.objects.order_by('last_name').all()
    return render(request, 'people/list.html',
                  {'people': people})


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def profile(request, id):
    person = get_object_or_404(Person, slug=id)
    return render(request, 'people/profile.html',
                  {'person': person, 'groupsheets': person.groupsheet_set.all()})


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def egograph_js(request, id):
    person = get_object_or_404(Person, slug=id)
    # TODO: possibly make ego-graph radius a parameter in future
    graph = person.rdfinfo.ego_graph(radius=1,
                                     types=['Person', 'Organization', 'Place'])
    # annotate nodes in graph with degree
        # FIXME: not a directional graph; in/out degree not available

    graph = annotate_graph(graph, fields=['degree', 'in_degree', 'out_degree',
                                          'betweenness_centrality',
                                          'eigenvector_centrality'])

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf (?)
def egograph(request, id):
    person = get_object_or_404(Person, slug=id)
    return render(request, 'people/ego_graph.html', {'person': person})
