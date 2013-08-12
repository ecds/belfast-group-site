from django.db.models import Count
from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
from eulexistdb.exceptions import DoesNotExist, ExistDBException
import logging
import urllib

from belfast import rdfns
from belfast.groupsheets.forms import KeywordSearchForm
from belfast.groupsheets.models import GroupSheet, ArchivalCollection
from belfast.groupsheets.rdfmodels import TeiGroupSheet, TeiDocument
from belfast.util import rdf_data_lastmodified, network_data_lastmodified

logger = logging.getLogger(__name__)


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())

# TODO: add etag/last-modified headers for views based on single-document TEI
# use document last-modification date in eXist (should be similar to findingaids code)

def view_sheet(request, id):
    context = {
        'extra_ns': {'bg': rdfns.BG},
        'page_rdf_type': 'bg:GroupSheet'
    }
    try:
        gs = TeiGroupSheet.objects.also('ark_list',
                                     'document_name') \
                               .get(id=id)
    except DoesNotExist:
        raise Http404

    sources = ArchivalCollection.objects.filter(groupsheet__tei_id=id)

    context.update({'document': gs,
                   'page_rdf_url': getattr(gs, 'ark', None),
                   'sources': sources})
    return render(request, 'groupsheets/display.html', context)


# TODO: throughout, would be good to use etag & last-modified headers


def teixml(request, name):
    """Display the full TEI XML content for digitized groupsheets.

    :param name: name of the document to be displayed
    """
    try:
        doc = TeiDocument.objects.get(document_name=name)
    except DoesNotExist:
        raise Http404
    tei_xml = doc.serialize(pretty=True)
    return HttpResponse(tei_xml, mimetype='application/xml')


# TODO: based on db, how to calculate last modified?
#@last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    # without filters, find all group sheets
    results = GroupSheet.objects.all()

    url_args = {}
    filter_digital = request.GET.get('edition', None)
    if filter_digital is not None:
        results = results.filter(url__isnull=False)
        url_args['edition'] = 'digital'

    filter_author = request.GET.get('author', None)
    if filter_author is not None:
        results = results.filter(author__slug=filter_author)
        url_args['author'] = filter_author

    filter_source = request.GET.get('source', None)
    if filter_source is not None:
        results = results.filter(sources__name=filter_source)
        url_args['source'] = filter_source

    results = results.order_by('author__last_name').all()

    # generate labels/totals for 'facet' filters
    digital_count = None
    # if not already filtered on digital, get a count
    if filter_digital is None:
        # use the already filtered group sheet query from above
        digital_count = results.filter(url__isnull=False).count()

    # filter to group sheets by author
    authors = None
    if filter_author is None:
        # find authors and calculate totals relative to filtered groupsheets we'll return
        # NOTE: should use distinct here, but apparently it's not supported on mysql
        gsauth = results.only('author').annotate(total_groupsheets=Count('author__groupsheet')) \
                        .filter(total_groupsheets__gte=1) \
                        .order_by('-total_groupsheets', 'author')
        # generate a list of tuples: author, total
        authors = []
        last = None
        for auth in gsauth:
            # if the same as the previous, skip
            if auth.author == last:
                continue
            last = auth.author
            authors.append((auth.author, auth.total_groupsheets))

    # filter to group sheets by source
    sources = None
    if filter_source is None:
        # can't find relative to filtered groupsheet b/c rel is many-to-many
        sources = ArchivalCollection.objects.all()
        # filter based on other facets that are set
        if filter_digital:
            sources = sources.filter(groupsheet__url__isnull=False)
        if filter_author:
            sources = sources.filter(groupsheet__author__slug=filter_author)

        sources = sources.annotate(total_groupsheets=Count('groupsheet')) \
                                 .filter(total_groupsheets__gte=1) \
                                 .order_by('-total_groupsheets')

    # FIXME: make facets empty dict to indicate nothing to show?
    facets = {'digital': digital_count, 'authors': authors, 'sources': sources}
    url_suffix = urllib.urlencode(url_args)
    # if not empty, prepend & for easy combination with other url args
    if url_suffix != '':
        url_suffix = '&%s' % url_suffix

    # generate query args to remove individual filters
    filters = {}
    if filter_digital is not None:
        args = url_args.copy()
        del args['edition']
        filters['digital edition'] = '?' + urllib.urlencode(args)
    if filter_author is not None:
        args = url_args.copy()
        del args['author']
        filters[results[0].author.name] = '?' + urllib.urlencode(args)
    if filter_source is not None:
        args = url_args.copy()
        del args['source']
        filters[filter_source] = '?' + urllib.urlencode(args)

    return render(request, 'groupsheets/list.html',
                  {'documents': results, 'facets': facets,
                   'url_suffix': url_suffix, 'filters': filters})


def search(request):
    form = KeywordSearchForm(request.GET)

    context = {'form': form, 'page_rdf_type': 'schema:SearchResultsPage'}
    if form.is_valid():
        keywords = form.cleaned_data['keywords']
        # pagination todo (?)
        # page = request.REQUEST.get('page', 1)

        try:
            results = TeiGroupSheet.objects \
                                .filter(fulltext_terms=keywords) \
                                .order_by('-fulltext_score') \
                                .also('fulltext_score')
            context.update({'documents': results, 'keywords': keywords})
            # calculate total to trigger exist query so error can be caught
            results.count()
        except ExistDBException as err:
            logger.error('eXist query error: %s' % err)
            context['query_error'] = True

    return render(request, 'groupsheets/search_results.html',
                  context)
