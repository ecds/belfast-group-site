import glob
from datetime import datetime
import rdflib
import logging
import os
from os import path
import re
import time
import networkx as nx
from networkx.readwrite import gexf

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

def normalize_whitespace(str):
    return re.sub(r'\s+', ' ', str.strip())

def rdf_data_lastmodified():
    # get a last modification time for rdf data, based on the
    # most recently modified file
    # TODO: store date last looded in the database instead?
    filelist = os.listdir(settings.RDF_DATA_DIR)
    filelist = filter(lambda x: not os.path.isdir(x) and x.endswith('.xml'), filelist)
    newest = max([os.stat(os.path.join(settings.RDF_DATA_DIR, x)).st_mtime for x in filelist])
    return datetime.fromtimestamp(newest)


def rdf_dburi_from_settings():
    # generate db uri for rdflib-sqlalchemy based on django conf
    # NOTE: getting database wrapper errors, so rdf data will
    # need to be loaded into a separate db from site django content
    dbconfig = settings.DATABASES['rdf']
    if dbconfig['ENGINE'] == 'django.db.backends.sqlite3':
        return rdflib.Literal('sqlite:///%s' % dbconfig['NAME'])

    elif dbconfig['ENGINE'] == 'django.db.backends.mysql':
        # FIXME: what if django port is set to empty string for default ?
        # TODO: if port is not set, default is 3306
        return rdflib.Literal('mysql+mysqldb://%(USER)s:%(PASSWORD)s@%(HOST)s:%(PORT)s/%(NAME)s?charset=utf8' % \
                              dbconfig)

_rdf_data = None


def rdf_data():
    global _rdf_data
    if _rdf_data is not None:
        return _rdf_data

    start = time.time()
    cache_key = 'BELFAST_RDF_GRAPH'
    timeout = 60 * 60 * 24
    graph = cache.get(cache_key)
    if graph is None:

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

        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*', '*.xml')):
            try:
                graph.parse(infile)
                filecount += 1
            except Exception as err:
                logger.error('Failed to parse file %s: %s' % (infile, err))
                errcount += 1

        logger.debug('Loaded %d RDF documents in %.02f sec (%d errors)' % \
                     (filecount, time.time() - start, errcount))

        cache.set(cache_key, graph, timeout)
    else:
        logger.debug('Loaded RDF data from cache in %.02f sec' % \
                     (time.time() - start))

    _rdf_data = graph
    return graph


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
