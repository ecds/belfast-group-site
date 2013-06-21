import logging
import rdflib
import time

from belfast.util import rdf_data
from belfast.groupsheets.models import RdfPerson

logger = logging.getLogger(__name__)

# fixme: common
BELFAST_GROUP_URI = 'http://viaf.org/viaf/123393054/'
ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')


def get_belfast_people():
    g = rdf_data()

    start = time.time()
    # query for persons one relation removed from the belfast group
    res = g.query('''
        PREFIX schema: <%(xsd)s>
        PREFIX rdf: <%(rdf)s>
        SELECT DISTINCT ?person
        WHERE {
            {
              ?person ?rel1 <%(bg)s> .
              ?person rdf:type schema:Person
            }
            UNION
            {
              <%(bg)s> ?rel2 ?person .
              ?person rdf:type schema:Person
            }
            ?author schema:name ?name
        } ORDER BY ?name
        ''' % {'xsd': rdflib.XSD, 'rdf': rdflib.RDF,
               'bg': BELFAST_GROUP_URI}
    )
    logger.debug('Found %d people in %.02f sec' % (len(res),
                 time.time() - start))

#            FILTER EXISTS {?person ?p <%(bg)s>}
# { ?book dc10:title  ?title } UNION { ?book dc11:title  ?title }
    #    ?person schema:affiliation <%s> .
    #    ?person schema:memberOf <%s> .

    people = [RdfPerson(g, r['person']) for r in res]
    return people

