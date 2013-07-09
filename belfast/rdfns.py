import rdflib

# RDF namespaces for use throughout the site

ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
DBPEDIA_OWL = rdflib.Namespace('http://dbpedia.org/ontology/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
GN = rdflib.Namespace('http://www.geonames.org/ontology#')
DBPPROP = rdflib.Namespace('http://dbpedia.org/property/')
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

# local belfast group ontology
BG = rdflib.Namespace('http://belfastgroup.library.emory.edu/ontologies/2013/6/belfastgroup/#')

# not strictly a namespace, but needs to be shared...
BELFAST_GROUP_URI = 'http://viaf.org/viaf/123393054'
BELFAST_GROUP_URIREF = rdflib.URIRef(BELFAST_GROUP_URI)
