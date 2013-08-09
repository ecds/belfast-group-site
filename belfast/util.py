import glob
from datetime import datetime
import rdflib
import logging
import os
from os import path
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


def rdf_data():
    start = time.time()
    # FIXME: should graph ident be configured in settings or similar?
    # load rdf data for the site from database
    ident = rdflib.URIRef('http://belfastgroup.ecds.emory.edu/')
    datastore = rdflib.plugin.get("SQLAlchemy", rdflib.store.Store)(identifier=ident)
    graph = rdflib.Graph(datastore, identifier=ident)
    graph.open(rdf_dburi_from_settings())
    logger.debug('Opened RDF graph from db in %.02f sec' % \
                 (time.time() - start))
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
