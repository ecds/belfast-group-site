import glob
import rdflib
import logging
from os import path
import time

from django.conf import settings

logger = logging.getLogger(__name__)

_RDF_GRAPH = None


def rdf_data():
    global _RDF_GRAPH
    if _RDF_GRAPH is None:
        start = time.time()

        g = rdflib.Graph()
        filecount = 0
        # TODO: log time it takes to parse and load, totalnumber of files
        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*.xml')):
            g.parse(infile)
            filecount += 1

        for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*', '*.rdf')):
            g.parse(infile)
            filecount += 1

        logger.debug('Loaded %d RDF documents in %.02f sec' % (filecount,
                     time.time() - start))

        _RDF_GRAPH = g

    return _RDF_GRAPH
    # load related info (viaf, dbpedia, geonames)
    # for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, 'viaf/*.rdf')):
    #     g.parse(infile)
