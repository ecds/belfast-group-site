from django.shortcuts import render
from belfast.people.models import ProfilePicture
from belfast.people.rdfmodels import profile_people

# NOTE: last-modified would be good here, but probably should be based
# on profile picture modification dates, which is not currently stored

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
