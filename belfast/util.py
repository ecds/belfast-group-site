from datetime import datetime
import rdflib
import logging
import os
import re
from networkx.readwrite import gexf

from django.conf import settings

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
        _NX_GRAPH = gexf.read_gexf(settings.GEXF_DATA)
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

