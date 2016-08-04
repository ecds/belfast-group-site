from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import last_modified
import json
from networkx.readwrite import json_graph, gexf
import rdflib

from belfast import rdfns
from belfast.util import rdf_data, rdf_data_lastmodified, \
    network_data_lastmodified, local_uri
from belfast.groupsheets.rdfmodels import get_rdf_groupsheets
from belfast.people.rdfmodels import profile_people, RdfPerson, RdfPoem
from belfast.network.util import annotate_graph


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


@last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    'Display a list of people one remove from the Belfast Group.'
    people = profile_people()
    # filter to only people with a description
    people = [p for p in people if p.has_profile]

    # filter to people with a profile photo loaded, if requested
    # (defaults to true)
    if getattr(settings, 'REQUIRE_PROFILE_PICTURE', True):
        people = [p for p in people if p.picture]

    return render(request, 'people/list.html',
                  {'people': people})

@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def profile(request, id):
    'Display a profile page for a single person associated with the Belfast Group.'
    uri = local_uri(reverse('people:profile', args=[id]), request)
    g = rdf_data()
    uriref = rdflib.URIRef(uri)
    # check that the generated URI is actually a person in our rdf dataset;
    # if not, 404
    if not (uriref, rdflib.RDF.type, rdfns.SCHEMA_ORG.Person) in g:
        raise Http404
    person = RdfPerson(g, uriref)
    groupsheets = get_rdf_groupsheets(author=uri) # TODO: move to rdfperson class

    return render(request, 'people/profile.html',
                  {'person': person, 'groupsheets': groupsheets,
                  'page_rdf_type': 'schema:ProfilePage'})


@last_modified(rdf_nx_lastmod)  # uses both rdf and gexf
def egograph_js(request, id):
    'Egograph information as JSON for a single person.'
    uri = local_uri(reverse('people:profile', args=[id]), request)
    g = rdf_data()
    person = RdfPerson(g, rdflib.URIRef(uri))
    graph = person.ego_graph(radius=1,
                             types=['Person', 'Organization', 'Place'])
    # annotate nodes in graph with degree
    #  NOTE: not a directional graph, so in/out degree not available

    graph = annotate_graph(graph, fields=['degree', 'in_degree', 'out_degree',
                                          'betweenness_centrality',
                                          'eigenvector_centrality'])

    data = json_graph.node_link_data(graph)
    return HttpResponse(json.dumps(data), content_type='application/json')


# NOTE: egograph view no longer in use, but might want to consider
# switching network graph tab of profile page to be loaded via ajax

# @last_modified(rdf_nx_lastmod)  # uses both rdf and gexf (?)
# def egograph(request, id):
#     person = get_object_or_404(Person, slug=id)
#     return render(request, 'people/ego_graph.html', {'person': person})

def egograph_node_info(request, id):
    '''HTML snippet to provide information about a node in the egograph.
    Intended to be loaded and displayed via AJAX.

    Some overlap with :meth:`belfast.network.views.node_info`.
    '''

    # id is the person to whom this node is connected
    uri = local_uri(reverse('people:profile', args=[id]), request)
    g = rdf_data()
    ego_person = RdfPerson(g, rdflib.URIRef(uri))

    # NOTE: some overlap here with networks node_info view

    # id param is the node we want information
    node_id = request.GET.get('id', None)
    if node_id is None:
        raise Http404

    node_uri = rdflib.URIRef(node_id)
    # TODO: better to get relations from gexf or rdf ?
    graph = gexf.read_gexf(settings.GEXF_DATA['full'])
    node = graph.node[node_id]
    context = {'node': node}

    if node.get('type', None) == 'Person':
        # init rdf person
        person = RdfPerson(rdf_data(), rdflib.URIRef(node_id))
        context['person'] = person

    # determine relation between node and ego-center
    rels = set(g.predicates(ego_person.identifier, node_uri))
    # TODO: may want to display other relationships?

    # special case: if "mentions", should be a poem; find for display/link
    if rdfns.SCHEMA_ORG.mentions in rels:
        txts = set(g.subjects(rdfns.SCHEMA_ORG.mentions, node_uri)) \
               - set([ego_person.identifier])
        if txts:
            poems = [RdfPoem(g, p) for p in txts]
            # explicitly skip any non-poems, just in case
            context['poems'] = [p for p in poems if rdfns.FREEBASE["book/poem"] in p.rdf_types]

    return render(request, 'network/node_info.html', context)
