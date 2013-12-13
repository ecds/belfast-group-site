from eulxml import xmlmap
from eulxml.xmlmap import teimap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel
import logging
import rdflib
from rdflib.collection import Collection as RdfCollection
import time

from belfast import rdfns
from belfast.data import descriptors as rdfmap
from belfast.util import rdf_data, normalize_whitespace
from belfast.people.rdfmodels import RdfPerson


logger = logging.getLogger(__name__)


class Contents(teimap._TeiBase):
    title = xmlmap.StringField('tei:p')
    items = xmlmap.StringListField('tei:list/tei:item')


class Poem(teimap._TeiBase):
    id = xmlmap.StringField('@xml:id')    # is this the correct id to use?
    title = xmlmap.StringField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]')
    body = xmlmap.NodeField('tei:body', xmlmap.XmlObject)
    back = xmlmap.NodeField('tei:back', xmlmap.XmlObject)
    byline = xmlmap.StringField('tei:back/tei:byline')


class IdNumber(teimap._TeiBase):
    # xmlobject for idno element, to provide access to ARK urls
    type = xmlmap.StringField('@type')
    id = xmlmap.StringField('@n')
    value = xmlmap.StringField('./text()')


class ArkIdentifier(IdNumber, XmlModel):
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei': ROOT_NS,
    }
    objects = Manager('//tei:idno[@type="ark"]')

# cache ark -> ids that have been looked up recently
_id_from_ark = {}

def id_from_ark(ark):
    global _id_from_ark
    # simple method to look up a TEI id based on the ARK url,
    # to allow linking within the current site based on an ARK
    if ark in _id_from_ark:
        return _id_from_ark[ark]
    try:
        id = ArkIdentifier.objects.get(value=ark).id
        _id_from_ark[ark] = id
        return id
    except Exception as err:
        logger.warn('Error attempting to retrieve TEI id for ARK %s : %s'
                    % (ark, err))
        pass


class TeiDocument(XmlModel, teimap.Tei):
    '''Simple top-level class to provide access to the full TEI document
    (which may contain multiple groupsheets).'''
    objects = Manager('/tei:TEI')


# TODO: move to tei models?
class TeiGroupSheet(XmlModel):
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei': ROOT_NS,
    }

    id = xmlmap.StringField('@xml:id')
    title = xmlmap.StringField('tei:head')
    author = xmlmap.StringField('tei:docAuthor')
    date = xmlmap.StringField('tei:docDate')
    toc = xmlmap.NodeField('tei:argument', Contents)
    # in one case, list of Contents sectiosn (multiple authors in a single sheet)
    toc_list = xmlmap.NodeListField('tei:argument', Contents)

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

class RdfArchivalCollection(rdflib.resource.Resource):
    '''RDF :class:`~rdflib.resource.Resource` for an archival collection. '''
    rdf_type = rdfns.ARCH.Collection
    'expected rdf:type for this class'
    name = rdfmap.Value(rdfns.SCHEMA_ORG.name)


