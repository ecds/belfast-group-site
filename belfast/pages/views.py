# Create your views here.
from django.shortcuts import render

def site_index(request):
    return render(request, 'pages/site_index.html')
