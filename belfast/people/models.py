import logging
import networkx as nx
import rdflib
import time

from belfast import rdfns
from belfast.util import rdf_data, network_data, cached_property

logger = logging.getLogger(__name__)


class RdfLocation(rdflib.resource.Resource):

    @property
    def name(self):
        return self.value(rdfns.SCHEMA_ORG.name)

    def __unicode__(self):
        return self.value(rdfns.GN.name) or self.value(rdfns.DBPPROP.name) \
            or self.graph.preferredLabel(self) \
            or self.name or self.identifier


class RdfPerson(rdflib.resource.Resource):

    @property
    def name(self):
        # NOTE: would be better if we could use preferredLabel somehown
        return self.value(rdfns.SCHEMA_ORG.name)

    @property
    def lastname(self):
        return self.value(rdfns.SCHEMA_ORG.familyName)

    @property
    def firstname(self):
        return self.value(rdfns.SCHEMA_ORG.givenName)

    @property
    def fullname(self):
        if self.lastname and self.firstname:
            return '%s %s' % (self.firstname, self.lastname)
        elif self.value(rdfns.FOAF.name):
            return self.value(rdfns.FOAF.name)
        else:
            return self.name

    @property
    def birthdate(self):
        # TODO: convert to date type
        return self.value(rdfns.SCHEMA_ORG.birthDate)

    @property
    def birthplace(self):
        place = self.value(rdfns.DBPEDIA_OWL.birthPlace)
        if place:
            return RdfLocation(self.graph, place.identifier)

    @property
    def occupation(self):
        'list of occupations via http://schema.org/jobTitle property'
        return list(self.objects(rdfns.SCHEMA_ORG.jobTitle))

    @cached_property
    def locations(self):
        place_uris = list(self.objects(rdfns.SCHEMA_ORG.workLocation))
        place_uris.extend(list(self.objects(rdfns.SCHEMA_ORG.homeLocation)))
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
        ''' % (rdflib.RDF, rdflib.OWL, rdfns.DBPEDIA_OWL,
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
            if (uriref, rdflib.RDF.type, rdfns.SCHEMA_ORG.Person) in graph:
                person = RdfPerson(graph, uriref)
                rels = set()
                # find any edges between this node and me
                # include data to simplify accessing edge label
                # use edges & labels from original multidigraph
                all_edges = network.out_edges(node, data=True) + \
                    network.in_edges(node, data=True)

                for edge in all_edges:
                    src, target, data = edge
                    if self.nx_node_id in edge and 'label' in data:
                        rels.add(data['label'])

                connections[person] = rels

        return connections

    # TODO: need access to groupsheets by this person


def get_belfast_people():
    g = rdf_data()
    # FIXME: possibly more efficient to use nx / ego graph?

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
               'bg': rdfns.BELFAST_GROUP}
    )
    logger.debug('Found %d people in %.02f sec' % (len(res),
                 time.time() - start))

#            FILTER EXISTS {?person ?p <%(bg)s>}
# { ?book dc10:title  ?title } UNION { ?book dc11:title  ?title }
    #    ?person schema:affiliation <%s> .
    #    ?person schema:memberOf <%s> .

    people = [RdfPerson(g, r['person']) for r in res]
    return people


