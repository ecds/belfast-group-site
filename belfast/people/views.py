from django.core.urlresolvers import reverse
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
from django.contrib.sites.models import get_current_site
import json
from networkx.readwrite import json_graph
import rdflib

from belfast import rdfns
from belfast.util import rdf_data, rdf_data_lastmodified, \
    network_data_lastmodified
from belfast.groupsheets.rdfmodels import get_rdf_groupsheets
from belfast.people.rdfmodels import BelfastGroup, get_belfast_people, profile_people, RdfPerson
from belfast.network.util import annotate_graph


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


# @last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    # display a list of people one remove from belfast group
    # people = get_belfast_people()
    people = profile_people()
    # people = BelfastGroup().connected_people
    # people = Person.objects.order_by('last_name').all()
    return render(request, 'people/list.html',
                  {'people': people})


# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def profile(request, id):
    current_site = get_current_site(request)
    uri = 'http://%s%s' % (
        current_site.domain,
        reverse('people:profile', args=[id])
    )
    g = rdf_data()
    person = RdfPerson(g, rdflib.URIRef(uri))
    groupsheets = get_rdf_groupsheets(author=uri) # TODO: move to rdfperson class
    # for t in g.triples((rdflib.URIRef(uri), None, None)):
    #     print t

    # person = get_object_or_404(Person, slug=id)
    return render(request, 'people/profile.html',
                  {'person': person, 'groupsheets': groupsheets})


# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def egograph_js(request, id):
    current_site = get_current_site(request)
    uri = 'http://%s%s' % (
        current_site.domain,
        reverse('people:profile', args=[id])
    )
    g = rdf_data()
    person = RdfPerson(g, rdflib.URIRef(uri))
    # TODO: possibly make ego-graph radius a parameter in future
    graph = person.ego_graph(radius=1,
                             types=['Person', 'Organization', 'Place'])
    # annotate nodes in graph with degree
        # FIXME: not a directional graph; in/out degree not available

    graph = annotate_graph(graph, fields=['degree', 'in_degree', 'out_degree',
                                          'betweenness_centrality',
                                          'eigenvector_centrality'])

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf (?)
def egograph(request, id):
    person = get_object_or_404(Person, slug=id)
    return render(request, 'people/ego_graph.html', {'person': person})
