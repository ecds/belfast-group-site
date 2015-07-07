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
from belfast.util import rdf_data, cached_property
from belfast.people.rdfmodels import RdfPerson


logger = logging.getLogger(__name__)


class Contents(teimap._TeiBase):
    ''':class:`~eulxml.xmlmap.XmlObject` for table of contents information,
    with a title and list of items, for a :class:`TeiGroupSheet`.'''
    #: title - ``tei:p``
    title = xmlmap.StringField('tei:p')
    #: list of items - ``tei:list/tei:item``
    items = xmlmap.StringListField('tei:list/tei:item')


class Poem(teimap._TeiBase):
    ''':class:`~eulxml.xmlmap.XmlObject` for a single Poem in a :class:`TeiGroupSheet`.'''
    #: poem identifier
    id = xmlmap.StringField('@xml:id')    # is this the correct id to use?
    #: poem title - uses ``tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type='main']``
    title = xmlmap.StringField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]')
    #: access to title as an :class:`~eulxml.xmlmap.XmlObject`, to allow for generating formatting
    #: or exposing tagged names within the title
    title_node = xmlmap.NodeField('tei:front/tei:titlePage/tei:docTitle/tei:titlePart[@type="main"]', xmlmap.XmlObject)
    # little bit hacky; access to title as node instead of string, to allow formatting
    # embedded content (i.e. tagged places or other names)
    #: body of the poem ``tei:body``
    body = xmlmap.NodeField('tei:body', xmlmap.XmlObject)
    #: back matter of the poem ``tei:back``
    back = xmlmap.NodeField('tei:back', xmlmap.XmlObject)
    #: byline from the back matter, usually used for author attribution on :class:`TeiGroupSheet`
    byline = xmlmap.StringField('tei:back/tei:byline', normalize=True)


class IdNumber(teimap._TeiBase):
    ''':class:`~eulxml.xmlmap.XmlObject` for ``tei:idno`` element, to provide
    access to ARK urls stored in the TEI header of the Group sheet xml.'''
    #: type ``@type``
    type = xmlmap.StringField('@type')
    #:id ``@id``
    id = xmlmap.StringField('@n')
    #: actual value of the id element (i.e., the ARK URL)
    value = xmlmap.StringField('./text()')


class ArkIdentifier(IdNumber, XmlModel):
    ''':class:`~eulexistdb.models.XmlModel` for searching eXist-db for
    ``tei:idno`` elements.'''
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei': ROOT_NS,
    }
    #: manager for searching on ``//tei:idno[@type='ark']``
    objects = Manager('//tei:idno[@type="ark"]')

# cache ark -> ids that have been looked up recently
_id_from_ark = {}

def id_from_ark(ark):
    '''Simple method to look up a TEI id based on the ARK url
       to allow linking within the current site based on an ARK'''
    global _id_from_ark
    if ark in _id_from_ark:
        return _id_from_ark[ark]
    try:
        ark_id = ArkIdentifier.objects.get(value=ark).id
        _id_from_ark[ark] = ark_id
        return ark_id
    except Exception as err:
        logger.warn('Error attempting to retrieve TEI id for ARK %s : %s',
                    ark, err)


class TeiDocument(XmlModel, teimap.Tei):
    '''Simple top-level :class:`~eulxml.xmlmap.XmlObject` to provide access to
    the full TEI document (which may contain more than one :class:`TeiGroupSheet`).'''
    #: manager, searches on ``/tei:TEI``
    objects = Manager('/tei:TEI')


# NOTE: would it make more sense to split out RDF and TEI models?


class TeiGroupSheet(XmlModel):
    ''':class:`~eulexistdb.models.XmlModel` for searching and displaying a single
    TEI Group sheet document.'''
    #: root namespace
    ROOT_NS = teimap.TEI_NAMESPACE
    ROOT_NAMESPACES = {
        'tei': ROOT_NS,
    }
    #: group sheet id
    id = xmlmap.StringField('@xml:id')
    #: groupsheet title
    title = xmlmap.StringField('tei:head')
    #: document author
    author = xmlmap.StringField('tei:docAuthor')
    #: list of all authors, as :class:`~eulxml.xmlmap.XmlObject` so identifying
    #: information can be used to expose name information via RDFa
    authors = xmlmap.NodeListField('tei:docAuthor', xmlmap.XmlObject)
    #: document date
    date = xmlmap.StringField('tei:docDate')
    #: table of contents, as :class:`Contents`
    toc = xmlmap.NodeField('tei:argument', Contents)
    #: list of table of contents, as :class:`Contents` (in one group sheet, there
    #: are multiple contents sections because there are multiple authors)
    toc_list = xmlmap.NodeListField('tei:argument', Contents)

    #: list of poems in the groupsheet, as :class:`Poem`
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
    #: list of ARKs in the TEI header, as list of :class:`IdNumber`
    ark_list = xmlmap.NodeListField('ancestor::tei:TEI//tei:idno[@type="ark"]',
                                    IdNumber)

    @property
    def ark(self):
        '''ARK URL for this groupsheet'''
        for a in self.ark_list:
            if a.id == self.id:
                return a.value

    @cached_property
    def multi_author(self):
        '''boolean indicating if this groupsheet includes content by
        multiple authors'''
        # use > 1 so that groupsheet without any bylines is not detected
        # as being multi-author
        return len(set([p.byline for p in self.poems
                       if p.byline is not None])) > 1

    # TODO: it would be nice if this were a little easier to access
    # or generate; xmlmap dictfield might get part way there..
    # Possible to generate xpaths based on current object properties?


