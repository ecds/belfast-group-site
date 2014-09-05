import logging
import networkx as nx
import rdflib
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import get_model

from belfast import rdfns
from belfast.rdf import rdfmap
from belfast.rdf.models import RdfResource
from belfast.util import rdf_data, network_data, cached_property
from belfast.network.util import filter_graph

logger = logging.getLogger(__name__)


class RdfEntity(RdfResource):
    '''Base :class:`belftas.rdf.models.RdfResource` class with common
    functionality for :class:`RdfPerson` and :class:`RdfOrganization`.'''

    _person_type = rdflib.resource.Resource
    _org_type = rdflib.resource.Resource

    @property
    def nx_node_id(self):
        'node identifier for this person in network graphs'
        return unicode(self.identifier)

    def ego_graph(self, radius=1, types=None, min_degree=None):
        '''Generate an undirected ego graph around the current entity.

        :param radius: radius or degree of the ego graph; defaults to 1
        :param types: node types to be included in the graph (e.g., restrict
            to people and organizations only)
        :param min_degree: optionally filter nodes in the generated ego graph
            by minimum degree
        '''
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

        eg = nx.ego_graph(undirected_net, self.nx_node_id,
                            radius=radius)
        if min_degree is not None:
            return filter_graph(eg, min_degree=min_degree)
        return eg

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
            weight = 0
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
                    weight += data.get('weight', 1)  # assume default of 1 if not set
                    rels.add(data['label'])

            if 'knows' in rels and 'correspondedWith' in rels:
                rels.remove('knows')

            # connections[res] = {'rels': rels, 'weight': weight}
            connections[res] = (rels, weight)

        # sort by weight so strongest connections will be listed first
        conn =  sorted(connections.items(), key=lambda x: x[1][1], reverse=True)
        return conn

    @cached_property
    def connected_people(self):
        '''List of tuples of people (as :class:`RdfPerson`) connected to
        this person, with an associated tuple containing a list of
        relationship terms indicating how they are connected and the
        cumulative weight of the connection, sorted by strongest connection.'''
        start = time.time()
        conn = self.connections(rdfns.SCHEMA_ORG.Person, self._person_type)
        logger.debug('Found %d people in %.02f sec',
                     len(conn), time.time() - start)
        return conn

    @cached_property
    def connected_organizations(self):
        '''List of tuples of organizations (as :class:`RdfOrganization`)
        this person is connected to, with an associated tuple with a list
        of terms indicating how they are connected and the weight of the connection,
        sorted by strongest connection.'''
        start = time.time()
        conn = self.connections(rdfns.SCHEMA_ORG.Organization, self._org_type)
        logger.debug('Found %d organizations in %.02f sec',
                     len(conn), time.time() - start)
        return conn


class RdfLocation(RdfEntity):
    '''RDF location'''

    #: name
    name = rdfmap.Value(rdfns.SCHEMA_ORG.name)
    #: geonames name
    geonames_name = rdfmap.Value(rdfns.GN.name)
    #: dbpedia name
    dbpedia_name = rdfmap.Value(rdfns.DBPPROP.name)
    #: latitude
    latitude = rdfmap.Value(rdfns.GEO.lat, rdflib.XSD.double)
    #: longitude
    longitude = rdfmap.Value(rdfns.GEO.long, rdflib.XSD.double)

    # property to get preferred label value inherited from base rdf model class

    def __unicode__(self):
        return self.geonames_name \
            or self.preferred_label \
            or self.dbpedia_name \
            or self.name or self.identifier

    # text/poem
    mentioned_in = rdfmap.ResourceList(rdfns.SCHEMA_ORG.mentions, RdfEntity, is_object=False)

    @property
    def texts(self):
        'list of poems that mention this location'
        return [RdfPoem(res.graph, res.identifier)
                for res in self.mentioned_in
                if rdfns.FREEBASE['book/poem'] in res.rdf_types]

    # current types of locations we support
    #: list of persons who were born here
    born_here = rdfmap.ResourceList(rdfns.DBPEDIA_OWL.birthPlace, RdfEntity, is_object=False)
    #: list of persons who worked here
    worked_here = rdfmap.ResourceList(rdfns.SCHEMA_ORG.workLocation, RdfEntity, is_object=False)
    #: list of persons who resided here
    home_here = rdfmap.ResourceList(rdfns.SCHEMA_ORG.homeLocation, RdfEntity, is_object=False)

    @property
    def people(self):
        '''List of :class:`RdfPerson` connected to this location.'''
        # NOTE: this seems clunky, but seems to be significantly faster than
        # getting the same data via sparql query
        return [RdfPerson(self.graph, r.identifier)
                for r in set(self.born_here + self.worked_here + self.home_here)]


class DBpediaEntity(RdfEntity):
    '''Convenience object for a dbpedia resource'''

    #: description (owl:abstract)
    description = rdfmap.Value(rdfns.DBPEDIA_OWL.abstract)     # FIXME: how to specify language?
    #: wikipedia url (via foaf:isPrimaryTopicOf)
    wikipedia_url = rdfmap.Value(rdfns.FOAF.isPrimaryTopicOf)
    #: thumbnail image (owl:thumbnail)
    thumbnail = rdfmap.Value(rdfns.DBPEDIA_OWL.thumbnail)


class RdfOrganization(RdfEntity):
    ''':class:`RdfEntity` for an organization.'''

    # FIXME: copied from rdfperson; move somewhere common
    #: list of other URIs that are equilvaent to this one
    same_as = rdfmap.ValueList(rdflib.OWL.sameAs, transitive=True)

    @property
    def viaf_uri(self):
        'VIAF URi for this organization'
        for uri in self.same_as:
            if 'viaf.org' in uri:
                return uri

    @property
    def dbpedia_uri(self):
        'DBpedia URI for this organization'
        for uri in self.same_as:
            if 'dbpedia.org' in uri:
                return uri

    @property
    def dbpedia(self):
        ':class:`DBpediaEntity` for this organization'
        if self.dbpedia_uri is not None:
            return DBpediaEntity(self.graph, self.dbpedia_uri)


class RdfPerson(RdfEntity):
    ''':class:`RdfEntity` for a person.'''
    _org_type = RdfOrganization

    @property
    def slug(self):
        'slug identifier used for persons with local profiles'
        # all persons with profiles should have local, slug-based uris
        return self.identifier.strip('/').split('/')[-1]

    _current_site = None
    @property
    def current_site(self):
        if self._current_site is None:
            self._current_site = Site.objects.get(id=settings.SITE_ID)
        return self._current_site

    @property
    def local_uri(self):
        'local site URI for the person'
        return str(self.identifier).startswith('http://%s' % self.current_site.domain)

    # NOTE: group sheet authors and other people with profiles on this site
    # should have first/last names added to the rdf data by the dataprep process

    #: last name (schema.org/familyName)
    lastname = rdfmap.Value(rdfns.SCHEMA_ORG.familyName)
    #: first name (schema.org/givenName)
    firstname = rdfmap.Value(rdfns.SCHEMA_ORG.givenName)

    @property
    def fullname(self):
        'fullname (constructed from first and last names if available)'
        if self.lastname and self.firstname:
            return '%s %s' % (self.firstname, self.lastname)
        elif self.value(rdfns.FOAF.name):
            return self.value(rdfns.FOAF.name)
        else:
            return self.name

    #: list of other URIs equivalent to the current entity, via owl:sameAs
    same_as = rdfmap.ValueList(rdflib.OWL.sameAs, transitive=True)

    @property
    def dbpedia_uri(self):
        'dbpedia URI'
        for uri in self.same_as:
            if 'dbpedia.org' in uri:
                return uri

    @property
    def dbpedia(self):
        ':class:`DBpediaEntity` for this resource'
        if self.dbpedia_uri is not None:
            return DBpediaEntity(self.graph, self.dbpedia_uri)

    @property
    def viaf_uri(self):
        'VIAF URI'
        for uri in self.same_as:
            if 'viaf.org' in uri:
                return uri

    #: birth date
    birthdate = rdfmap.Value(rdfns.SCHEMA_ORG.birthDate)
    #: birth place
    birthplace = rdfmap.Resource(rdfns.DBPEDIA_OWL.birthPlace, RdfLocation)
    #: list of occupations
    occupation = rdfmap.ValueList(rdfns.SCHEMA_ORG.jobTitle)
    #: description
    description = rdfmap.Value(rdfns.SCHEMA_ORG.description)

    @property
    def description_context(self):
        '''Description context - identifier for the document where the
        description of this person comes from.'''
        # person comes from
        # NOTE: Using triples here because description text doesn't match (loses lang?)
        triples = list(self.graph.triples((self.identifier, rdfns.SCHEMA_ORG.description, None)))
        # there should only be one triple
        if triples:
            # and there should only be one context
            contexts = list(self.graph.contexts(triple=triples[0]))
            if contexts:
                ctx = contexts[0]

                # FIXME: for some reason the rdf types don't seem to be in the correct context;
                # should be able to query by type if they were
                # list(ctx[0].subjects(rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage))
                # list(ctx[0].subjects(rdflib.RDF.type, rdfns.ARCH.Collection))

                # as a work-around, find things that are *about* this person and
                # then filter to make sure we return the correct url
                about = list(ctx.subjects(rdfns.SCHEMA_ORG.about, self.identifier))
                for a in about:
                    # might be niceto use archival collection object from groupsheet models
                    # (currently that would be a circular import)
                    if (a, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                        return self.graph.value(a, rdfns.DC.isPartOf) or a

    @property
    def desc_context_name(self):
        'Name or label of the :attr:`description_context` source'
        # for some reason, context uri is coming through as a literal instead;
        # perhaps because it is being found via isPartOf rel?
        desc_context = rdflib.URIRef(self.description_context)
        return self.graph.value(desc_context, rdfns.SCHEMA_ORG.name)

    #: list of work locations
    work_locations = rdfmap.ResourceList(rdfns.SCHEMA_ORG.workLocation, RdfLocation)
    #: list of home locations
    home_locations = rdfmap.ResourceList(rdfns.SCHEMA_ORG.homeLocation, RdfLocation)

    @property
    def locations(self):
        'all locations (work and home)'
        return self.work_locations + self.home_locations

    @property
    def has_profile(self):
        'boolean flag to indicate if this person should have a local profile page'
        # current requirements: local uri and has a description
        return self.local_uri and \
           self.description_context or (self.dbpedia and self.dbpedia.description)

    # TODO: need access to groupsheets by this person

    #: list of documents authored by this person
    documents = rdfmap.ResourceList(rdfns.DC.creator, RdfResource, is_object=False)

    @property
    def groupsheets(self):
        # list of Group sheets by this person
        return [d for d in self.documents if rdfns.BG.GroupSheet in d.rdf_types]

    @cached_property
    def picture(self):
        ''':class:`~belfast.people.models.ProfilePicture` of this person,
        if there is one.'''
        # NOTE: using get_model because importing ProfilePicture is a circular dep
        profile_pic_model = get_model('people', 'ProfilePicture')
        pics = profile_pic_model.objects.filter(person_uri=self.identifier)
        if pics.count():
            return pics[0]


class RdfPoem(RdfEntity):
    ':class:`RdfEntity` for a single poem'
    #: author
    author = rdfmap.Resource(rdfns.SCHEMA_ORG.author, RdfPerson)
    #: title
    title = rdfmap.Value(rdfns.SCHEMA_ORG.name, normalize=True)

# FIXME! this is a hack; find a better way to do this...
# patch in types to return for connected persons/orgs
RdfOrganization._person_type = RdfPerson
RdfOrganization._org_type = RdfOrganization
RdfPerson._person_type = RdfPerson

# NOTE: this is forcing rdf graph load every restart
#BelfastGroup = RdfOrganization(rdf_data(), rdfns.BELFAST_GROUP_URIREF)

def BelfastGroup():
    '''Convenience method to initalize and return an :class:`RdfOrganization`
    for the Belfast Group'''
    return RdfOrganization(rdf_data(), rdfns.BELFAST_GROUP_URIREF)


def profile_people():
    'Generate a list of :class:`RdfPerson` with profiles on the site.'
    g = rdf_data()
    start = time.time()
    current_site = Site.objects.get(id=settings.SITE_ID)
    res = g.query('''
        PREFIX schema: <%(schema)s>
        PREFIX rdf: <%(rdf)s>
        SELECT DISTINCT ?person
        WHERE {
          ?person rdf:type schema:Person .
          ?person schema:familyName ?name .
          FILTER regex(str(?person), "^http://%(site)s")
        } ORDER BY ?name
        ''' % {'schema': rdfns.SCHEMA_ORG, 'rdf': rdflib.RDF,
               'site': current_site.domain}
        )
    # FIXME:  should be possible to filter at this level
    # on precense of a dbpedia description or a local schema description
    # but can't get the query to work...

    logger.debug('Found %d people in %.02f sec' % (len(res),
                 time.time() - start))
    # people = [RdfPerson(g.get_context(r['person']), r['person']) for r in res]
    people = [RdfPerson(g, r['person']) for r in res]
    return people


def find_places():
    'Generate a list of :class:`RdfLocation` associated with Belfast Group people.'
    g = rdf_data()
    return [RdfLocation(g, subj) for subj in g.subjects(predicate=rdflib.RDF.type,
                                                       object=rdfns.SCHEMA_ORG.Place)]
