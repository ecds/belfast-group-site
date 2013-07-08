from django.shortcuts import render
from django.http import Http404, HttpResponse
from eulexistdb.exceptions import DoesNotExist, ExistDBException
import logging

from belfast.groupsheets.forms import KeywordSearchForm
from belfast.groupsheets.models import GroupSheet, get_rdf_groupsheets, \
    TeiDocument

logger = logging.getLogger(__name__)


def view_sheet(request, id):
    try:
        gs = GroupSheet.objects.also('ark_list',
                                     'document_name') \
                               .get(id=id)
    except DoesNotExist:
        raise Http404
    return render(request, 'groupsheets/display.html',
                  {'document': gs, 'page_rdf_url': getattr(gs, 'ark', None)})


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


def list(request):
    # use rdf to generate a list of belfast group sheets
    results = get_rdf_groupsheets()
    return render(request, 'groupsheets/list.html',
                  {'documents': results})


def search(request):
    form = KeywordSearchForm(request.GET)

    context = {'form': form, 'page_rdf_type': 'schema:SearchResultsPage'}
    if form.is_valid():
        keywords = form.cleaned_data['keywords']
        # pagination todo (?)
        # page = request.REQUEST.get('page', 1)

        try:
            results = GroupSheet.objects \
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
