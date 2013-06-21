from django.shortcuts import render
from django.http import Http404
import rdflib

from belfast.people.models import get_belfast_people
from belfast.groupsheets.models import RdfPerson
from belfast.util import rdf_data


def list(request):
    # use rdf to generate a list of people one remove from belfast group
    results = get_belfast_people()
    return render(request, 'people/list.html',
                  {'people': results})


def profile(request, id):
    idtype, idnum = id.split(':')
    if idtype == 'viaf':
        uri = 'http://viaf.org/viaf/%s/' % idnum
        graph = rdf_data()
        person = RdfPerson(graph, rdflib.URIRef(uri))
    else:
        # anything else not found for now
        raise Http404

    return render(request, 'people/profile.html', {'person': person})
