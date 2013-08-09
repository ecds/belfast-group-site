import logging
import networkx as nx
import rdflib
import re
import time

from belfast import rdfns
from belfast.util import rdf_data, network_data, cached_property

logger = logging.getLogger(__name__)



class RdfEntity(rdflib.resource.Resource):
    # base class with common functionality for person, org

    _person_type = rdflib.resource.Resource
    _org_type = rdflib.resource.Resource

    @property
    def name(self):
        # NOTE: would be better if we could use preferredLabel somehow
        return self.value(rdfns.SCHEMA_ORG.name)

    @property
    def nx_node_id(self):
        'node identifier for this person in network graphs'
        return unicode(self.identifier)

    def ego_graph(self, radius=1, types=None):
        'generate an undirected ego graph around the current person'
        # TODO: options to specify distance
        network = network_data()
        undirected_net = network.to_undirected()

        # filter network *before* generating ego graph
        # so we don't get disconnected nodes
        if types is not None:
            for n in undirected_net.nodes():
                if 'type' not in undirected_net.node[n] or \
                   undirected_net.node[n]['type'] not in types:
                    undirected_net.remove_node(n)

        # converted multidigraph to undirected
        # to make it possible to find all neighbors,
        # not just outbound connections
        # (should be a way to get this from a digraph...)
        return nx.ego_graph(undirected_net, self.nx_node_id,
                            radius=radius)

    def connections(self, rdftype=None, resource=rdflib.resource.Resource):
        '''Generate a dictionary of connected entities (direct neighbors
        in the network graph) with a list of relationship terms (edge labels).
        Optionally, takes an RDF type to filter the entities (e.g., restrict
        only to People or Organizations), and a subclass of
        :class:`rdflib.resource.Resource` to initialize the entity as.'''
        network = network_data()
        graph = rdf_data()

        if self.nx_node_id not in network.nodes():
            return {}

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
            # if an rdf type was specified, filter out items that do not
            # match that type.
            if rdftype is not None and \
               (uriref, rdflib.RDF.type, rdftype) not in graph:
                continue

            res = resource(graph, uriref)
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

            connections[res] = rels

        return connections

    @cached_property
    def connected_people(self):
        '''dictionary of people (as :class:`RdfPerson`) connected to
        this person, with a list of relationship terms indicating
        how they are connected.'''
        start = time.time()
        conn = self.connections(rdfns.SCHEMA_ORG.Person, self._person_type)
        logger.debug('Found %d people in %.02f sec' % (len(conn),
                     time.time() - start))
        return conn

    @cached_property
    def connected_organizations(self):
        '''dictionary of organizations (as :class:`RdfOrganization`)
        this person is connected to, with a list of terms indicating
        how they are connected.'''
        start = time.time()
        conn = self.connections(rdfns.SCHEMA_ORG.Organization, self._org_type)
        logger.debug('Found %d organizations in %.02f sec' % (len(conn),
                     time.time() - start))
        return conn


class RdfLocation(RdfEntity):

    @property
    def name(self):
        return self.value(rdfns.SCHEMA_ORG.name)

    def __unicode__(self):
        return self.value(rdfns.GN.name) or self.value(rdfns.DBPPROP.name) \
            or self.graph.preferredLabel(self) \
            or self.name or self.identifier

    @property
    def latitude(self):
        val = self.value(rdfns.GEO.lat)
        if val is not None:
            return float(unicode(val))

    @property
    def longitude(self):
        val = self.value(rdfns.GEO.long)
        if val is not None:
            return float(unicode(val))



class RdfOrganization(RdfEntity):
    pass


