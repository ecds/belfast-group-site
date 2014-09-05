from collections import defaultdict
import datetime
import hashlib
import logging
import rdflib
from rdflib import collection as rdfcollection
import re
import string
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.functional import SimpleLazyObject
from django.utils.text import slugify

from belfast import rdfns
from belfast.util import local_uri
from belfast.rdf import rdfmap
from belfast.rdf.qub import QUB

logger = logging.getLogger(__name__)


def normalize_whitespace(s):
    'utility method to normalize whitespace'
    # FIXME: if we want to use flags in python 2.6 needs to be compiled first
    return unicode(re.sub(r'\s+', u' ', s.strip(), flags=re.UNICODE | re.MULTILINE))
    # return unicode(re.sub(r'\s+', u' ', s.strip(), flags=re.UNICODE))


class IdentifyGroupSheets(object):
    '''Identify Belfast Group sheets in the RDF data, and label them with
    a locally defined Group Sheet type, :attr:`belfast.rdfns.BG.GroupSheet`
    so they can be identified quickly at run-time for display on the website.
    '''

    total = 0
    def __init__(self, graph, verbosity=1):

        self.verbosity = verbosity

        # iterate over all contexts in a conjunctive graph and process each one
        for ctx in graph.contexts():
            self.total += self.process_graph(ctx)

    def process_graph(self, graph):
        found = 0

        # identify belfast group sheets and label them with our local
        # belfast group sheet type

        # some collections include group sheets mixed with other content
        # (irishmisc, ormsby)
        # first look for a manuscript with an author that directly
        # references the belfast group
        res = graph.query('''
            PREFIX dc: <%(dc)s>
            PREFIX rdf: <%(rdf)s>
            PREFIX bibo: <%(bibo)s>
            SELECT ?ms
            WHERE {
                ?ms rdf:type bibo:Manuscript .
                ?ms schema:mentions <%(belfast_group)s> .
                ?ms dc:creator ?auth
            }
            ''' % {'dc': rdfns.DC,
                   'rdf': rdflib.RDF,
                   'bibo': rdfns.BIBO,
                   'belfast_group': rdfns.BELFAST_GROUP_URI
                   }
            )
            # searching for all manuscript that 'mention' belfast group
            # NOTE: schema:mentions NOT the right relation here;
            # needs to be fixed in findingaids and then here

        # if no matches, do a greedier search
        if len(res) == 0:
            # Find every manuscript mentioned in a document
            # that is *about* the belfast group

            # This should find group sheets in EAD RDF:
            # document (webpage) that is about the belfast group
            # and also about a collection, which has manuscripts

            # TODO: will also need to find ms associated with / presented at BG
            # NOTE: need a way to filter non-belfast group content
            res = graph.query('''
                PREFIX schema: <%(schema)s>
                PREFIX rdf: <%(rdf)s>
                PREFIX bibo: <%(bibo)s>
                SELECT ?ms
                WHERE {
                    ?doc schema:about <%(belfast_group)s> .
                    ?doc schema:about ?coll .
                    ?coll schema:mentions ?ms .
                    ?ms rdf:type bibo:Manuscript
                }
                ''' % {'schema': rdfns.SCHEMA_ORG,
                       'rdf': rdflib.RDF,
                       'bibo': rdfns.BIBO,
                       'belfast_group': rdfns.BELFAST_GROUP_URI
                       }
            )

        # if no manuscripts are found, stop and do not update the file
        if len(res) == 0:
            # Report nothing found in verbose mode
            if self.verbosity > 1:
                print 'No groupsheets found in %s' % graph.identifier
            return 0

        if self.verbosity >= 1:
            print 'Found %d groupsheet%s in %s' % \
                (len(res), 's' if len(res) != 1 else '', graph.identifier)

        for r in res:
            # add a new triple with groupsheet type in the current context
            graph.add((r['ms'], rdflib.RDF.type, rdfns.BG.GroupSheet))
            found += 1

        return found


def get_local_domain():
    return Site.objects.get(id=settings.SITE_ID).domain


