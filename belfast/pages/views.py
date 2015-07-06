from django.shortcuts import render
from django.views.decorators.http import last_modified
from belfast.people.models import ProfilePicture
from belfast.people.rdfmodels import profile_people
from belfast.util import rdf_data_lastmodified

def rdf_lastmodified(request, *args, **kwargs):
    # NOTE: last-modified would be good here, but probably should be based
    # on profile picture modification dates, which is not currently stored
    return rdf_data_lastmodified()

@last_modified(rdf_lastmodified)
def site_index(request):
    '''Site home page.  Includes a random-order list of profile pictures
    for display at the bottom of the home page.
    '''
    pictures = ProfilePicture.objects.all().order_by('?')  # random order
    # find people who have profiles on thes ite
    people = profile_people()
    # filter to only people with a description
    people = [p for p in people if p.has_profile and p.picture]

    return render(request, 'pages/site_index.html',
                  {'pictures': pictures,
                   'people': people})
