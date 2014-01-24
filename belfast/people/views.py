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
    network_data_lastmodified, local_uri
from belfast.groupsheets.rdfmodels import get_rdf_groupsheets
from belfast.people.models import ProfilePicture
from belfast.people.rdfmodels import BelfastGroup, profile_people, RdfPerson
from belfast.network.util import annotate_graph


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


# @last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    # display a list of people one remove from belfast group
    people = profile_people()
    people = [p for p in people if p.description or p.dbpedia and p.dbpedia.description]
    # people = BelfastGroup().connected_people
    # people = Person.objects.order_by('last_name').all()
    return render(request, 'people/list.html',
                  {'people': people})


# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def profile(request, id):
    uri = local_uri(reverse('people:profile', args=[id]), request)
    g = rdf_data()
    uriref = rdflib.URIRef(uri)
    # check that the generated URI is actually a person in our rdf dataset;
    # if not, 404
    if not (uriref, rdflib.RDF.type, rdfns.SCHEMA_ORG.Person) in g:
        raise Http404
    person = RdfPerson(g, uriref)
    groupsheets = get_rdf_groupsheets(author=uri) # TODO: move to rdfperson class

    # find profile picture if there is one (not present for all)
    # TODO: make this a class method on rdfperson
    pics = ProfilePicture.objects.filter(person_uri=uri)
    pic = pics[0] if pics.count() else None

    return render(request, 'people/profile.html',
                  {'person': person, 'groupsheets': groupsheets,
                  'pic': pic})


# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def egograph_js(request, id):
    uri = local_uri(reverse('people:profile', args=[id]), request)
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
