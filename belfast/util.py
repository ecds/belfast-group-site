from datetime import datetime
import rdflib
import logging
import os
import re
from urlparse import urlparse

from networkx.readwrite import gexf

from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site, get_current_site


logger = logging.getLogger(__name__)


# TODO: consolidate with version somewhere in belfast.rdf
def normalize_whitespace(str):
    return re.sub(r'\s+', ' ', str.strip())

_rdf_data = None

def rdf_data():
    global _rdf_data
    # TODO: check if there is a way to open this read-only?
    # only requires read access for normal site operation
    if _rdf_data is None:
        # method to get a copy of the conjunctive graph with rdf data for the site
        _rdf_data = rdflib.ConjunctiveGraph('Sleepycat')
        _rdf_data.open(settings.RDF_DATABASE)
    return _rdf_data


def local_uri(path, request=None):
    '''Utility method to generate an absolute path for a local URI based
    on the current Site.'''
    # NOTE: should possibly be in belfast.rdf.util or similar

    if request is not None:
        current_site = get_current_site(request)
    else:
        current_site = Site.objects.get(id=settings.SITE_ID)

    # If django is configured to run under a non-root url, reverse
    # will include that path when generating urls.  Make sure we don't
    # duplicate that portion of the path
    base_url = 'http://%s' % (current_site.domain)
    parsed_url = urlparse(base_url)
    if parsed_url.path and path.startswith(parsed_url.path):
        path = path[len(parsed_url.path):]

    return 'http://%s/%s' % (current_site.domain.rstrip('/'), path.lstrip('/'))


# TODO: determine how to generate last-modified dates for refactored RDF
# handling within the site
# NOTE: the methods below are probably out of date

def rdf_data_lastmodified():
    # get a last modification time for rdf data, based on the
    # most recently modified file
    # TODO: store date last looded in the database instead?
    filelist = os.listdir(settings.RDF_DATA_DIR)
    filelist = filter(lambda x: not os.path.isdir(x) and x.endswith('.xml'), filelist)
    newest = max([os.stat(os.path.join(settings.RDF_DATA_DIR, x)).st_mtime for x in filelist])
    return datetime.fromtimestamp(newest)

def network_data_lastmodified():
    # last modification time for nx network data, based on the gexf file
    return datetime.fromtimestamp(os.stat(settings.GEXF_DATA).st_mtime)


_NX_GRAPH = None

def network_data():
    global _NX_GRAPH
    if _NX_GRAPH is None:
        _NX_GRAPH = gexf.read_gexf(settings.GEXF_DATA['full'])
    return _NX_GRAPH


class cached_property(object):
    '''A read-only @property that is only evaluated once. The value is cached
    on the object itself rather than the function or class; this should prevent
    memory leakage.'''
    # from http://www.toofishes.net/blog/python-cached-property-decorator/
    def __init__(self, fget, doc=None):
        self.fget = fget
        self.__doc__ = doc or fget.__doc__
        self.__name__ = fget.__name__
        self.__module__ = fget.__module__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        obj.__dict__[self.__name__] = result = self.fget(obj)
        return result


def relative_flatpage_url(request):
    # generate the relative url for a flatpage, taking into account subdomain
    current_site = get_current_site(request)
    url = request.path
    # if running on a subdomain, search for flatpage with url without leading path
    if '/' in current_site.domain:
        parts = current_site.domain.rstrip('/').split('/')
        suburl = '/%s/' % parts[-1]
        if url.startswith(suburl):
            url = request.path[len(suburl) - 1:]  # -1 to preserve leading /
    return url

def get_flatpage(request):
    # get flatpage for this url & site if it exists; otherwise, return none
    url = relative_flatpage_url(request)
    try:
        return FlatPage.objects.get(url=url, sites__id=settings.SITE_ID)
    except FlatPage.DoesNotExist:
        return None