class SmushGroupSheets(object):
    '''"Smush" Group sheets to de-dupe documents that are held in multiple
    locations and group them into a single document.

    Generates a local URI based on the author URI (if available) or name (if no
    URI) and a slugified, sorted list of the titles in the document.
    '''
    #: base identifier for 'smushed' ids, based on configured site domain
    BELFASTGROUPSHEET = SimpleLazyObject(lambda:
        rdflib.Namespace("http://%s/groupsheets/md5/" % get_local_domain()))

    # dictionary of smushed ids by graph identifier, in order to guarantee
    # unique ids within a single graph and avoid smushing multiple, different
    # untitled works into a single work
    groupsheet_ids = defaultdict(list)

    def __init__(self, graph, verbosity=1):
        self.verbosity = verbosity
        self.full_graph = graph

        # iterate over all contexts in a conjunctive graph and process each one
        for ctx in graph.contexts():
            self.process_graph(ctx)

        # dictionary to keep track of unique group sheet ids within a particular graph,
        # so that we don't collapse multiple untitled documents into a single doc

    def calculate_uri(self, uri, graph):
        '''Calculate a 'smushed' uri for a single groupsheet'''
        titles = []
        title = graph.value(uri, rdfns.DC.title)

        # title is either a single literal OR an rdf sequence
        if title:
            # single literal
            if isinstance(title, rdflib.Literal):
                normalized_title = normalize_whitespace(title)
                # if normalized title is different, update value in graph
                if unicode(title) != normalized_title:
                    logger.debug('Replacing title "%s" with normalized version "%s"' \
                                 % (title, normalized_title))
                    graph.set((uri, rdfns.DC.title, rdflib.Literal(normalized_title)))
                titles.append(normalize_whitespace(title))


            # otherwise, assuming node is an rdf sequence
            else:
                # convert from resource to standard blank node
                # since collection doesn't seem to handle resource
                # create a collection to allow treating as a list
                title_collection = rdfcollection.Collection(graph, title)
                for t in title_collection:
                    normalized_title = normalize_whitespace(t)
                    if unicode(t) != normalized_title:
                        logger.debug('Replacing title "%s" with normalized version "%s"' \
                                 % (t, normalized_title))

                        # NOTE: AFAICT, it should be possible to update the value
                        # via collection, something like this:
                        # index = title_collection.index(t)
                        # title_collection[index] = rdflib.Literal(normalized_title)

                        # but since that isn't working, find the exact triple
                        # and update the value for it directly

                        triples = list(graph.triples((None, rdflib.RDF.first, t)))
                        s, p, o = triples[0]
                        graph.set((s, p, rdflib.Literal(normalized_title)))

                    titles.append(normalized_title)

        # ignore title order for the purposes of de-duping
        # - sort titles so we can get a consistent MD5
        #   (assumes any group sheet with the same titles in any order
        #    and the same author is equivalent)
        # - slugify titles so we can ignore discrepancies in case and punctuation
        titles = sorted([slugify(t) for t in titles])

        author = graph.value(uri, rdfns.DC.creator)
        # NOTE: for some reason, author is not being found in local graph;
        # check in the full graph to ensure we get one
        # if author is None:
        #     author = self.full_graph.value(uri, rdfns.DC.creator)

        # blank node for the author is unreliable...
        # NOTE: possible goes away if running *after* generating local profile uris
        if isinstance(author, rdflib.BNode):
            # This should mostly only occur in Queen's University Belfast,
            # where we don't have URIs but *do* have first & last names.
            # Construct lastname, first for author identifier
            # (Assumes we are using a VIAF URI wherever possible, which
            # should be the case.)
            last = graph.value(author, rdfns.SCHEMA_ORG.familyName)
            first = graph.value(author, rdfns.SCHEMA_ORG.givenName)
            if last is not None and first is not None:
                author = normalize_whitespace('%s, %s' % (last, first))
            else:
                author_name = None
                names = list(graph.objects(author, rdfns.SCHEMA_ORG.name))
                for n in names:
                    if ',' in n:
                        author_name = normalize_whitespace(n)
                        break

                # if author is still not set, build lastname, first format from existing name
                if author_name is None:
                    name_parts = normalize_whitespace(names[0]).split(' ')
                    # pop off last name (splitting on whitespace)
                    last_name = name_parts.pop()
                    # remaning name(s) = first name
                    first_name = ' '.join(name_parts)
                    author_name ='%s, %s' % (last_name, first_name)

                author = author_name

        # if not at least one title or title and author, skip this ms
        if not titles and not author:
            logger.warn('No titles or author found for Group sheet %s', uri)
            return

        logger.debug('author %s titles %s', author, titles)

        m = hashlib.md5()
        if author is None:
            author = 'anonymous'
        text = '%s %s' % (author, ' '.join(titles))
        m.update(text.encode('utf-8'))

        identifier = m.hexdigest()
        # In two cases (Paul Smyth and Stewart Parker), there are multiple different
        # untitled Group sheets in the same collection (QUB).
        # Since identifiers are based on author and title list, these were being
        # collapsed into a single document.
        # To avoid that, check if the generated identifier is unique for this graph,
        # and if not, add a suffix until it *is* unique.
        if identifier in self.groupsheet_ids[graph.identifier]:

            # add suffix to the base id to differentiate
            for suffix in string.ascii_lowercase:
                new_id = '%s-%s' % (identifier, suffix)
                # if the new id is not already in the list for this graph, it is unique
                # and can be used
                if new_id not in self.groupsheet_ids[graph.identifier]:
                    identifier = new_id
                    # add to the list so we don't repeat this one either
                    self.groupsheet_ids[graph.identifier].append(identifier)
                    break

        else:
            self.groupsheet_ids[graph.identifier].append(identifier)

        return self.BELFASTGROUPSHEET[identifier]

    def process_graph(self, graph):
        '''Process a single graph context and update the group sheet URIs in that
        graph.  Builds a dictionary of "smushed" URIs for belfast group sheets
        for this document so all tuples referring to the old document id can
        be updated.'''
        new_uris = {}

        # smushing should be done after infer/identify group sheets
        # and assign local group sheet type
        # SO - simply find by our belfast group sheet type

        ms = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.BG.GroupSheet))
        # if no manuscripts are found, stop and do not update the file
        if len(ms) == 0:
            if self.verbosity > 1:
                print 'No groupsheets found in %s' % graph.identifier
            return

        # report number of groupsheets found in context, as a sanity check
        if self.verbosity >= 1:
            print 'Found %d groupsheet%s in %s' % \
                (len(ms), 's' if len(ms) != 1 else '', graph.identifier)

        for m in ms:
            newURI = self.calculate_uri(m, graph)
            if newURI is not None:
                new_uris[m] = newURI

        smush(graph, new_uris)


