from eulxml import xmlmap
from eulxml.xmlmap import teimap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel
import glob
import logging
import networkx as nx
import rdflib
from rdflib import collection as rdfcollection
import time
from django.conf import settings
from os import path

from belfast.util import rdf_data, network_data, cached_property

logger = logging.getLogger(__name__)


class Contents(teimap._TeiBase):
    title = xmlmap.StringField('tei:p')
    items = xmlmap.StringListField('tei:list/tei:item')


class Poem(teimap._TeiBase):
    id = xmlmap.StringField('@xml:id')    # is this the correct id to use?
    title = xmlmap.StringField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]')
    body = xmlmap.NodeField('tei:body', xmlmap.XmlObject)
    byline = xmlmap.StringField('tei:back/tei:byline')


class IdNumber(teimap._TeiBase):
    # xmlobject for idno element, to provide access to ARK urls
    type = xmlmap.StringField('@type')
    id = xmlmap.StringField('@n')
    value = xmlmap.StringField('./text()')


class GroupSheet(XmlModel):
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei': ROOT_NS,
    }

    id = xmlmap.StringField('@xml:id')
    title = xmlmap.StringField('tei:head')
    author = xmlmap.StringField('tei:docAuthor')
    date = xmlmap.StringField('tei:docDate')
    toc = xmlmap.NodeField('tei:argument', Contents)

    poems = xmlmap.NodeListField('tei:text', Poem)

    objects = Manager('//tei:text/tei:group/tei:group')
    """:class:`eulexistdb.manager.Manager` - similar to an object manager
        for django db objects, used for finding and retrieving GroupSheet objects
        in eXist.

        Configured to use *//tei:text/tei:group/tei:group* as base search path.
    """

    # ARK urls are stored in the header as idno elements with
    # an `n` attribute referencing the group id
    # Provide access to all of them so we can retrieve the appropiate one
    ark_list = xmlmap.NodeListField('ancestor::tei:TEI//tei:idno[@type="ark"]',
                                    IdNumber)

    @property
    def ark(self):
        'ARK URL for this groupsheet'
        for a in self.ark_list:
            if a.id == self.id:
                return a.value

    # TODO: it would be nice if this were a little easier to access
    # or generate; xmlmap dictfield might get part way there..
    # Possible to generate xpaths based on current object properties?


BELFAST_GROUP_URI = 'http://viaf.org/viaf/123393054/'

ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
DBPEDIA_OWL = rdflib.Namespace('http://dbpedia.org/ontology/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')
SKOS = rdflib.Namespace('http://www.w3.org/2004/02/skos/core#')
GN = rdflib.Namespace('http://www.geonames.org/ontology#')
DBPPROP = rdflib.Namespace('http://dbpedia.org/property/')
FOAF = rdflib.Namespace('http://xmlns.com/foaf/0.1/')

#rdflib.resource.Resource - takes graph, subject

# TBD: how do groupsheet and people apps share rdf models?


class RdfLocation(rdflib.resource.Resource):

    @property
    def name(self):
        return self.value(SCHEMA_ORG.name)

    def __unicode__(self):
        return self.value(GN.name) or self.value(DBPPROP.name) \
            or self.graph.preferredLabel(self) \
            or self.name or self.identifier


class RdfPerson(rdflib.resource.Resource):

    @property
    def name(self):
        # NOTE: would be better if we could use preferredLabel somehown
        return self.value(SCHEMA_ORG.name)

    @property
    def lastname(self):
        return self.value(SCHEMA_ORG.familyName)

    @property
    def firstname(self):
        return self.value(SCHEMA_ORG.givenName)

    @property
    def fullname(self):
        if self.lastname and self.firstname:
            return '%s %s' % (self.firstname, self.lastname)
        elif self.value(FOAF.name):
            return self.value(FOAF.name)
        else:
            return self.name

    @property
    def birthdate(self):
        # TODO: convert to date type
        return self.value(SCHEMA_ORG.birthDate)

    @property
    def birthplace(self):
        place = self.value(DBPEDIA_OWL.birthPlace)
        if place:
            return RdfLocation(self.graph, place.identifier)

    @property
    def occupation(self):
        'list of occupations via http://schema.org/jobTitle property'
        return list(self.objects(SCHEMA_ORG.jobTitle))

    @cached_property
    def locations(self):
        place_uris = list(self.objects(SCHEMA_ORG.workLocation))
        place_uris.extend(list(self.objects(SCHEMA_ORG.homeLocation)))
        place_uris = set(p.identifier for p in place_uris)
        return [RdfLocation(self.graph, p) for p in place_uris]

    @cached_property
    def short_id(self):
        uri = unicode(self)
        baseid = uri.rstrip('/').split('/')[-1]
        if 'viaf.org' in uri:
            idtype = 'viaf'
        elif 'dbpedia.org' in uri:
            idtype = 'dbpedia'
        return '%s:%s' % (idtype, baseid)

    @cached_property
    def dbpedia_description(self):
        # TODO: grab same-as URIs at init so we can query directly (?)
        # FIXME: why are these not returning any matches?
        # print 'same as rels = ', list(self.objects(rdflib.OWL.sameAs))
        # print 'same as rels = ', list(self.graph.objects(self.identifier.rstrip('/'),
        #     rdflib.OWL.sameAs))
        res = self.graph.query('''
            PREFIX rdf: <%s>
            PREFIX owl: <%s>
            PREFIX dbpedia-owl: <%s>
            SELECT ?abstract
            WHERE {
                <%s> owl:sameAs ?dbp .
                ?dbp dbpedia-owl:abstract ?abstract
                FILTER langMatches( lang(?abstract), "EN" )
            }
        ''' % (rdflib.RDF, rdflib.OWL, DBPEDIA_OWL,
               self.identifier.rstrip('/'))
        )
        # FIXME: discrepancy in VIAF uris - RDF has no trailing slash

        # TODO: filter by language
        for r in res:
            return r['abstract']

    @property
    def nx_node_id(self):
        'node identifier for this person in network graphs'
        return unicode(self.identifier)

    def ego_graph(self):
        'generate an indirected ego graph around the current person'
        # TODO: options to specify distance
        network = network_data()
        undirected_net = network.to_undirected()
        # converted multidigraph to undirected
        # to make it possible to find all neighbors,
        # not just outbound connections
        # (should be a way to get this from a digraph...)
        return nx.ego_graph(undirected_net, self.nx_node_id)

    @cached_property
    def connected_people(self):
        # generate a dictionary of connected people and list of
        # how this person is related to them
        network = network_data()
        graph = rdf_data()
        # this also works...
        # neighbors = network.neighbors(self.nx_node_id)
        ego_graph = self.ego_graph()
        neighbors = ego_graph.nodes()

        connections = {}
        for node in neighbors:
            # don't include the current person in their own connections
            if node == self.nx_node_id:
                continue

            uriref = rdflib.URIRef(node)
            # TODO: probably want something similar for organizations
            if (uriref, rdflib.RDF.type, SCHEMA_ORG.Person) in graph:
                person = RdfPerson(graph, uriref)
                rels = set()
                # find any edges between this node and me
                # include data to simplify accessing edge label
                # use edges & labels from original multidigraph
                all_edges = network.out_edges(node, data=True) + \
                    network.in_edges(node, data=True)

                for edge in all_edges:
                    src, target, data = edge
                    if node_id in edge and 'label' in data:
                        rels.add(data['label'])

                connections[person] = rels

        return connections

    # TODO: need access to groupsheets by this person


class RdfGroupSheet(rdflib.resource.Resource):

    # simple single-value properties

    @property
    def date(self):
        return self.value(DC.date)

    @property
    def num_pages(self):
        return self.value(BIBO.numPages)

    @property
    def genre(self):
        return self.value(SCHEMA_ORG.genre)

    # more complex properties: aggregate, other resources

    @property
    def author(self):
        author_uri = self.value(DC.creator) or \
            self.value(SCHEMA_ORG.author)

        if author_uri is not None:
            # returns an rdflib Resource, so use identifier to re-init
            # TODO: see if there is a way to auto-init as rdfperson obj
            pers = RdfPerson(self.graph, author_uri.identifier)
            return pers

    @property
    def titles(self):
        titles = []
        # title is either a single literal OR an rdf sequence
        if self.value(DC.title) is not None:
            title = self.value(DC.title)
            # single literal
            if isinstance(title, rdflib.Literal):
                titles.append(title)

            # otherwise, assuming node is an rdf sequence
            else:
                # convert from resource to standard blank node
                # since collection doesn't seem to handle resource
                bnode = rdflib.BNode(title)
                # create a collection to allow treating as a list
                titles.extend(rdfcollection.Collection(self.graph,
                                                       bnode))
        return titles

    @property
    def sources(self):
        sources = []
        # TODO: convert into dict with name & access uri
        for coll in self.graph.subjects(SCHEMA_ORG.mentions, self.identifier):
            if (coll, rdflib.RDF.type, ARCH.Collection) in self.graph:
                name = self.graph.value(coll, SCHEMA_ORG.name)
                sources.append(name)  # title/name ?
            else:
                # NOTE: may want to use transitive subjects here (?)
                # FIXME: https: vs http: uri may be an issue!
                for pcoll in self.graph.subjects(DC.hasPart, coll):
                    # ugh, why so complicated!
                    # this is finding the *document* that describes the collection
                    # but is not itself a collection
                    if (pcoll, rdflib.RDF.type, ARCH.Collection) in self.graph  \
                       or (pcoll, rdflib.RDF.type, SCHEMA_ORG.WebPage):
                        # FIXME: need to check webpage that is ABOUT a collection
                        name = self.graph.value(pcoll, SCHEMA_ORG.name).strip()
                        sources.append(name)  # title/name ?

                    # FIXME: getting two versions of longley with different
                    # whitespace, one as bnode and one with ark url
        return sources


def get_rdf_groupsheets():
    g = rdf_data()
    res = g.query('''
        PREFIX schema: <%s>
        PREFIX rdf: <%s>
        PREFIX bibo: <%s>
        PREFIX skos: <%s>
        SELECT DISTINCT ?ms ?author
        WHERE {
            ?doc schema:about <%s> .
            ?doc schema:mentions ?ms .
            ?ms rdf:type bibo:Manuscript .
            ?ms schema:author ?author .
            ?author schema:name ?name
        } ORDER BY ?name
        ''' % (rdflib.XSD, rdflib.RDF, BIBO, SKOS, BELFAST_GROUP_URI)
    )

    # } ORDER BY ?authorLast
    # FIXME:  only QUB has schema:familyName so that query restricts to them
    # TODO: clean up data so we have lastnames for all authors

    # skos:prefLabel is in VIAF data but not directly related to viaf entity

    # FIXME: restricting to ms with author loses one anonymous sheet
    # how to filter out non-group sheet irish misc content?
    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs

