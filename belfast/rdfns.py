'''RDF Namespaces used throughout the site.'''

import rdflib

# RDF namespaces for use throughout the site

#:archival vocabularly
ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
#: schema.org
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
#: dbpedia owl
DBPEDIA_OWL = rdflib.Namespace('http://dbpedia.org/ontology/')
#: dublin core
DC = rdflib.Namespace('http://purl.org/dc/terms/')
#: dcmi type
DCMITYPE = rdflib.Namespace('http://purl.org/dc/dcmitype/')
#: bibo (bibliographic)
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
#: skos
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
#: geonames
GN = rdflib.Namespace('http://www.geonames.org/ontology#')
#: DBpedia property
DBPPROP = rdflib.Namespace('http://dbpedia.org/property/')
#: FOAF
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')
#: geo
GEO = rdflib.Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')
#: freebace
FREEBASE = rdflib.Namespace('http://www.freebase.com/')

#: local belfast group ontology
BG = rdflib.Namespace('http://belfastgroup.library.emory.edu/ontologies/2013/6/belfastgroup/#')

# not strictly a namespace, but needs to be shared...
BELFAST_GROUP_URI = 'http://viaf.org/viaf/123393054'
BELFAST_GROUP_URIREF = rdflib.URIRef(BELFAST_GROUP_URI)
