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
        # TODO: log time it takes to parse and load, totalnumber of files
        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*.xml')):
            graph.parse(infile)
            filecount += 1

        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*', '*.rdf')):
            graph.parse(infile)
            filecount += 1

        logger.debug('Loaded %d RDF documents in %.02f sec' % (filecount,
                     time.time() - start))

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

