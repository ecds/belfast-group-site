from django.db.models import Count
from django.shortcuts import render
from django.http import Http404, HttpResponse
from django.views.decorators.http import last_modified
from eulexistdb.exceptions import DoesNotExist, ExistDBException
import logging

from belfast import rdfns
from belfast.groupsheets.forms import KeywordSearchForm
from belfast.groupsheets.models import GroupSheet
from belfast.groupsheets.rdfmodels import TeiGroupSheet, get_rdf_groupsheets, \
    TeiDocument
from belfast.people.models import Person
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

    context.update({'document': gs,
                   'page_rdf_url': getattr(gs, 'ark', None)})
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


# TODO: based on db, how to calculate?
#@last_modified(rdf_lastmod)  # for now, list is based on rdf
def list(request):
    results = GroupSheet.objects.all()

    # FIXME: naming to differentiate filters from facets
    digital = request.GET.get('edition', None)
    if digital is not None:
        results = results.filter(url__isnull=False)

    author = request.GET.get('author', None)
    if author is not None:
        results = results.filter(author__slug=author)

    results = results.order_by('author__last_name').all()

    # FIXME: combinations of facets?
    digital_count = None
    if digital is None:
        gs = GroupSheet.objects.all()
        if author is not None:
            gs = gs.filter(author__slug=author)

        digital_count = gs.filter(url__isnull=False).count()

    # probably shouldn't display if digital count == total displayed count

    authors = None
    if author is None:
        authors = Person.objects.all()
        if digital is not None:
            authors = authors.filter(groupsheet__url__isnull=False)

        authors = authors.annotate(total_groupsheets=Count('groupsheet')) \
                         .filter(total_groupsheets__gte=1) \
                         .order_by('-total_groupsheets')

    # TODO: archival collection source ?

    # FIXME: make facets empty dict to indicate nothing to show?
    facets = {'digital': digital_count, 'authors': authors}

    return render(request, 'groupsheets/list.html',
                  {'documents': results, 'facets': facets})


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