def smush(graph, urimap):
    '''Iterate over all triples in a graph and convert any
    URIs in the specified dictionary key to the new identifier in the
    corresponding value.'''

    # special cases / exemptions
    # predicates where the object should *NOT* smushed
    # e.g., TEI groupsheet url or sameAs from local uri to VIAF or similar
    exceptions = [rdfns.SCHEMA_ORG.URL, rdflib.OWL.sameAs]

    for s, p, o in graph:
        orig_s = s
        orig_o = o
        s = urimap.get(s, s)
        if not p in exceptions:
            o = urimap.get(o, o)

        if orig_s != s or orig_o != o:
            # if changed remove old version, add new version
            graph.remove((orig_s, p, orig_o))
            graph.add((s, p, o))

class Person(rdflib.resource.Resource):
    'minimal person resource, for use in cleaning up person data'
    #: schema.org/name
    s_names = rdfmap.ValueList(rdfns.SCHEMA_ORG.name)
    #: schema.org/givenName
    s_first_name = rdfmap.Value(rdfns.SCHEMA_ORG.givenName)
    #: schema.org/familyName
    s_last_name = rdfmap.Value(rdfns.SCHEMA_ORG.familyName)
    #: list of foaf:name
    f_names = rdfmap.ValueList(rdfns.FOAF.name)


def person_names(graph, uri):
    '''Given an :class:`rdflib.Graph` and a uri for a person, returns a
    tuple of first and last name.  Uses schema.org given name and family name
    if they are available; otherwise, attempts to detect and split a name by
    regular expression based on available schema.org foaf names in the data.
    '''
    # uri could be a uriref or bnode; don't convert since we don't know which
    p = Person(graph, uri)

    # look for lastname, firstname first - more reliable for splitting names correctly
    # - firstname could include . in the case of initials
    lastnamefirst_re = re.compile('^((?P<last>[^ ]{2,}), (?P<first>[^,( ]{2,}))[.,]?')
    firstnamelast_re = re.compile('^((?P<first>[^ ]{2,}) (?P<last>[^,( ]{2,}))$')
    firstname = p.s_first_name
    lastname = p.s_last_name

    if not all([firstname, lastname]):
        names = p.s_names + p.f_names
        for name in names:
            match = lastnamefirst_re.match(normalize_whitespace(name))
            if match:
                name_info = match.groupdict()
                firstname = name_info['first']
                lastname = name_info['last']
                # in some places names are all caps; don't use those
                if firstname.isupper() and lastname.isupper():
                    continue
                # stop after we get the first name we can use
                # note that for ciaran carson only one variant has the accent...
                break

        # if we couldn't find a lastname, firstname version look for firstname last
        if not all([firstname, lastname]):
            for name in names:
                match = firstnamelast_re.match(normalize_whitespace(name))
                if match:
                    name_info = match.groupdict()
                    firstname = name_info['first']
                    lastname = name_info['last']
                    # in some places names are all caps; don't use those
                    if firstname.isupper() and lastname.isupper():
                        continue
                    break

    return (firstname, lastname)


