from belfast import __version__

def version(request):
    return {
       'SW_VERSION': __version__
    }