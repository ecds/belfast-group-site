from eulxml import xmlmap
from eulxml.xmlmap import teimap
from eulexistdb.manager import Manager
from eulexistdb.models import XmlModel
import logging
import rdflib
import time

from belfast import rdfns
from belfast.rdf import rdfmap
from belfast.rdf.models import RdfResource
from belfast.util import rdf_data
from belfast.people.rdfmodels import RdfPerson


logger = logging.getLogger(__name__)


class Contents(teimap._TeiBase):
    title = xmlmap.StringField('tei:p')
    items = xmlmap.StringListField('tei:list/tei:item')


class Poem(teimap._TeiBase):
    id = xmlmap.StringField('@xml:id')    # is this the correct id to use?
    title = xmlmap.StringField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]')
    title_node = xmlmap.NodeField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]', xmlmap.XmlObject)
    # little bit hacky; access to title as node instead of string, to allow formatting
    # embedded content (i.e. tagged places or other names)
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
    # map as node to allow exposing name info as RDFa
    authors = xmlmap.NodeListField('tei:docAuthor', xmlmap.XmlObject)
    date = xmlmap.StringField('tei:docDate')
    toc = xmlmap.NodeField('tei:argument', Contents)
    # in one case, list of Contents sections (multiple authors in a single sheet)
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

    @property
    def multi_author(self):
        '''boolean indicating if this groupsheet includes content by
        multiple authors'''
        return len(set([p.byline for p in self.poems])) != 1

    # TODO: it would be nice if this were a little easier to access
    # or generate; xmlmap dictfield might get part way there..
    # Possible to generate xpaths based on current object properties?


# TBD: how do groupsheet and people apps share rdf models?

class RdfDocument(RdfResource):
    part_of = rdfmap.Resource(rdfns.DC.isPartOf, RdfResource)

def archival_collections():
    graph = rdf_data()
    subj = graph.subjects(rdflib.RDF.type, rdfns.ARCH.Collection)
    return [RdfArchivalCollection(graph, s) for s in subj]

class RdfArchivalCollection(RdfResource):
    '''RDF :class:`~rdflib.resource.Resource` for an archival collection. '''
    rdf_type = rdfns.ARCH.Collection
    'expected rdf:type for this class'

    # inherits standard name property

    # access to the webpage/findingaid that describes this collection
    # (NOTE: in at least one case, collection id does NOT resolve to findingaid)
    documents = rdfmap.ResourceList(rdfns.SCHEMA_ORG.about, RdfDocument,
                                    is_object=False)
    @property
    def access_url(self):
        # subseries are part of primary findingaid docuent, so if there
        # is a partOf rel use that uri, otherwise use document uri
        for d in self.documents:
            return d.part_of or d

        # fallback access (should only apply to QUB collection)
        return self.identifier



class RdfGroupSheet(RdfResource):
    '''RDF :class:`~belfast.rdf.models.RdfResource` for a Belfast Group Sheet.'''
    rdf_type = rdfns.BG.GroupSheet

    # simple single-value properties
    date = rdfmap.Value(rdfns.DC.date)
    'date of groupsheet if known; dc:date'
    coverage = rdfmap.Value(rdfns.DC.coverage)
    'date range for groupsheet (i.e., first or second period of Belfast Group)'
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

    # single author
    author = rdfmap.Resource(rdfns.DC.creator, RdfPerson)
    # author list - a very few groupsheets have multiple authors
    author_list = rdfmap.ResourceList(rdfns.DC.creator, RdfPerson)

    # single title as literal value
    title = rdfmap.Value(rdfns.DC.title)
    # title list as rdf:sequence
    title_list = rdfmap.Sequence(rdfns.DC.title)

    sources = rdfmap.ResourceList(rdfns.SCHEMA_ORG.mentions, RdfArchivalCollection,
                                  is_object=False)

    owners = rdfmap.ResourceList(rdfns.SCHEMA_ORG.owns, RdfPerson,
                                  is_object=False)

def groupsheet_by_url(url):
    start = time.time()
    g = rdf_data()
    uris = list(g.subjects(rdfns.SCHEMA_ORG.URL, rdflib.URIRef(url)))
    logger.debug('Found %d group sheet for url %s in %.02f sec' % (
                 len(uris), url, time.time() - start))
    # type should be rdfns.BG.GroupSheet, but probably don't need to confirm...
    return [RdfGroupSheet(g, u) for u in uris]


def get_rdf_groupsheets(author=None, has_url=None, source=None, coverage=None):
    # query rdf data to get a list of belfast group sheets
    # optionally filter by author (takes a URI)
    start = time.time()
    g = rdf_data()
    fltr = ''
    if author is not None:
        fltr = '. ?ms dc:creator <%s> ' % author

    if has_url is True:
        fltr += '. ?ms schema:URL ?url '

    if source is not None:
        fltr += '. <%s> schema:mentions ?ms' % source

    if coverage is not None:
        if coverage == 'undetermined':
            # TEMPORARY: hopefully we don't actually need to support this...
            fltr += ' FILTER NOT EXISTS { ?ms dc:coverage ?date } '
        else:
            fltr += '. ?ms dc:coverage "%s"' % coverage

    query = '''
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
               'rdf': rdflib.RDF, 'bg': rdfns.BG.GroupSheet,
               'filter': fltr}
    # TODO: use OPTIONAL {...} for author/name to include anonymous groupsheet?

    logger.debug(query)
    res = g.query(query)

    # FIXME: restricting to ms with author loses one anonymous sheet;
    # how to make optional?

    logger.debug('Found %d group sheets in %.02f sec' % (len(res),
                 time.time() - start))

    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs
