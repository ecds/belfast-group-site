import hashlib
import rdflib
from rdflib import collection as rdfcollection
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.text import slugify

from belfast import rdfns
from belfast.rdf import rdfmap


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
            # TODO: how to filter out non-group sheet irish misc content?
            # FIXME: not finding group sheets in irishmisc! (no titles?)


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

    # base identifier for 'smushed' ids
    # FIXME: don't hardcode; base on configured site ?
    BELFASTGROUPSHEET = rdflib.Namespace("http://belfastgroup.library.emory.edu/groupsheets/md5/")

    def __init__(self, graph, verbosity=1):
        self.verbosity = verbosity

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

        author = graph.value(uri, rdfns.SCHEMA_ORG.author)
        # blank node for the author is unreliable...
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
            # FIXME: only calculate a new uri for blank nodes?
            # TODO: handle TEI-based rdf with ARK pid urls
            newURI = self.calculate_uri(m, graph)
            if newURI is not None:
                new_uris[m] = newURI

        smush(graph, new_uris)
        # # iterate over all triples in the old graph and convert
        # # any uris in the new_uris dictionary to the smushed identifier
        # for s, p, o in graph:
        #     orig_s = s
        #     orig_o = o
        #     s = new_uris.get(s, s)
        #     # don't convert a smushed URL (e.g., TEI groupsheet URL)
        #     if not p == rdfns.SCHEMA_ORG.URL:
        #         o = new_uris.get(o, o)

        #     if orig_s != s or orig_o != o:
        #         # if changed remove old version, add new version
        #         graph.remove((orig_s, p, orig_o))
        #         graph.add((s, p, o))


def smush(graph, urimap):
    '''Ierate over all triples in a graph and convert any
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

    name_re = re.compile('^((?P<last>[^ ]{2,}), (?P<first>[^.,( ]{2,}))[.,]?')
    firstname = p.s_first_name
    lastname = p.s_last_name

    if not all([firstname, lastname]):
        names = p.s_names + p.f_names
        for name in names:
            match = name_re.match(unicode(name))
            if match:
                name_info = match.groupdict()
                firstname = name_info['first']
                lastname = name_info['last']
                # stop after we get the first name we can use (?)
                # note that for ciaran carson only one variant has the accent...
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
        for ctx in graph.contexts():
            self.process_graph(ctx)

        # FIXME: we only want to generate local uris for people associated
        # with the belfast group

        # NOTE: possibly iterate through people referenced in QUB first
        # should give us a good first-pass at good versions of names
        # and help clean up blank nodes for people without viaf/dbpedia ids
        # gqub = graph.get_context(self.QUB_URL)
        # qub = graph.get_context(self.QUB_URL)

        # TODO: keep track of replaced uris globally (?)
        # - non-blank-node uris may be referenced in multiple contexts...
        # new_uris = {}

        # TODO: consider keeping track of total number of replacements to assist with testing
        # (might be inflated due to blank nodes across contexts...)

    def local_person_uri(self, name):
        # calculate a local uri for a person based on their name
        uri = 'http://%s%s' % (
            self.current_site.domain,
            reverse('people:profile', args=[slugify(name)])
        )
        return uri

    def process_graph(self, graph):
        # local URIs for people in the group

        ctx_uris = {}
        for subject in graph.subjects(rdflib.RDF.type, rdfns.SCHEMA_ORG.Person):

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
            # "smush" - convert all author identifiers to local uris
            # convert bnodes to local URIs so we can group authors
            # bnodes should only be converted in current context
            ctx_uris[subject] = uriref
            # other uris should be converted throughout the graph
            # if not isinstance(subject, rdflib.BNode):
            # new_uris[subject] = uriref

            # set type to person (FIXME: redundant once smushed?)
            # ctx.add((uriref, rdflib.namespace.RDF.type, rdfns.SCHEMA_ORG.Person))
            # add full name as preferred label for local use
            name = (uriref, rdflib.namespace.SKOS.preferredLabel, rdflib.Literal(full_name))
            # if not present anywhere in the graph, add to current context
            if name not in self.full_graph:
                graph.add(name)

            # if original subject uri was not a blank node, add a sameAs rel
            if not isinstance(subject, rdflib.BNode):
                graph.add((uriref, rdflib.OWL.sameAs, subject))
            # FIXME: dbpedia rel might already be in graph somewhere via viaf?
            # if person.dbpedia_uri:
            #     ctx.add((uriref, rdflib.OWL.sameAs, rdflib.URIRef(person.dbpedia_uri)))
            smush(graph, ctx_uris)


class InferConnections(object):

    def __init__(self, graph):

        for ctx in graph.contexts():
            # returns graphs
            # print ctx
            # print len(ctx)
            # g = graph.get_context(ctx)
            self.process_graph(ctx)

        # for f in files:
        #     self.process_file(f)

    # def process_file(self, filename):
    def process_graph(self, graph):

        # infer rdf format from file extension
        # filebase, rdf_format = os.path.splitext(filename)
        # rdf_format = rdf_format.strip('.')

        # g = rdflib.Graph()
        # g.parse(filename, format=rdf_format)

        ms = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.BG.GroupSheet))
        # if no manuscripts are found, skip
        if len(ms) == 0:
            return

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