class ProfileUris(object):
    '''Generate local uris for persons associated with the belfast group,
    who will have profile pages on the site; smush or add relations to
    any additional information that will be needed for generating profiles.'''

    def __init__(self, graph, verbosity=1):
        self.verbosity = verbosity
        self.current_site = Site.objects.get(id=settings.SITE_ID)

        self.full_graph = graph
        # iterate over all contexts in a conjunctive graph and process each one
        for ctx in list(graph.contexts()):  # store before iterating in case of changes
            self.process_graph(ctx)

        # TODO: consider keeping track of total number of replacements to assist with testing
        # (might be inflated due to blank nodes across contexts...)

    # in some cases, there are multiple versions of a name; convert name slug
    # here to ensure we get a single uri for each person
    name_conversions = {
        'hugh-t-bredin': 'hugh-bredin',
    }

    @staticmethod
    def local_person_uri(name):
        # calculate a local uri for a person based on their name
        slug = slugify(name)
        if slug in ProfileUris.name_conversions:
            slug = ProfileUris.name_conversions[slug]

        uri = local_uri(reverse('people:profile', args=[slug]))
        return uri

    def belfast_group_people(self, graph):
        '''Identify people associated with the Belfast Group and generate
        local URIs for them so they can be quickly identified for display
        on the website.'''
        # NOTE: if we adjust the script so inferred connections are added first
        # the second query alone would probably be sufficient
        # (adds affiliation rel for all groupsheet authors)

        # sparql query to find groupsheet authors
        query = '''
            PREFIX schema: <%(schema)s>
            PREFIX dc: <%(dc)s>
            PREFIX rdf: <%(rdf)s>
            SELECT DISTINCT ?author
            WHERE {
                ?ms rdf:type <%(bg)s> .
                ?ms dc:creator ?author .
                FILTER regex(str(?author), "^(?!http://%(local_domain)s)")
            }''' % {'schema': rdfns.SCHEMA_ORG, 'dc': rdfns.DC,
                    'rdf': rdflib.RDF, 'bg': rdfns.BG.GroupSheet,
                    'local_domain': self.current_site.domain}
        start = time.time()
        res = graph.query(query)
        if res:
            logger.debug('Found %d group sheets author(s) in %.02f sec' % (len(res),
                time.time() - start))
        people = set([r['author'] for r in res])

        start = time.time()
        # query to find people with any rdf relation to the belfast group
        query = '''
            PREFIX schema: <%(schema)s>
            PREFIX rdf: <%(rdf)s>
            SELECT DISTINCT ?person
            WHERE {
                ?person rdf:type schema:Person .
                ?person ?rel <%(bg_uri)s>
                FILTER regex(str(?person), "^(?!http://%(local_domain)s)")
            }''' % {'schema': rdfns.SCHEMA_ORG,
                    'rdf': rdflib.RDF, 'bg_uri': rdfns.BELFAST_GROUP_URI,
                    'local_domain': self.current_site.domain}
        res = graph.query(query)
        if res:
            logger.debug('Found %d people connected to the Belfast Group in %.02f sec' % (len(res),
                time.time() - start))
        people |= set([r['person'] for r in res])

        return people

    @staticmethod
    def convert_to_localprofile(graph, subject, full_graph, verbosity=1):
        '''Convert a person URI to the new local person URI, updating all triples
        that reference the old URI to use the new one.'''

        # takes context graph, person uri, full graph
        firstname, lastname = person_names(graph, subject)
        if firstname is None and lastname is None:
            # if names were not found in current context, check full graph
            firstname, lastname = person_names(full_graph, subject)
            if firstname is None and lastname is None:
                if verbosity >= 1:
                    print 'Names could not be determined for %s' % subject
                # for now, skip if names couldn't be found
                return

        full_name = '%s %s' % (firstname, lastname)
        uri = ProfileUris.local_person_uri(full_name)
        uriref = rdflib.URIRef(uri)
        # set type to person (FIXME: redundant once smushed?)
        # ctx.add((uriref, rdflib.namespace.RDF.type, rdfns.SCHEMA_ORG.Person))
        # add full name as preferred label for local use
        name_triples = [
            (uriref, rdflib.namespace.SKOS.prefLabel, rdflib.Literal(full_name)),
            (uriref, rdfns.SCHEMA_ORG.givenName, rdflib.Literal(firstname)),
            (uriref, rdfns.SCHEMA_ORG.familyName, rdflib.Literal(lastname))
        ]
        # if names are not yet present in the graph, add to current context
        for name in name_triples:
            if name not in full_graph:
                graph.add(name)

        # if original subject uri was not a blank node, add a sameAs rel
        if not isinstance(uri, rdflib.BNode):
            graph.add((uriref, rdflib.OWL.sameAs, subject))

        return uri

    def process_graph(self, graph):
        '''Process an rdf graph and generate local URIs for people in the group,
        making sure there is a first and last names for each (where possible).'''

        # TODO: add more verbose output so it is easier to tell what is happening
        # and where things are going wrong when people get lost

        ctx_uris = {}
        fullgraph_uris = {}
        people = self.belfast_group_people(graph)
        # nothing to do in this graph context; stop processing
        if not people:
            return
        # report number of people found in context, as a sanity check
        if self.verbosity >= 1:
            print 'Found %d %s in %s' % \
                (len(people), 'people' if len(people) != 1 else 'person',
                 graph.identifier)


        for subject in people:
            uriref = None
            # FIXME: should not be necessary if we clean up as we go...
            # Check the full graph if already converted to a local uri
            same_as = list(self.full_graph.subjects(predicate=rdflib.OWL.sameAs, object=subject))
            if same_as:

                for uri in same_as:
                    if self.current_site.domain in str(same_as):
                        uriref = uri
                        break

            # if existing sameAs local uri was not found, generate local uri + add names
            if uriref is None:
                uri = ProfileUris.convert_to_localprofile(graph, subject,
                    self.full_graph, verbosity=self.verbosity)
                # skip if local-uri generation failed (e.g. first/last name not determined)
                if uri is None:
                    continue
                uriref = rdflib.URIRef(uri)

                # skip if already converted ??
                if uri == str(subject):
                    continue

            # "smush" - convert all author identifiers to local uris
            # convert bnodes to local URIs so we can group authors
            # bnodes should only be converted in current context
            ctx_uris[subject] = uriref

            # proper URIs (e.g. VIAF ids) should be converted anywhere
            # they occur, throughout the graph
            if not isinstance(subject, rdflib.BNode):
                fullgraph_uris[subject] = uriref

            # NOTE: dbpedia rel will be harvested via VIAF

        # after processing people in this context, convert all uris
        smush(self.full_graph, fullgraph_uris)
        smush(graph, ctx_uris)


