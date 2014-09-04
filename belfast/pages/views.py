# Create your views here.
from django.shortcuts import render
from belfast.people.models import ProfilePicture

def site_index(request):
    '''Site home page.  Includes a random-order list of profile pictures
    for display at the bottom of the home page.
    '''
    pictures = ProfilePicture.objects.all().order_by('?')  # random order
    return render(request, 'pages/site_index.html',
                  {'pictures': pictures})