# TBD: how do groupsheet and people apps share rdf models?

class RdfDocument(RdfResource):
    ''':class:`belfast.rdf.models.RdfResource` for an an RDF Document'''
    #: :class:`~belfast.rdf.models.RdfResource` that this resource is part of,
    #: via dc:isPartOf relation
    part_of = rdfmap.Resource(rdfns.DC.isPartOf, RdfResource)

def archival_collections():
    '''Find and return a list of all archival :class:`RdfArchivalCollection`
    in the RDF data'''
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
    #: list of :class:RdfDocument` that are about (``schema.org/about``) this document
    documents = rdfmap.ResourceList(rdfns.SCHEMA_ORG.about, RdfDocument,
                                    is_object=False)
    @property
    def access_url(self):
        '''Access URL for this archival collection (i.e., URL to the finding aid).'''
        # subseries are part of primary findingaid docuent, so if there
        # is a partOf rel use that uri, otherwise use document uri
        for d in self.documents:
            return unicode(d.part_of or d)

        # fallback access (should only apply to QUB collection)
        # - but only use identifier if it looks like a url
        if self.identifier.startswith('http'):
            return self.identifier

        # no url for Pakenham Group sheet in private collection


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
    description = rdfmap.Value(rdfns.DC.description)
    'dc:description, used for additional notes about some groupsheets'

    # TODO: store this somewhere...
    @property
    def tei_id(self):
        '''TEI identifier for this group sheet, retrieved via ARK URL'''
        if self.url:
            return id_from_ark(str(self.url.identifier))

    # more complex properties: aggregate, other resources

    #: single author; :class:`RdfPerson` related via dc:creator
    author = rdfmap.Resource(rdfns.DC.creator, RdfPerson)
    #: list of authors (a very few groupsheets have multiple authors)
    #: list of :class:`RdfPerson', related via dc:creator`
    author_list = rdfmap.ResourceList(rdfns.DC.creator, RdfPerson,
        sort=lambda author: author.lastname)

    #: single title as literal value (dc:title)
    title = rdfmap.Value(rdfns.DC.title)
    #: title list as rdf:sequence (dc:title)
    title_list = rdfmap.Sequence(rdfns.DC.title)

    #: :class:`RdfArchivalCollection` sources that mention this document
    sources = rdfmap.ResourceList(rdfns.SCHEMA_ORG.mentions, RdfArchivalCollection,
                                  is_object=False)

    #: list of :class:`RdfPerson` who owned this document, via schema.org/owns
    owners = rdfmap.ResourceList(rdfns.SCHEMA_ORG.owns, RdfPerson,
                                  is_object=False)

def groupsheet_by_url(url):
    '''Find :class:`RdfGroupSheet` by URL'''
    start = time.time()
    g = rdf_data()
    uris = list(g.subjects(rdfns.SCHEMA_ORG.URL, rdflib.URIRef(url)))
    logger.debug('Found %d group sheet for url %s in %.02f sec',
                 len(uris), url, time.time() - start)
    # type should be rdfns.BG.GroupSheet, but probably don't need to confirm...
    return [RdfGroupSheet(g, u) for u in uris]


def get_rdf_groupsheets(author=None, has_url=None, source=None, coverage=None):
    '''Query RDF data to get a list of :class:`RdfGroupSheet`
    optionally filter by various attributes.

    :param author: optional author URI; use to find Group sheets by a specific
        author
    :param has_url: filter to only those Group sheets with a URL (i.e., digital
        editions on the site)
    :param source: filter by source archival collection that includes the Group
        sheet
    :param coverag: filter by coverage dates
    '''
    start = time.time()
    g = rdf_data()
    # in most cases, sort by last name and then title
    sort = '?sort_name ?sort_title'

    fltr = ''
    if author is not None:
        fltr = '. ?ms dc:creator <%s> ' % author
        # when filtering by author, only sort on title
        # (better handling for multi-author Group sheets)
        sort = '?sort_title'

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
            # one Group sheet is anonymous; make author optional to avoid omitting
            OPTIONAL {
               ?ms dc:creator ?author .
               ?author schema:familyName ?name
            } .
            # some Group sheets are untitled; make title optional so we don't lose those
            OPTIONAL {
               ?ms dc:title ?title .
               # some Group sheets have only one title while others have a list
               OPTIONAL {
                  ?title rdf:first ?first_title
               }
            } .
            # sort anonymous Group sheet at the beginning of the list
            BIND (COALESCE(?name, "AA") AS ?sort_name) .
            # untitled should sort *after* other titles; set default string of ZZ
            BIND (COALESCE(?title, "ZZ") AS ?title1) .
            # first title default to empty string
            BIND (COALESCE(?first_title, "") AS ?first_title1) .
            # sort on first title (if list) or only title, together
            BIND (concat(str(?first_title1), str(?title1)) as ?sort_title)
            %(filter)s
        } ORDER BY %(sort)s
        ''' % {'schema': rdfns.SCHEMA_ORG, 'dc': rdfns.DC,
               'rdf': rdflib.RDF, 'bg': rdfns.BG.GroupSheet,
               'filter': fltr, 'sort': sort}

    # NOTE: some group sheets have rdf:sequence for titles, others have literal titles
    # combining first title in sequence (if present) with dc:title literal
    # so literal and sequence titles can be sorted together

    logger.debug(query)
    res = g.query(query)

    logger.debug('Found %d group sheets in %.02f sec', len(res),
                 time.time() - start)

    gs = [RdfGroupSheet(g, r['ms']) for r in res]
    return gs
