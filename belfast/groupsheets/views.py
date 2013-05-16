from django.shortcuts import render
from django.http import Http404
from eulexistdb.exceptions import DoesNotExist

from belfast.groupsheets.models import GroupSheet


def view_sheet(request, id):
    try:
        gs = GroupSheet.objects.get(id=id)
    except DoesNotExist:
        raise Http404
    return render(request, 'groupsheets/display.html',
                 {'document': gs})
