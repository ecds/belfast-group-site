import rdflib

# rdf namespaces
ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')
DCMITYPE = rdflib.Namespace('http://purl.org/dc/dcmitype/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
GEO = rdflib.Namespace('http://www.w3.org/2003/01/geo/wgs84_pos#')

# local belfast group ontology
BG = rdflib.Namespace('http://belfastgroup.library.emory.edu/ontologies/2013/6/belfastgroup/#')

# not technically a namespace, but seems sensible to keep here
BELFAST_GROUP_URI = 'http://viaf.org/viaf/123393054'
