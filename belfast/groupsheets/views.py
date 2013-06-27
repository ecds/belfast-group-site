from django.shortcuts import render
from django.http import Http404
from eulexistdb.exceptions import DoesNotExist, ExistDBException
import logging

from belfast.groupsheets.forms import KeywordSearchForm
from belfast.groupsheets.models import GroupSheet, get_rdf_groupsheets

logger = logging.getLogger(__name__)


def view_sheet(request, id):
    try:
        gs = GroupSheet.objects.also('ark_list').get(id=id)
    except DoesNotExist:
        raise Http404
    return render(request, 'groupsheets/display.html',
                  {'document': gs})


def list(request):
    # use rdf to generate a list of belfast group sheets
    results = get_rdf_groupsheets()
    return render(request, 'groupsheets/list.html',
                  {'documents': results})


def search(request):
    form = KeywordSearchForm(request.GET)

    context = {'form': form}
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