class RdfGroupSheet(rdflib.resource.Resource):
    '''RDF :class:`~rdflib.resource.Resource`) for a Belfast Group Sheet.'''
    rdf_type = rdfns.BG.GroupSheet

    # simple single-value properties
    date = rdfmap.Value(rdfns.DC.date)
    'date of groupsheet if known; dc:date'
    num_pages = rdfmap.Value(rdfns.BIBO.numPages)
    'number of pages in this groupsheet, if known; bibo:numPages'
    genre = rdfmap.Value(rdfns.SCHEMA_ORG.genre)
    'genre of the groupsheet content if known; schema.org/genre'
    url = rdfmap.Value(rdfns.SCHEMA_ORG.URL)
    'url for the groupsheet if digital edition is available; schema.org/URL'

    # TODO: store this somewhere...
    @property
    def tei_id(self):
        if self.url:
            return id_from_ark(str(self.url.identifier))

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

    # single title
    title = rdfmap.Value(rdfns.DC.title)

    # title list
    title_list = rdfmap.Sequence(rdfns.DC.title)

    @property
    def old_titles(self):
        titles = []
        # title is either a single literal OR an rdf sequence
        if self.value(rdfns.DC.title) is not None:
            title = self.value(rdfns.DC.title)
            # single literal
            if isinstance(title, rdflib.Literal):
                titles.append(normalize_whitespace(title))

            # otherwise, assuming node is an rdf sequence
            else:
                # convert from resource to standard blank node
                # since collection doesn't seem to handle resource
                bnode = rdflib.BNode(title)
                # create a collection to allow treating as a list
                titles.extend(RdfCollection(self.graph, bnode))
        return titles

    # FIXME: should be able to do this more efficiently;
    # set to return an rdf resource with a name...

    sources = rdfmap.ResourceList(rdfns.SCHEMA_ORG.mentions, RdfArchivalCollection,
                                  is_object=False)

    # should be sufficient, but make sure this works for all cases

    @property
    def old_sources(self):
        ''''Dictionary of archival collections that hold copies of this groupsheet.
        Key is URI,
        '''
        sources = {}
        # FIXME: for ormsby, this is displaying the series title in one case
        # rather than the collection title (subsubseries... )

        # TODO: refactor this so it is simpler

        for coll in self.graph.subjects(rdfns.SCHEMA_ORG.mentions, self.identifier):
            if (coll, rdflib.RDF.type, rdfns.ARCH.Collection) in self.graph:
                name = self.graph.value(coll, rdfns.SCHEMA_ORG.name)
                # if a blank node (i.e. irishmisc), get the webpage with a url
                if isinstance(coll, rdflib.BNode):
                    for pcoll in self.graph.subjects(rdfns.SCHEMA_ORG.about, coll):
                        if (pcoll, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                            name = self.graph.value(pcoll, rdfns.SCHEMA_ORG.name).strip()
                            sources[unicode(pcoll)] = name  # title/name ?

                else:
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

def groupsheet_by_url(url):
    start = time.time()
    # FIXME: could we just find by url? should be a groupsheet...
    # could use triple instead of query
    g = rdf_data()
    uris = list(g.subjects(rdfns.SCHEMA_ORG.URL, rdflib.URIRef(url)))
    logger.debug('Found %d group sheet for url %s in %.02f sec' % (
                 len(uris), url, time.time() - start))
    # FIXME: what to do if there are multiple?
    # type is expected to be rdfns.BG.GroupSheet
    if uris:
        return RdfGroupSheet(g, uris[0])


def get_rdf_groupsheets(author=None, has_url=None):
    # query rdf data to get a list of belfast group sheets
    # optionally filter by author (takes a URI)
    start = time.time()
    g = rdf_data()
    fltr = ''
    if author is not None:
        fltr = '. ?ms dc:creator <%s> ' % author

    if has_url is True:
        fltr += '. ?ms schema:URL ?url '

    res = g.query('''
        PREFIX schema: <%(schema)s>
        PREFIX dc: <%(dc)s>
        PREFIX rdf: <%(rdf)s>
        SELECT DISTINCT ?ms
        WHERE {
            ?ms rdf:type <%(bg)s> .
            ?ms dc:creator ?author .
            ?author schema:familyName ?name
            %(filter)s
        } ORDER BY ?name
        ''' % {'schema': rdfns.SCHEMA_ORG, 'dc': rdfns.DC,
               'rdf': rdflib.RDF, 'bg': rdfns.BG.GroupSheet, 'filter': fltr}
    )
                # ?author schema:familyName ?name
                        # } ORDER BY ?name

    # } ORDER BY ?authorLast
    # FIXME:  only QUB has schema:familyName so that query restricts to them
    # TODO: clean up data so we have lastnames for all authors

    # skos:prefLabel is in VIAF data but not directly related to viaf entity

    # FIXME: restricting to ms with author loses one anonymous sheet

    logger.debug('Found %d group sheets in %.02f sec' % (len(res),
                 time.time() - start))

    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs
