from eulxml import xmlmap
from eulxml.xmlmap import teimap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel
import glob
import logging
from os import path
import rdflib
from rdflib.collection import Collection as RdfCollection
import time

from django.conf import settings

from belfast import rdfns
from belfast.util import rdf_data, network_data, cached_property
from belfast.people.models import RdfPerson

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


# TBD: how do groupsheet and people apps share rdf models?

class RdfGroupSheet(rdflib.resource.Resource):

    # simple single-value properties

    @property
    def date(self):
        return self.value(rdfns.DC.date)

    @property
    def num_pages(self):
        return self.value(rdfns.BIBO.numPages)

    @property
    def genre(self):
        return self.value(rdfns.SCHEMA_ORG.genre)

    # more complex properties: aggregate, other resources

    @property
    def author(self):
        author_uri = self.value(rdfns.DC.creator) or \
            self.value(rdfns.SCHEMA_ORG.author)

        if author_uri is not None:
            # returns an rdflib Resource, so use identifier to re-init
            # TODO: see if there is a way to auto-init as rdfperson obj
            pers = RdfPerson(self.graph, author_uri.identifier)
            return pers

    @property
    def titles(self):
        titles = []
        # title is either a single literal OR an rdf sequence
        if self.value(rdfns.DC.title) is not None:
            title = self.value(rdfns.DC.title)
            # single literal
            if isinstance(title, rdflib.Literal):
                titles.append(title)

            # otherwise, assuming node is an rdf sequence
            else:
                # convert from resource to standard blank node
                # since collection doesn't seem to handle resource
                bnode = rdflib.BNode(title)
                # create a collection to allow treating as a list
                titles.extend(RdfCollection(self.graph, bnode))
        return titles

    @property
    def sources(self):
        ''''Dictionary of archival collections that hold copies of this groupsheet.
        Key is URI,
        '''
        sources = {}
        # TODO: convert into dict with name & access uri
        for coll in self.graph.subjects(rdfns.SCHEMA_ORG.mentions, self.identifier):
            if (coll, rdflib.RDF.type, rdfns.ARCH.Collection) in self.graph:
                name = self.graph.value(coll, rdfns.SCHEMA_ORG.name)
                sources[unicode(coll)] = name  # title/name ?
            else:
                # NOTE: may want to use transitive subjects here (?)
                # FIXME: https: vs http: uri may be an issue!
                for pcoll in self.graph.subjects(rdfns.DC.hasPart, coll):
                    # find the *document* that describes the collection
                    # (but is not itself a collection), because the document
                    # is the thing we can link to.

                    # NOTE: looking for ARCH.Collection seems to generate
                    # redundant sources, one without a resolvable URI.
                    # Ignore the collection for now and only use the webpage.

                    # if (pcoll, rdflib.RDF.type, rdfns.ARCH.Collection) in self.graph \
                    #    or (pcoll, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                    if (pcoll, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                        # do we need to check webpage that is ABOUT a collection?
                        name = self.graph.value(pcoll, rdfns.SCHEMA_ORG.name).strip()
                        sources[unicode(pcoll)] = name  # title/name ?
        return sources


def get_rdf_groupsheets():
    g = rdf_data()
    res = g.query('''
        PREFIX schema: <%s>
        PREFIX rdf: <%s>
        PREFIX bibo: <%s>
        PREFIX skos: <%s>
        SELECT DISTINCT ?ms
        WHERE {
            ?doc schema:about <%s> .
            ?doc schema:mentions ?ms .
            ?ms rdf:type bibo:Manuscript .
            ?ms schema:author ?author .
            ?author schema:name ?name
        } ORDER BY ?name
        ''' % (rdflib.XSD, rdflib.RDF, rdfns.BIBO, rdfns.SKOS,
               rdfns.BELFAST_GROUP_URI)
    )

    # } ORDER BY ?authorLast
    # FIXME:  only QUB has schema:familyName so that query restricts to them
    # TODO: clean up data so we have lastnames for all authors

    # skos:prefLabel is in VIAF data but not directly related to viaf entity

    # FIXME: restricting to ms with author loses one anonymous sheet
    # how to filter out non-group sheet irish misc content?
    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs
