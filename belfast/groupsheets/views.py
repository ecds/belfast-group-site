from collections import defaultdict
from django.core.urlresolvers import reverse
from django.db.models import Count
from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
from django.contrib.sites.models import get_current_site
from eulexistdb.exceptions import DoesNotExist, ExistDBException
import logging
import urllib

from belfast import rdfns
from belfast.groupsheets.forms import KeywordSearchForm
from belfast.groupsheets.rdfmodels import TeiGroupSheet, TeiDocument, \
    get_rdf_groupsheets, groupsheet_by_url
from belfast.util import rdf_data_lastmodified, network_data_lastmodified, \
    local_uri

logger = logging.getLogger(__name__)


def rdf_lastmod(request, *args, **kwargs):
    return rdf_data_lastmodified()


def rdf_nx_lastmod(request, *args, **kwargs):
    return max(rdf_data_lastmodified(), network_data_lastmodified())

# TODO: add etag/last-modified headers for views based on single-document TEI
# use document last-modification date in eXist (should be similar to findingaids code)

def view_sheet(request, id):
    context = {
        'extra_ns': {'bg': rdfns.BG, 'freebase': rdfns.FREEBASE},
        'page_rdf_type': 'bg:GroupSheet'
    }
    try:
        gs = TeiGroupSheet.objects.also('ark_list',
                                     'document_name') \
                               .get(id=id)
    except DoesNotExist:
        raise Http404

    # find the related rdf groupsheet object(s)
    # so we can display & link to sources
    rdfgs = groupsheet_by_url(gs.ark)  # todo: associate with tei or rdf gs model
    sources = [s for r in rdfgs for s in r.sources]

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
def list_groupsheets(request):
    # without filters, find all group sheets
    # results = GroupSheet.objects.all()
    url_args = {}
    filters = {}
    filter_digital = request.GET.get('edition', None)
    if filter_digital is not None:
        filters['has_url'] = True
        url_args['edition'] = 'digital'

    filter_author = request.GET.get('author', None)
    if filter_author is not None:
        # filter is in slug form; use that to build local uri
        url_args['author'] = filter_author
        author_uri = local_uri(reverse('people:profile', args=[filter_author]),
                               request)
        filters['author'] = author_uri

    filter_source = request.GET.get('source', None)
    if filter_source is not None:
        url_args['source'] = filter_source
        # TODO: preferred label / slugs / local identifier for these?
        # currently arg is the uri
        filters['source'] = filter_source

    filter_time = request.GET.get('dates', None)
    if filter_time is not None:
        url_args['dates'] = filter_time
        filters['coverage'] = filter_time

    results = get_rdf_groupsheets(**filters)
    # TODO: support source filter; make more django-like

    # generate labels/totals for 'facet' filters
    digital_count = 0
    authors = defaultdict(int)
    sources = defaultdict(int)
    time_periods = defaultdict(int)
    for r in results:
       # if not already filtered on digital, get a count
        if filter_digital is None and r.url:
            digital_count += 1
        if filter_author is None:
            # use author list to ensure *all* authors are listed properly
            for author in r.author_list:
                authors[author] += 1
        if filter_source is None:
            for s in r.sources:
                sources[s] +=1
        if filter_time is None:
            time_periods[r.coverage] += 1

    # generate lists of dicts for easy sorting in django template
    authors = [{'author': k, 'total': v} for k, v in authors.iteritems()]
    sources = [{'source': k, 'total': v} for k, v in sources.iteritems()]
    time_periods = [{'time_period': k, 'total': v} for k, v in time_periods.iteritems()]

    facets = {'digital': digital_count, 'authors': authors, 'sources': sources,
              'time_periods': time_periods}

    url_suffix = ''
    url_suffix = urllib.urlencode(url_args)
    # if not empty, prepend & for easy combination with other url args
    if url_suffix != '':
        url_suffix = '&%s' % url_suffix

    # generate query args to remove individual filters
    filters = {}
    if filter_digital is not None:
        args = url_args.copy()
        del args['edition']
        filter_args = urllib.urlencode(args)
        filters['digital edition'] = '?' + (filter_args if filter_args else '')
    if filter_author is not None:
        args = url_args.copy()
        del args['author']
        # pull author display name from results
        # TODO: init rdfperson and use that label instead?
        if results:
            for a in results[0].author_list:
                # groupsheets may have multiple authors, so make sure
                # we get the correct label for the active filter
                if str(a.identifier) == author_uri:
                    filters[a.name] = '?' + urllib.urlencode(args)
                    break

    if filter_source is not None:
        args = url_args.copy()
        del args['source']
        if results:
            # pull source name from results (TODO: shorter labels)
            for s in results[0].sources:
                # groupsheets may have multiple sources, so make sure
                # we get the correct label
                if str(s.identifier) == filter_source:
                    filters[s.name] = '?' + urllib.urlencode(args)
                    break

    if filter_time is not None:
        args = url_args.copy()
        del args['dates']
        filters[filter_time] = '?' + urllib.urlencode(args)


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