class RdfPerson(RdfEntity):
    _org_type = RdfOrganization

    @cached_property
    def dbpedia_uri(self):
        # same as
        for res in self.objects(rdflib.OWL.sameAs):
            if 'dbpedia.org' in res.identifier:
                return res.identifier

    @cached_property
    def viaf_uri(self):
        if 'viaf.org' in self.identifier:
            return unicode(self.identifier)

    @property
    def name(self):
        # NOTE: would be better if we could use preferredLabel somehow
        return self.value(rdfns.SCHEMA_ORG.name)

    name_re = re.compile('^((?P<last>[^ ]{2,}), (?P<first>[^.,( ]{2,}))[.,]?')
    _firstname = None
    _lastname = None

    def _calculate_first_last_name(self):
        for name in self.objects(rdfns.FOAF.name):
            match = self.name_re.match(unicode(name))
            if match:
                name_info = match.groupdict()
                self._firstname = name_info['first']
                self._lastname = name_info['last']
                # stop after we get the first name we can use (?)
                # note that for ciaran carson only one variant has the accent...
                break

    @property
    def lastname(self):
        if self._lastname is not None:
            return self._lastname
        val = self.value(rdfns.SCHEMA_ORG.familyName)
        if val is not None:
            return val
        self._calculate_first_last_name()
        return self._lastname


    @property
    def firstname(self):
        if self._firstname is not None:
            return self._firstname
        fname = self.value(rdfns.SCHEMA_ORG.givenName)
        if fname is not None:
            return fname
        self._calculate_first_last_name()
        return self._firstname

# (u'Carson, Ciaran Irish poet and novelist, born 1948'), rdflib.term.Literal(u'Ciaran Carson'), rdflib.term.Literal(u'Carson, Ciaran, 1948-'), rdflib.term.Literal(u'Carson, Ciaran.'), rdflib.term.Literal(u'Carson, Ciaran'), rdflib.term.Literal(u'Carson, Ciar\xe1n (1948- ).')]
# error: no first/last name for http://viaf.org/viaf/85621766 - na

        return fname

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

    @property
    def same_as(self):
        return list(self.objects(rdflib.OWL.sameAs))

    @property
    def description(self):
        'http://schema.org/description, if available'
        return self.value(rdfns.SCHEMA_ORG.description).strip()

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
        if self.dbpedia_uri is not None:
            for desc in self.graph.objects(subject=self.dbpedia_uri,
                                           predicate=rdfns.DBPEDIA_OWL.abstract):
                if desc.language == 'en':  # TODO: configurable (?)
                    return desc

    @cached_property
    def wikipedia_url(self):
        if self.dbpedia_uri is not None:
            return self.graph.value(subject=self.dbpedia_uri,
                                    predicate=rdfns.FOAF.isPrimaryTopicOf)

    # TODO: need access to groupsheets by this person


# FIXME! this is a hack; find a better way to do this...
# patch in types to return for connected persons/orgs
RdfOrganization._person_type = RdfPerson
RdfOrganization._org_type = RdfOrganization
RdfPerson._person_type = RdfPerson

# NOTE: this is forcing rdf graph load every restart
#BelfastGroup = RdfOrganization(rdf_data(), rdfns.BELFAST_GROUP_URIREF)

def BelfastGroup():
  return RdfOrganization(rdf_data(), rdfns.BELFAST_GROUP_URIREF)


# deprecated; this is slow, use BelfastGroup.connected_people instead
def get_belfast_people():
    g = rdf_data()
    # FIXME: possibly more efficient to use nx / ego graph?
    # i.e., equivalent of connected_people for RdfOrganization instance

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
               'bg': rdfns.BELFAST_GROUP_URI}
    )
    logger.debug('Found %d people in %.02f sec' % (len(res),
                 time.time() - start))

#            FILTER EXISTS {?person ?p <%(bg)s>}
# { ?book dc10:title  ?title } UNION { ?book dc11:title  ?title }
    #    ?person schema:affiliation <%s> .
    #    ?person schema:memberOf <%s> .

    people = [RdfPerson(g, r['person']) for r in res]
    return people

def find_places():
    g = rdf_data()
    return [RdfLocation(g, subj) for subj in g.subjects(predicate=rdflib.RDF.type,
                                                       object=rdfns.SCHEMA_ORG.Place)]

