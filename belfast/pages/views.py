# Create your views here.
from django.shortcuts import render
from belfast.people.models import ProfilePicture

def site_index(request):
    pictures = ProfilePicture.objects.all().order_by('?')  # random order
    return render(request, 'pages/site_index.html',
                  {'pictures': pictures})
