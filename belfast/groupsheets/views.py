from django.shortcuts import render
from django.http import Http404
from eulexistdb.exceptions import DoesNotExist

from belfast.groupsheets.models import GroupSheet, get_rdf_groupsheets


def view_sheet(request, id):
    try:
        gs = GroupSheet.objects.get(id=id)
    except DoesNotExist:
        raise Http404
    return render(request, 'groupsheets/display.html',
                 {'document': gs})

def list(request):
    # use rdf to generate a list of belfast group sheets
    results = get_rdf_groupsheets()
    return render(request, 'groupsheets/list.html',
        {'documents': results})