class InferConnections(object):
    '''Make inferences about the data and add explicit relations based on
    implicit connections.'''

    first_period = {  # using cumulative dates for comparison
        'start': datetime.date(1963, 10, 1),
        'end': datetime.date(1966, 3, 30),
        'coverage': '1963-1966'

    }
    second_period = {
        'start': datetime.date(1966, 4, 1),
        'end': datetime.date(1972, 12, 31),
        'coverage': '1966-1972'
    }
    # October 1963-March 1966
    # Second Period, 1966-1970 & 1971-1972?

    # a couple of TEI groupsheets have dates that don't quite match what
    # we expect; make them consistent with our dates
    coverage_convert = {
        '1963-1968': '1963-1966',
        '1963-1972': '1963-1966',
        '1966-1976': '1966-1972'
    }

    # need to recognize dates in the following formats: YYYY, YYYY-MM-DD, or YYYY/YYYY
    # year_re = re.compile('^\d{4}$')
    # yearmonthday_re = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$')
    date_re = re.compile(r'^(?P<year>\d{4})(-(?P<month>\d{2})-(?P<day>\d{2}))?(/(?P<year2>\d{4}))?$')


    def __init__(self, graph):
        self.full_graph = graph
        self.current_site = Site.objects.get(id=settings.SITE_ID)

        for ctx in graph.contexts():
            self.process_graph(ctx)

    def process_graph(self, graph):
        '''Process a graph and add direct relationships for authors of poems
        that mention other people, places, etc.'''
        self.writes_about(graph)

        ms = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.BG.GroupSheet))
        # if no manuscripts are found, skip
        if len(ms) == 0:
            return

        # *** group sheet specific information: time period, owner
        for m in ms:
            # calculate time period for group sheet
            self.time_period(m, graph)
            # infer ownership of groupsheet copies based on archival collection
            self.ownership(m, graph)

        # *** find authors and owners of groupsheets and explicitly associate
        # them with the Belfast Group
        res = graph.query('''
                PREFIX schema: <%(schema)s>
                PREFIX dc: <%(dc)s>
                PREFIX rdf: <%(rdf)s>
                PREFIX bg: <%(bg)s>
                SELECT DISTINCT ?person
                WHERE {
                    ?ms rdf:type bg:GroupSheet .
                    {?ms dc:creator ?person }
                      UNION
                    {?person schema:owns ?ms }
                }
                ''' % {'schema': rdfns.SCHEMA_ORG, 'dc': rdfns.DC,
                       'rdf': rdflib.RDF, 'bg': rdfns.BG}
        )
        for r in res:
            # triple to indicate the author is affiliated with BG
            bg_assoc = (r['person'], rdfns.SCHEMA_ORG.affiliation, rdflib.URIRef(rdfns.BELFAST_GROUP_URI))
            if bg_assoc not in graph:
                graph.add(bg_assoc)

            # if person does not have a local uri (i.e., owner and not author),
            # generate one now (can't detect sooner)
            if not str(r['person']).startswith('http://%s' % self.current_site.domain):
                uri = ProfileUris.convert_to_localprofile(graph, r['person'],
                    self.full_graph)
                if uri is not None:
                    # if local uri was generated, convert everywhere in the graph
                    smush(self.full_graph, {r['person']: rdflib.URIRef(uri)})

    def time_period(self, ms, graph):
        '''Determine whether a groupsheet is first or second period
        and store the corresponding dates for that period in the RDF graph.

        If coverage is already present anywhere in the full graph
        (e.g., from a TEI groupsheet or previous calculation),
        nothing needs to be done.'''
        coverage = self.full_graph.value(ms, rdfns.DC.coverage)
        if coverage is not None:
            # a couple of TEI groupsheet dates need to be cleaned up
            if str(coverage) in self.coverage_convert:
                graph.set((ms, rdfns.DC.coverage,
                           rdflib.Literal(self.coverage_convert[str(coverage)])))

            # no conversion necessary; coverage date is valid
            return

        # look for exact date of ms, if known
        date = graph.value(ms, rdfns.DC.date)

        # In case there is no date, get all contexts where this ms occurs
        # so we can correctly infer the correct time period.
        # (Inferring based on presence/absence in Hobsbaum collection, but may
        # not encounter the Hobsbaum version of a ms first.)
        context_ids = [str(ctx.identifier) for ctx in
                       self.full_graph.contexts((ms, rdflib.RDF.type, rdfns.BG.GroupSheet))]

        # if date is known, check which period it falls into and assign dc:coverage accordingly
        if date:
            match = self.date_re.match(date)
            if match:
                info = match.groupdict()
                d = datetime.date(int(info['year']),
                    int(info['month'] or 1),
                    int(info['day'] or 1))

                if self.first_period['start'] < d < self.first_period['end']:
                    graph.set((ms, rdfns.DC.coverage, rdflib.Literal(self.first_period['coverage'])))
                elif self.second_period['start'] < d < self.second_period['end']:
                    graph.set((ms, rdfns.DC.coverage, rdflib.Literal(self.second_period['coverage'])))

        # If date is not known but part of Hobsbaum collection, infer first period
        # (Hobsbaum collection at Queen's is labeled 1963-6; first period materials only)
        elif QUB.QUB_BELFAST_COLLECTION in context_ids:
            graph.set((ms, rdfns.DC.coverage,
                      rdflib.Literal(self.first_period['coverage'])))

        # Hobsbaum collection is *very* complete for first period
        # so if not known and not Hobsbaum, infer second period
        else:
            graph.set((ms, rdfns.DC.coverage,
                      rdflib.Literal(self.second_period['coverage'])))

    def ownership(self, ms, graph):
        '''If possible, infer ownership of a manuscript based on the archival
        collection it came from and add an owner relationship, for use in the
        site network graphs.'''
        collection = list(self.full_graph.subjects(rdfns.SCHEMA_ORG.mentions, ms))
        for c in collection:
            types = list(self.full_graph.objects(c, rdflib.RDF.type))
            if rdfns.ARCH.Collection not in types:
                continue

            # the *creator* of the archival collection is the person
            # who collected and owned the materials before they were donated
            # to the archive
            # therefore, inferring that collection creator owned the
            # groupsheets that are included in that collection

            creator = graph.value(c, rdfns.SCHEMA_ORG.creator)
            # may not be in the current context, so check full graph in case
            if not creator:
                creator = self.full_graph.value(c, rdfns.SCHEMA_ORG.creator)

            # not all collections have a creator
            if creator:
                # NOTE: this identifier is most likely a VIAF URI;
                # we probably want to use the local profile uri instead;
                # consider usingsame-as rel to find?

                # using schema.org owns rel here - intended for product ownership,
                # but seems to be close enough for our purposes
                graph.set((creator, rdfns.SCHEMA_ORG.owns, ms))

    def writes_about(self, graph):
        '''Iterate over poems in the current graph and add an explicit relationship
        between the poem's author and any entities mentioned in the poem.'''
        poems = list(graph.subjects(predicate=rdflib.RDF.type,
                     object=rdflib.URIRef('http://www.freebase.com/book/poem')))

        for p in poems:
            # NOTE: this *should* be in the local graph context, but
            # apparently context is getting lost when triples including local URIs are converted
            authors = list(self.full_graph.objects(subject=p, predicate=rdfns.DC.creator))
            if not authors:  # should be present, but check just in case...
                continue
            author = authors[0]
            mentioned = list(graph.objects(subject=p, predicate=rdfns.SCHEMA_ORG.mentions))
            for m in mentioned:
                # triple to add direct connection between author and subject
                # using schema:mentions as shorthand for "writes about"
                writes_about = (author, rdfns.SCHEMA_ORG.mentions, m)
                if writes_about not in graph:
                    graph.add(writes_about)



