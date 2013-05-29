from eulxml import xmlmap
from eulxml.xmlmap import teimap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel
import glob
import rdflib
from django.conf import settings
from os import path


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


BELFAST_GROUP_URI = 'http://viaf.org/123393054/'

ARCH = rdflib.Namespace('http://purl.org/archival/vocab/arch#')
SCHEMA_ORG = rdflib.Namespace('http://schema.org/')
DC = rdflib.Namespace('http://purl.org/dc/terms/')
BIBO = rdflib.Namespace('http://purl.org/ontology/bibo/')

#rdflib.resource.Resource - takes graph, subject

class RdfPerson(rdflib.resource.Resource):

    @property
    def name(self):
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
            return '%s, %s' % (self.lastname, self.firstname)
        else:
            return self.name


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
        # FIXME: current model *loses* title order;
        # this is particularly bad for sequences, but generally bad

        if self.value(DC.title) is not None:
            titles.append(self.value(DC.title))

        # objects returns another rdflib Resource
        titles.extend([p.value(DC.title) for p in self.objects(DC.hasPart)
          if p.value(DC.title) is not None])

        return titles

    @property
    def sources(self):
        sources = []
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
                        name = self.graph.value(pcoll, SCHEMA_ORG.name)
                        sources.append(name)  # title/name ?

        return sources


def get_rdf_groupsheets():
    g = rdflib.Graph()
    for infile in glob.iglob(path.join(settings.RDF_DATA_DIR, '*.xml')):
        g.parse(infile)
    res = g.query('''
        PREFIX schema: <%s>
        PREFIX rdf: <%s>
        PREFIX bibo: <%s>
        SELECT ?ms ?author
        WHERE {
            ?doc schema:about <%s> .
            ?doc schema:mentions ?ms .
            ?ms rdf:type bibo:Manuscript .
            ?ms schema:author ?author .
            ?author schema:name ?name
        } ORDER BY ?name
        ''' % (rdflib.XSD, rdflib.RDF, BIBO, BELFAST_GROUP_URI)
    )
        #         ?author schema:familyName ?authorLast
        # } ORDER BY ?authorLast
    # FIXME:  only QUB has schema:familyName so that query restricts to them
    # TODO: clean up data so we have lastnames for all authors

    # FIXME: restricting to ms with author loses one anonymous sheet
    # how to filter out non-group sheet irish misc content?
    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs

