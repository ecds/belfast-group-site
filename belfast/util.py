import glob
import rdflib
import logging
from os import path
import time
import networkx as nx
from networkx.readwrite import gexf

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def rdf_data():
    cache_key = 'BELFAST_RDF_GRAPH'
    timeout = 60 * 60 * 24
    graph = cache.get(cache_key)
    if graph is None:
        start = time.time()

        graph = rdflib.Graph()
        filecount = 0
        errcount = 0
        # TODO: log time it takes to parse and load, totalnumber of files
        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*.xml')):
            try:
                graph.parse(infile)
                filecount += 1
            except Exception as err:
                logger.error('Failed to parse file %s: %s' % (infile, err))
                errcount += 1

        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*', '*.rdf')):
            try:
                graph.parse(infile)
                filecount += 1
            except Exception as err:
                logger.error('Failed to parse file %s: %s' % (infile, err))
                errcount += 1

        logger.debug('Loaded %d RDF documents in %.02f sec (%d errors)' % \
                     (filecount, time.time() - start, errcount))

        cache.set(cache_key, graph, timeout)

    return graph
    # load related info (viaf, dbpedia, geonames)
    # for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, 'viaf/*.rdf')):
    #     g.parse(infile)


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
