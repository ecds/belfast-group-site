from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import last_modified
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import get_current_site
import json
import logging
import networkx as nx
from networkx.readwrite import json_graph, gexf
import rdflib
from StringIO import StringIO

from belfast.util import network_data, rdf_data,  \
    rdf_data_lastmodified, network_data_lastmodified, normalize_whitespace
from belfast.rdfns import BELFAST_GROUP_URI
from belfast.groupsheets.rdfmodels import RdfGroupSheet
from belfast.people.rdfmodels import RdfOrganization, RdfPerson, find_places
from belfast.network.util import annotate_graph, filter_graph


logger = logging.getLogger(__name__)


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())

def _relative_flatpage_url(request):
    current_site = get_current_site(request)
    url = request.path
    # if running on a subdomain, search for flatpage with url without leading path
    if '/' in current_site.domain:
        parts = current_site.domain.rstrip('/').split('/')
        suburl = '/%s/' % parts[-1]
        if url.startswith(suburl):
            url = request.path[len(suburl) - 1:]  # -1 to preserve leading /
    return url

def _get_flatpage(request):
    # get flatpage for this url & site if it exists; otherwise, return none
    url = _relative_flatpage_url(request)
    try:
        return FlatPage.objects.get(url=url, sites__id=settings.SITE_ID)
    except FlatPage.DoesNotExist:
        return None

def overview(request):
    # get flatpage for this url; if not available, 404 (?)
    # flatpage = FlatPage.objects.get(url=request.path, sites__id=settings.SITE_ID)
    fpage = get_object_or_404(FlatPage,
        url=_relative_flatpage_url(request), sites__id=settings.SITE_ID)
    return render(request, 'network/overview.html', {'flatpage': fpage})

def _network_graph(min_degree=1, **kwargs):
    graph = network_data().copy()   # don't modify the original network

    rdfgraph = rdf_data()
    # filter graph by type of node
    types = ['Person', 'Organization', 'Place', 'BelfastGroupSheet']

    for n in graph.nodes():
        if ('type' not in graph.node[n] or \
           graph.node[n]['type'] not in types) :
            graph.remove_node(n)
            continue

        # use groupsheets to infer a connection between the author
        # of the groupsheet and the group itself
        # FIXME: this needs to be in data prep/clean, NOT here
        # TODO: should be handled in prep now; confirm and then remove this logic
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

    # AFTER filtering by type, filter out by requested minimum degree

    removed = 0
    for n in graph.nodes():
        if graph.degree(n) < min_degree:
            removed += 1
            graph.remove_node(n)

    logger.info('removed %d nodes with degree less than %d' % (removed, min_degree))

    return graph


# @last_modified(rdf_nx_lastmod)
def full_js(request, mode):
    # mode options:
    #  full (node & link data) or adjacency (adjacency matrix)

    # optionally filter by minimum degree
    min_degree =  request.GET.get('min_degree', None)
    filter = {}
    if min_degree:
        filter['min_degree'] = int(min_degree)

    graph = _network_graph(**filter)
    if mode == 'full':
        graph = annotate_graph(graph, fields=['degree', 'in_degree', 'out_degree',
                                              'betweenness_centrality',
                                              'eigenvector_centrality'])
        # standard nodes & links data
        data = json_graph.node_link_data(graph)

    if mode == 'adjacency':
        # adjacency matrix for generating chord diagram
        matrix = nx.linalg.graphmatrix.adjacency_matrix(graph)
        data = matrix.tolist()
    return HttpResponse(json.dumps(data), content_type='application/json')


# @last_modified(rdf_nx_lastmod)
def full_gexf(request):
    # generate same network graph as gexf for download/use in tools like gephi
    graph = _network_graph()
    buf = StringIO()
    gexf.write_gexf(graph, buf)
    response = HttpResponse(buf.getvalue(), content_type='application/gexf+xml')
    response['Content-Disposition'] = 'attachment; filename=belfastgroup.gexf'
    return response


# @last_modified(rdf_nx_lastmod)
def force_graph(request):
    # force directed graph of entire network
    return render(request, 'network/graph.html')


# @last_modified(rdf_nx_lastmod)
def chord_diagram(request):
    # circular chord chart of entire network
    fpage = _get_flatpage(request)
    return render(request, 'network/chord.html', {'flatpage': fpage})


# @last_modified(rdf_nx_lastmod)
def group_people(request, mode='egograph'):
    fpage = _get_flatpage(request)

    # graph of just people directly connected to the belfast group
    if mode == 'egograph':
        js_view = 'network:bg-js'
    elif mode == 'groupsheet-model':
        js_view = 'network:bg-gs-js'
    return render(request, 'network/bg.html',
                  {'bg_uri': BELFAST_GROUP_URI,
                  'js_view': js_view, 'mode': mode, 'flatpage': fpage})


