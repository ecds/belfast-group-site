from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.views.decorators.http import last_modified
from django.contrib.flatpages.models import FlatPage
import json
import logging
import networkx as nx
from networkx.readwrite import json_graph, gexf
import rdflib
from StringIO import StringIO

from belfast.util import network_data, rdf_data,  \
    rdf_data_lastmodified, network_data_lastmodified, normalize_whitespace, \
    relative_flatpage_url, get_flatpage
from belfast.rdfns import BELFAST_GROUP_URI
from belfast.groupsheets.rdfmodels import RdfGroupSheet
from belfast.people.rdfmodels import RdfOrganization, RdfPerson, find_places
from belfast.network.util import annotate_graph


logger = logging.getLogger(__name__)


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())


def overview(request):
    '''Overview/intro page for network graphs and maps, with links to the
    network graphs, chord diagrams, and maps.

    Looks for a :class:`~django.contrib.flatpages.models.FlatPage` for this url,
    and if found, passes to the template to include in display.  If no
    page is found, results in a 404 not found error.
    '''
    # get flatpage for this url; if not available, 404
    fpage = get_object_or_404(FlatPage,
        url=relative_flatpage_url(request), sites__id=settings.SITE_ID)
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


@last_modified(rdf_nx_lastmod)
def full_js(request, mode):
    '''Return full network graph data as JSON.  Optionally filter
    the data by minimum degree, if min_degree is specified as a url parameter.
    When generating the node and link data, nodes are annotated with
    degree, in degree, out degree, betweenness centrality, and eigenvector
    centrality if available.  (In/out degree is only available for directed
    graphs.)


    :param mode: full - node and link data; adjacency - adjacency matrix,
        used to construct a chord diagram

    .. deprecated:: 1.0

       This network graph is too large to be usable or viewable in a
       browser/javascript display environment, and should not be used;
       :meth:`group_people` should be used instead.
    '''


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


@last_modified(rdf_nx_lastmod)
def full_gexf(request):
    '''Generate the same Belfast Group network data exposed in :meth:`full_js`
    in the GEXF format, for download and use in tools like Gephi.'''
    graph = _network_graph()
    buf = StringIO()
    gexf.write_gexf(graph, buf)
    response = HttpResponse(buf.getvalue(), content_type='application/gexf+xml')
    response['Content-Disposition'] = 'attachment; filename=belfastgroup.gexf'
    return response


@last_modified(rdf_nx_lastmod)
def gexf_content(request, mode):
    '''Make network data available as GEXF files for download and use in
    tools like Gephi.'''
    if mode == 'all':
        graph = network_data()
    elif mode == 'group-people':
        # filtered graph of people/places/organizations used for
        # first BG network graph displayed on the site
        # - same data used in :meth:`full_js`
        graph = _network_graph()
    elif mode == 'groupsheets':
        graph = gexf.read_gexf(settings.GEXF_DATA['bg1'])

    buf = StringIO()
    gexf.write_gexf(graph, buf)
    response = HttpResponse(buf.getvalue(), content_type='application/gexf+xml')
    response['Content-Disposition'] = 'attachment; filename=belfastgroup-%s.gexf' % mode
    return response


@last_modified(rdf_nx_lastmod)
def force_graph(request):
    '''Display a force-directed graph of the entire network.

    .. deprecated:: 1.0

       This network graph is too large to be usable or viewable in a
       browser/javascript display environment, and should not be used;
       :meth:`group_people` should be used instead.
    '''
    return render(request, 'network/graph.html')


@last_modified(rdf_nx_lastmod)
def chord_diagram(request):
    '''Display a circular chord diagram of the Belfast Group network.

    If a :class:`~django.contrib.flatpages.models.FlatPage` is found for
    this url, it is passed to the template to include in display.
    '''
    fpage = get_flatpage(request)
    return render(request, 'network/chord.html', {'flatpage': fpage})

@last_modified(rdf_nx_lastmod)
def group_people(request, mode='egograph'):
    '''Display a force-directed graph of people associated with the
    Belfast Group.

    :param mode: egograph: display people directly connected to the
       Belfast Group; groupsheet-model display a network model generated
       from information about the Group sheets.

    If a :class:`~django.contrib.flatpages.models.FlatPage` is found for
    this url, it is passed to the template to include in display.
    '''

    fpage = get_flatpage(request)

    # graph of just people directly connected to the belfast group
    if mode == 'egograph':
        js_view = 'network:bg-js'
    elif mode == 'groupsheet-model':
        js_view = 'network:bg-gs-js'
    return render(request, 'network/bg.html',
                  {'bg_uri': BELFAST_GROUP_URI,
                  'js_view': js_view, 'mode': mode, 'flatpage': fpage})


@last_modified(rdf_nx_lastmod)
def group_people_js(request, mode='egograph', output='full'):
    '''Return Belfast Group network graph data as JSON, for use with
    :meth:`group_people`.

    Optionally filter
    the data by minimum degree, if min_degree is specified as a url parameter.
    When generating the node and link data, nodes are annotated with
    degree, in degree, out degree, betweenness centrality, and eigenvector
    centrality if available.  (In/out degree is only available for directed
    graphs.)

    :param mode: egograph: network information for a one- or two-degree
        egograph centered around the Belfast Group; groupsheet-model:
        alternate network graph based on the Group sheets themselves
    :param output: full: node and link data; adjacency: adjacency matrix,
        used for generating chord diagram
    '''

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
                   'betweenness_centrality',
                   'eigenvector_centrality'])

    if output == 'full':
        data = json_graph.node_link_data(graph)
    if output == 'adjacency':
        # adjacency matrix for generating chord diagram
        matrix = nx.convert_matrix.to_numpy_matrix(graph)

        # NOTE: this also works, but as of networx 1.9 requires scipy
        # matrix = nx.linalg.graphmatrix.adjacency_matrix(graph)
        data = matrix.tolist()

    return HttpResponse(json.dumps(data), content_type='application/json')


@last_modified(rdf_nx_lastmod)
def node_info(request):
    '''Return an HTML snippet with brief information about a node in the
    network (e.g., name, number of Group sheets, link to profile page
    if there is one).  Intended to be called via AJAX and displayed with
    the network graphs.

    Expects a url parameter ``id`` with the node identifier.
    '''
    node_id = request.GET.get('id', None)
    # if no id is specified, 404
    if node_id is None:
        raise Http404
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
    '''Display a map of places associated with the people connected to the
    Belfast Group or mentioned in the digitized Group sheets on the site.

    If a :class:`~django.contrib.flatpages.models.FlatPage` is found for
    this url, it is passed to the template to include in display.
    '''

    fpage = get_flatpage(request)
    api_key = settings.GOOGLE_MAPS_API_KEY
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

    return render(
        request,
        'network/map.html',
        {
            'people': people,
            'flatpage': fpage,
            'api_key': api_key
        }
    )


@last_modified(rdf_lastmod)
def map_js(request):
    '''Location data for places associated with the people connected to the
    Belfast Group or mentioned in the digitized Group sheets on the site,
    returned as JSON for use with :meth:`map`.
    '''
    places = find_places()
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

        # flag to indicate the type of icon that should be used on the map
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
            'icon': icon

        }
        markers.append(info)

    map_data = {'markers': markers}
    return HttpResponse(json.dumps(map_data), content_type='application/json')

