import datetime
import hashlib
import logging
import rdflib
from rdflib import collection as rdfcollection
import re
import time

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.text import slugify

from belfast import rdfns
from belfast.rdf import rdfmap
from belfast.rdf.qub import QUB

logger = logging.getLogger(__name__)


def normalize_whitespace(s):
    return unicode(re.sub(r'\s+', u' ', s.strip(), flags=re.UNICODE))


class IdentifyGroupSheets(object):

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

class SmushGroupSheets(object):

    # base identifier for 'smushed' ids, based on configured site domain
    BELFASTGROUPSHEET = rdflib.Namespace("http://%s/groupsheets/md5/" % \
        Site.objects.get(id=settings.SITE_ID).domain)

    def __init__(self, graph, verbosity=1):
        self.verbosity = verbosity
        self.full_graph = graph

        # iterate over all contexts in a conjunctive graph and process each one
        for ctx in graph.contexts():
            self.process_graph(ctx)

    def calculate_uri(self, uri, graph):
        # calculate a 'smushed' uri for a single groupsheet
        titles = []
        title = graph.value(uri, rdfns.DC.title)

        # title is either a single literal OR an rdf sequence
        if title:
            # single literal
            if isinstance(title, rdflib.Literal):
                titles.append(normalize_whitespace(title))

            # otherwise, assuming node is an rdf sequence
            else:
                # convert from resource to standard blank node
                # since collection doesn't seem to handle resource
                # create a collection to allow treating as a list
                titles.extend([normalize_whitespace(t) for t in
                              rdfcollection.Collection(graph, title)])

        # ignore title order for the purposes of de-duping
        # - sort titles so we can get a consistent MD5
        #   (assumes any group sheet with the same titles in any order
        #    and the same author is equivalent)
        # - slugify titles so we can ignore discrepancies in case and punctuation
        titles = sorted([slugify(t) for t in titles])

        author = graph.value(uri, rdfns.DC.creator)
        # NOTE: for some reason, author is not being found in local graph;
        # check in the full graph to ensure we get one
        if author is None:
            author = self.full_graph.value(uri, rdfns.DC.creator)

        print 'author %s titles %s' % (author, titles)

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
                author = '%s, %s' % (last, first)
            else:
                author = None

        # if not at least one title or title and author, skip this ms
        if not titles and not author:
            return

        m = hashlib.md5()
        if author is None:
            author = 'anonymous'
        text = '%s %s' % (author, ' '.join(titles))
        m.update(text.encode('utf-8'))

        return self.BELFASTGROUPSHEET[m.hexdigest()]

    def process_graph(self, graph):
        # build a dictionary of "smushed" URIs for belfast group sheets
        # for this document
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
    # minimal person resource, for use in cleaning up person data
    s_names = rdfmap.ValueList(rdfns.SCHEMA_ORG.name)
    s_first_name = rdfmap.Value(rdfns.SCHEMA_ORG.givenName)
    s_last_name = rdfmap.Value(rdfns.SCHEMA_ORG.familyName)
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

    def local_person_uri(self, name):
        # calculate a local uri for a person based on their name
        slug = slugify(name)
        if slug in self.name_conversions:
            slug = self.name_conversions[slug]
        uri = 'http://%s%s' % (
            self.current_site.domain,
            reverse('people:profile', args=[slug])
        )
        return uri

    def belfast_group_people(self, graph):
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
                ?person rdf:type <schema:Person> .
                ?person ?rel <%(bg_uri)s>
                FILTER regex(str(?author), "^(?!http://%(local_domain)s)")
            }''' % {'schema': rdfns.SCHEMA_ORG,
                    'rdf': rdflib.RDF, 'bg_uri': rdfns.BELFAST_GROUP_URI,
                    'local_domain': self.current_site.domain}
        res = graph.query(query)
        if res:
            logger.debug('Found %d people connected to the Belfast Group in %.02f sec' % (len(res),
                time.time() - start))
        people |= set([r['people'] for r in res])

        return people

    def process_graph(self, graph):
        # generate local URIs for people in the group, and make sure we have
        # first and last names for everyone (where possible)

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
                firstname, lastname = person_names(graph, subject)
                if firstname is None and lastname is None:
                    if self.verbosity >= 1:
                        print 'Names could not be determined for %s' % subject

                    # for now, skip if names couldn't be found
                    continue

                full_name = '%s %s' % (firstname, lastname)
                uri = self.local_person_uri(full_name)

                # skip if already converted ??
                if uri == str(subject):
                    continue

                uriref = rdflib.URIRef(uri)

                # set type to person (FIXME: redundant once smushed?)
                # ctx.add((uriref, rdflib.namespace.RDF.type, rdfns.SCHEMA_ORG.Person))
                # add full name as preferred label for local use
                name_triples = [
                    (uriref, rdflib.namespace.SKOS.preferredLabel, rdflib.Literal(full_name)),
                    (uriref, rdfns.SCHEMA_ORG.givenName, rdflib.Literal(firstname)),
                    (uriref, rdfns.SCHEMA_ORG.familyName, rdflib.Literal(lastname))
                ]
                # if names are not yet present in theg raph, add to current context
                for name in name_triples:
                    if name not in self.full_graph:
                        graph.add(name)

            # "smush" - convert all author identifiers to local uris
            # convert bnodes to local URIs so we can group authors
            # bnodes should only be converted in current context
            ctx_uris[subject] = uriref

            # if original subject uri was not a blank node, add a sameAs rel
            if not isinstance(subject, rdflib.BNode):
                graph.add((uriref, rdflib.OWL.sameAs, subject))
                # proper URIs (e.g. VIAF ids) should be converted anywhere
                # they occur, throughout the graph
                fullgraph_uris[subject] = uriref

            # NOTE: dbpedia rel will be harvested via VIAF

        # after processing people in this context, convert all uris
        smush(self.full_graph, fullgraph_uris)
        smush(graph, ctx_uris)


class InferConnections(object):
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

    # cases where we can infer date based on the collection it belongs to
    known_collection_dates = {
        # Hobsbaum collection at Queen's is labeled 1963-6, first period materials only
        QUB.QUB_BELFAST_COLLECTION: first_period['coverage'],
        # Carson collection starts at 1970; we know Carson only involved in second period
        'http://findingaids.library.emory.edu/documents/carson746/series5/': second_period['coverage'],
        # Muldoon only involved in second period
        'http://findingaids.library.emory.edu/documents/muldoon784/series2/subseries2.7/': second_period['coverage'],
        # Irish Literary Miscellany includes letter about re-forming the group;
        # all groupsheets in this collection listed in second period on previous version of the site
        'http://findingaids.library.emory.edu/documents/irishmisc794/': second_period['coverage'],
        # ormsby groupsheets are all second period
        'http://findingaids.library.emory.edu/documents/ormsby805/series2/subseries2.2/': second_period['coverage']
    }

    # possible other ways to infer:
    # tom mcgurk seems to be all second period
    # hugh bredin all first
    # maurice gallagher not in hobsbaum collection -> second period



    # need to recognize dates in the following formats: YYYY, YYYY-MM-DD, or YYYY/YYYY
    # year_re = re.compile('^\d{4}$')
    # yearmonthday_re = re.compile('^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$')
    date_re = re.compile('^(?P<year>\d{4})(-(?P<month>\d{2})-(?P<day>\d{2}))?(/(?P<year2>\d{4}))?$')

    def __init__(self, graph):

        for ctx in graph.contexts():
            self.process_graph(ctx)

    def process_graph(self, graph):
        ms = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.BG.GroupSheet))
        # if no manuscripts are found, skip
        if len(ms) == 0:
            return

        # calculate or infer if ms belongs to first or second period of the group
        for m in ms:
            # if coverage is already present (e.g., from TEI groupsheet or previous calculation),
            # nothing needs to be done
            coverage = graph.value(m, rdfns.DC.coverage)
            if coverage is not None:
                continue

            date = graph.value(m, rdfns.DC.date)
            # if date is known, check which period it falls into and assign dc:coverage accordingly

            if date:
                print 'ms %s date %s coverage %s' % (m, date, coverage)
                match = self.date_re.match(date)
                if match:
                    info = match.groupdict()
                    d = datetime.date(int(info['year']),
                        int(info['month'] or 1),
                        int(info['day'] or 1))

                    if self.first_period['start'] < d < self.first_period['end']:
                        graph.set((m, rdfns.DC.coverage, rdflib.Literal(self.first_period['coverage'])))
                    elif self.second_period['start'] < d < self.second_period['end']:
                        graph.set((m, rdfns.DC.coverage, rdflib.Literal(self.second_period['coverage'])))

            # If date is not known but part of Hobsbaum collection, infer first period
            elif str(graph.identifier) in self.known_collection_dates:
                graph.set((m, rdfns.DC.coverage,
                          rdflib.Literal(self.known_collection_dates[str(graph.identifier)])))
            else:
                print 'no date for %s context %s' % (m, graph.identifier)

            # TODO: figure out how to handle remaining ms

        # find authors of groupsheets and associate them with the Belfast Group
        res = graph.query('''
                PREFIX schema: <%(schema)s>
                PREFIX rdf: <%(rdf)s>
                PREFIX bg: <%(bg)s>
                SELECT ?author
                WHERE {
                    ?ms schema:author ?author .
                    ?ms rdf:type bg:GroupSheet
                }
                ''' % {'schema': rdfns.SCHEMA_ORG,
                       'rdf': rdflib.RDF,
                       'bg': rdfns.BG}
        )
        for r in res:
            # triple to indicate the author is affiliated with BG
            bg_assoc = (r['author'], rdfns.SCHEMA_ORG.affiliation, rdflib.URIRef(rdfns.BELFAST_GROUP_URI))
            if bg_assoc not in graph:
                graph.add(bg_assoc)