# @last_modified(rdf_nx_lastmod)
def group_people_js(request, mode='egograph', output='full'):
    if mode == 'egograph':
        degree = request.GET.get('degree', 1)
        extra_opts = {}
        try:
            degree = int(degree)
            # currently only support 1 or 2 degree
            degree = max(1, min(degree, 2))
            # NOTE: degree 2 graph is large enough that it *must* be filtered
            # to be sensible and usable on the webpage;
            # by trial & error, I found a minimum degree of 5 to be reasonable
            if degree == 2:
                extra_opts['min_degree'] = 5
        except ValueError:
            # if a value is passed that can't be converted to int, fallback to 1
            degree = 1

        belfast_group = RdfOrganization(network_data().copy(), BELFAST_GROUP_URI)
        graph = belfast_group.ego_graph(radius=degree, types=['Person', 'Organization'],
                                        **extra_opts)

        # annotate nodes in graph with degree
        # FIXME: not a directional graph; in/out degree not available
        graph = annotate_graph(graph,
            fields=['degree', 'in_degree', 'out_degree',
                    'betweenness_centrality',
                    'eigenvector_centrality'])

    elif mode == 'groupsheet-model':
        graph = gexf.read_gexf(settings.GEXF_DATA['bg1'])
        graph = annotate_graph(graph,
            fields=['degree', #'in_degree', 'out_degree',
                   'betweenness_centrality'])

    if output == 'full':
        data = json_graph.node_link_data(graph)
    if output == 'adjacency':
        # adjacency matrix for generating chord diagram
        matrix = nx.convert_matrix.to_numpy_matrix(graph)

        # NOTE: this also works, but as of networx 1.9 requires scipy
        # matrix = nx.linalg.graphmatrix.adjacency_matrix(graph)
        data = matrix.tolist()

    return HttpResponse(json.dumps(data), content_type='application/json')

def node_info(request):
    node_id = request.GET.get('id', None)
    # TODO: better to get from gexf or rdf ?
    graph = gexf.read_gexf(settings.GEXF_DATA['full'])
    node = graph.node[node_id]
    context = {'node': node}
    if node.get('type', None) == 'Person':
        # init rdf person
        person = RdfPerson(rdf_data(), rdflib.URIRef(node_id))
        context['person'] = person
    # TODO: handle other types? location, organization
    return render(request, 'network/node_info.html', context)


def map(request):
    fpage = _get_flatpage(request)

    people = {}
    # semi-redundant with json view functionality, but easier to build filter
    for pl in find_places():
        # lat/long should have been added in rdf data prep, but
        # check just in case, because missing lat/long breaks the map
        if not all([pl.latitude, pl.longitude]):
            continue

        for p in pl.people:
            if p.local_uri:
                people[str(p.identifier)] = p.fullname

    return render(request, 'network/map.html',
                  {'people': people, 'flatpage': fpage})


# @last_modified(rdf_lastmod)
def map_js(request):
    places = find_places()
    # places = Place.objects.all()
    markers = []
    for pl in places:
        # lat/long should have been added in rdf data prep, but
        # check just in case, because missing lat/long breaks the map
        if not all([pl.latitude, pl.longitude]):
            continue

        tags = []
        # if this place is mentioned in poems, add title/link to description
        texts = ''
        if pl.texts:
            texts = '<p>Mentioned in %s.</p>' % (
                '; '.join('<a href="%s">%s</a>' % (t.identifier, normalize_whitespace(t.name))
                          for t in pl.texts)
            )
            tags.append('text')
            for t in pl.texts:
                if t.author is not None:
                    tags.append(unicode(t.author.identifier))

        people = ''
        if pl.people:
            people = '<p>Connected people: %s.</p>' % (
                '; '.join('<a href="%s">%s</a>' % (p.identifier, p.fullname) if p.local_uri
                          else p.fullname
                          for p in pl.people)
            )
            # possibly put specific slugs here for filtering
            tags.append('people')
            tags.extend([unicode(p.identifier) for p in pl.people if p.local_uri])

        # if this place is not identifiably connected to a person or place
        # in our data, skip it (for now at least)
        if not people and not texts:
            continue

        if people and texts:
            icon = 'bio-text'
        elif people:
            icon = 'bio'
        else:
            icon = 'text'

        info = {
            'latitude': pl.latitude,
            'longitude': pl.longitude,
            'title': pl.name,
            # text (html) content to be shown when clicking on a marker
            'content': '''<b>%s</b> %s %s''' % (pl.name, people, texts),
            # properties to affect display
            'tags': tags,
            # icon color so we can use different icons on the map by type (?)
            'icon_color': 'blue' if texts else 'red',
            'icon': icon

        }
        markers.append(info)

    map_data = {'markers': markers}
    return HttpResponse(json.dumps(map_data), content_type='application/json')

