# harvest rdf

from datetime import datetime
import os
import rdflib
import re
import requests
import SPARQLWrapper
import sys
from urlparse import urlparse
import logging

from django.conf import settings
from django.contrib.sites.models import Site

try:
    from progressbar import ProgressBar, Bar, Percentage, ETA, SimpleProgress
except ImportError:
    ProgressBar = None

from belfast import rdfns


logger = logging.getLogger(__name__)

class HarvestRdf(object):
    '''Harvest RDF data and add it to a local RDF datastore.

    :params urls: list of urls to be harvested
    :params output_dir: optional output directory for rdf files; deprecated
    :params find_related: boolean flag, indicates whether related urls found
        on any of the original list of urls should also be harvested
    :param verbosity: verbosity level for output
    :param format: RDF serialization format, if using output directory
    :param graph: optional :class:`rdflib.graph.Graph`, if specified, harvested
        data will be added to the existing graph with a new graph context for
        each url
    '''

    URL_QUEUE = set()  # use set to ensure we avoid duplication
    PROCESSED_URLS = set()
    total = 0
    harvested = 0
    errors = 0

    _serialize_opts = {}

    def __init__(self, urls, output_dir=None, find_related=False, verbosity=1,
                 format=None, graph=None, no_cache=False):
        self.URL_QUEUE.update(set(urls))
        self.find_related = find_related
        self.base_dir = output_dir
        self.verbosity = int(verbosity)
        self.graph = graph
        self.no_cache = no_cache

        self.format = format
        if format is not None:
            self._serialize_opts['format'] = format

        self.process_urls()

    def process_urls(self):
        '''Method to process urls; displays a progessbar if available & appropriate'''
        if (len(self.URL_QUEUE) >= 5 or self.find_related) \
           and ProgressBar and os.isatty(sys.stderr.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')',
                       Bar(), ETA()]
            progress = ProgressBar(widgets=widgets,
                                   maxval=len(self.URL_QUEUE)).start()
        else:
            progress = None

        while self.URL_QUEUE:
            url = self.URL_QUEUE.pop()
            self.harvest_rdf(url)
            self.total += 1
            self.PROCESSED_URLS.add(url)
            if progress:
                progress.maxval = self.total + len(self.URL_QUEUE)
                progress.update(len(self.PROCESSED_URLS))

        if progress:
            progress.finish()

        # report if sufficient numbers:
        if self.verbosity >= 1 and (self.harvested > 5 or self.errors):
            print 'Processed %d url%s: %d harvested, %d error%s' % \
                  (len(self.PROCESSED_URLS),
                   '' if len(self.PROCESSED_URLS) == 1 else 's',
                   self.harvested, self.errors,
                   '' if self.errors == 1 else 's')

    def harvest_rdf(self, url):
        '''Harvest RDF from a particular URL.

        '''
        g = self.graph.get_context(url)
        if g and len(g):
            last_modified = g.value(g.identifier, rdfns.SCHEMA_ORG.dateModified)
            # TODO: use g.set(triple) to replace; may need to adjust date formats
            try:
                if self.no_cache:
                    headers={'cache-control': 'no-cache'}
                else:
                    headers={'if-modified-since': last_modified}

                response = requests.get(url, headers=headers,
                                        allow_redirects=False)
                # if this is a redirect, don't follow but add the real
                # url to the queue; this avoids an issue where related
                # links are generated relative to the initial url rather
                #  than the actual, resolved url
                if response.status_code in [requests.codes.moved,
                                            requests.codes.see_other,
                                            requests.codes.found]:
                    self.queue_url(response.headers['location'])
                    return

                elif response.status_code == requests.codes.not_modified:
                    # print '%s not modified since last harvested' % url
                    return  # nothing to do
                else:
                    # otherwise, remove the current context to avoid errors/duplication
                    self.graph.remove_context(g)

            except Exception as err:
                print 'Error attempting to load %s - %s' % (url, err)
                self.errors += 1
                return

                # last_modified = g.value(g.identifier, rdfns.SCHEMA_ORG.dateModified)
                # TODO: use g.set(triple) to replace

        else:
            try:
                headers = {}
                if self.no_cache:
                    headers['cache-control'] = 'no-cache'
                response = requests.get(url, headers=headers,
                    allow_redirects=False)
                if response.status_code in [requests.codes.moved,
                                            requests.codes.see_other,
                                            requests.codes.found]:
                    self.queue_url(response.headers['location'])
                    return

            except Exception as err:
                print 'Error attempting to load %s - %s' % (url, err)
                self.errors += 1
                return

        # g = rdflib.ConjunctiveGraph()
        # use the conjunctive graph store for persistence, url as context

        # TODO: if context already present, use last-modified from the rdf
        # and conditional GET to speed this up

        # either new or old version removed
        g = rdflib.Graph(self.graph.store, url)

        try:
            data = g.parse(data=response.content, location=url, format='rdfa')
            # NOTE: this was working previously, and should be fine,
            # but now generates an RDFa parsing error / ascii codec error
            # data = g.parse(location=url, format='rdfa')
        except Exception as err:
            print 'Error attempting to parse %s - %s' % (url, err)
            self.errors += 1
            self.graph.remove_context(g)
            return

        triple_count = len(data)
        # if no rdf data was found, report and return
        if triple_count == 0:
            if self.verbosity >= 1:
                print 'No RDFa data found in %s' % url
            return
        else:
            if self.verbosity > 1:
                print 'Parsed %d triples from %s' % (triple_count, url)


        # replace schema.org/dateModified with full date-time from http response
        # so we can use it for conditional get when re-harvesting
        if 'last-modified' in response.headers:
            g.set((g.identifier, rdfns.SCHEMA_ORG.dateModified, rdflib.Literal(response.headers['last-modified'])))

        # TODO: add graph with context?
        if self.graph is not None:

            # automatically updates in the store
            pass
            # self.graph.addN([(s, p, o, url) for s, p, o in data])

        else:
            filename = self.filename_from_url(url)
            if self.verbosity > 1:
                print 'Saving as %s' % filename
                with open(filename, 'w') as datafile:
                    data.serialize(datafile, **self._serialize_opts)

        self.harvested += 1

        # if find related is true, look for urls related to this one
        # via either schema.org relatedLink or dcterms:hasPart
        queued = 0
        if self.find_related:
            orig_url = rdflib.URIRef(url)

            # find all sub parts of the current url (e.g., series and indexes)
            for subj, obj in data.subject_objects(predicate=rdfns.DC.hasPart):
                if subj == orig_url or \
                   (subj, rdflib.OWL.sameAs, rdflib.URIRef(url)) in data:
                    related_url = unicode(obj)
                    # add to queue if not already queued or processed
                    if self.queue_url(related_url):
                        queued += 1

            # follow all related link relations
            for subj, obj in data.subject_objects(predicate=rdfns.SCHEMA_ORG.relatedLink):
                # Technically, we may only want related links where
                # the subject is the current URL...
                # Currently, findingaids rdfa is putting that relation on the
                # archival collection object rather than the webpage object;
                # For now, go ahead and grab any relatedLink in the RDF.
                # if subj == orig_url or \
                #    (subj, rdflib.OWL.sameAs, rdflib.URIRef(url)) in data:
                related_url = unicode(obj)
                if self.queue_url(related_url):
                    queued += 1

        if queued and self.verbosity > 1:
            print 'Queued %d related URL%s to be harvested' % \
                  (queued, 's' if queued != 1 else '')

    def filename_from_url(self, url):
        '''Simple mechanism to generate a filename based on the harvested URL;
        used when serializing RDF data to a local directory.'''
        # generate a filename based on the url (simple version)
        # NOTE: doesn't handle query string parameters, etc
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        host = host.replace('.', '_').replace(':', '-')
        path = parsed_url.path
        path = path.strip('/').replace('/', '-')
        filebase = host
        if path:
            filebase += '_%s' % path
            #  NOTE: save as .rdf since it may or may not be rdf xml
            return os.path.join(self.base_dir, '%s.%s' % (filebase, self.format))

    def queue_url(self, url):
        # Add a url to the queue if it is not already queued
        # or processed.  Returns True if a url was queued.
        if url not in self.URL_QUEUE and url not in self.PROCESSED_URLS:
            self.URL_QUEUE.add(url)
            return True
        return False


class Annotate(object):
    '''Annotate RDF data in the local graph by harvesting minimum required
    information from other data souces, such as VIAF and DBpedia.'''

    # harvest only the bare minimum
    # for places, we need lat/long (and maybe authoritative name?)
    # for viaf people, we need dbpedia same as and possibly foaf names
    # for dbpedia people, get: description, wikipedia url; thumbnail?

    def __init__(self, graph):
        self.graph = graph
        self.current_site = Site.objects.get(id=settings.SITE_ID)

        self.places()
        self.viaf_people()
        self.dbpedia_people()

    # regex to pull geonames id from a geonames uri
    # geonames uris should look roughly like:
    #   http://www.geonames.org/2638360/
    # - some have sws instead of www; may not have trailing slash or could have /name.html
    geonames_id = re.compile('^http://[a-z]+.geonames.org/(?P<id>\d+)/?')

    def places(self):
        '''Iterate over geonames identifiers in the local dataset and pull
        needed information from geonames.org for those entities, including
        latitude and longitude.'''

        # not sure what graph context makes the most sense, so grouping by source
        context = self.graph.get_context('http://geonames.org/')
        # FIXME: for geonames use ###/about.rdf instead?
        # and probably should pull default title/name

        start = datetime.now()
        res = self.graph.query('''
            PREFIX schema: <%(schema)s>
            PREFIX rdf: <%(rdf)s>
            PREFIX geo: <%(geo)s>
            SELECT DISTINCT ?uri
            WHERE {
                ?uri rdf:type schema:Place .

            }
            ''' % {'schema': rdfns.SCHEMA_ORG, 'rdf': rdflib.RDF,
                   'geo': rdfns.GEO}
        )
                        # FILTER NOT EXISTS {?uri geo:lat ?lat}
        logger.info('Found %d places without lat/long in %s' % \
                    (len(res), datetime.now() - start))

        uris = [r['uri'] for r in res]

        if len(uris) >= 5 and ProgressBar and os.isatty(sys.stderr.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')',
                       Bar(), ETA()]
            progress = ProgressBar(widgets=widgets, maxval=len(uris)).start()
            processed = 0
        else:
            progress = None

        for uri in uris:
            if not uri.startswith('http:'):
                # skip (should be able to check for bnode type instead?)
                continue

            match = self.geonames_id.match(uri)
            geonames_id = match.groupdict()['id'] if match else None

            if not self.graph.value(uri, rdfns.GEO.lat):
                try:
                    g = rdflib.Graph()
                    # ought to be able to use content-negotation for any of
                    # these uris (geonames or dbpedia), but that errors on a
                    # handful of geonames documents
                    if geonames_id is not None:
                        rdf_url = 'http://www.geonames.org/%s/about.rdf' % geonames_id
                    else:
                        rdf_url = uri
                    data = requests.get(rdf_url, headers={'accept': 'application/rdf+xml'})
                    if data.status_code == requests.codes.ok:
                        g.parse(data=data.content)

                        lat = g.value(uri, rdfns.GEO.lat)
                        lon = g.value(uri, rdfns.GEO.long)
                        if lat is not None:
                            context.set((uri, rdfns.GEO.lat, lat))
                        if lon is not None:
                            context.set((uri, rdfns.GEO.long, lon))

                except Exception as err:
                    print 'Error loading %s : %s' % (uri, err)

            if progress:
                processed += 1
                progress.update(processed)

        if progress:
            progress.finish()

    def viaf_people(self):
        '''Iterate over VIAF identifiers in the local dataset and pull
        needed information from viaf.org for those entities, e.g. foaf:name.'''

        # not sure what graph context makes the most sense, so grouping by source
        context = self.graph.get_context('http://viaf.org/')

        # find VIAF uris for people with local uris
        start = datetime.now()
        res = self.graph.query('''
            PREFIX schema: <%(schema)s>
            PREFIX rdf: <%(rdf)s>
            PREFIX owl: <%(owl)s>
            SELECT DISTINCT ?viaf
            WHERE {
                ?uri rdf:type schema:Person .
                ?uri owl:sameAs ?viaf
                FILTER regex(str(?uri), "^http://%(domain)s")
                FILTER regex(str(?viaf), "^http://viaf.org")
            }
            ''' % {'schema': rdfns.SCHEMA_ORG, 'rdf': rdflib.RDF,
                   'owl': rdflib.OWL, 'domain': self.current_site.domain}
        )
        logger.info('Found %d VIAF person(s) in %s',
                    len(res), datetime.now() - start)

        uris = [r['viaf'] for r in res]

        if len(uris) >= 5 and ProgressBar and os.isatty(sys.stderr.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')',
                       Bar(), ETA()]
            progress = ProgressBar(widgets=widgets, maxval=len(uris)).start()
            processed = 0
        else:
            progress = None

        for uri in uris:
            names = list(self.graph.subjects(uri, rdfns.FOAF.name))
            if names:
                # skipping; info has already been harvested
                continue

            # Use requests with content negotiation to load the data
            data = requests.get(str(uri), headers={'accept': 'application/rdf+xml'})

            if data.status_code == requests.codes.ok:
                tmpgraph = rdflib.Graph()
                tmpgraph.parse(data=data.content)

                names = tmpgraph.query('''
                    PREFIX foaf: <%(foaf)s>
                    SELECT ?name
                    WHERE {
                       <%(uri)s> foaf:name ?name
                    }
                    ''' % {'foaf': rdfns.FOAF, 'uri': uri})
                    # NOTE: viaf names don't seem to be tagged by language
                    # (restricting to language returns nothing)
                    #     FILTER (lang(?name) = 'en')

                    # NOTE: may need to restrict to names we know we need...
                for n in names:
                    context.add((uri, rdfns.FOAF.name, n['name']))
                    logger.debug('Adding name %s for %s',  n['name'], uri)

                # VIAF now using schema.org/sameAs instead of owl:sameAs
                same_as = list(tmpgraph.objects(uri, rdflib.OWL.sameAs))
                same_as.extend(list(tmpgraph.objects(uri, rdfns.SCHEMA_ORG.sameAs)))
                for obj in same_as:
                    if 'dbpedia.org' in unicode(obj):
                        # for convenience, use owl:sameAs locally, since
                        # that is what the other code will be looking for
                        context.add((uri, rdflib.OWL.sameAs, obj))
                        logger.debug('Adding %s sameAs %s', uri, obj)

            if progress:
                processed += 1
                progress.update(processed)

        if progress:
            progress.finish()


    def dbpedia_people(self):
        '''Iterate over DBpedia identifiers in the local dataset and pull
        needed information from DBpedia for those entities, particularly abstract
        (description) and link to Wikipedia.'''

        # not sure what graph context makes the most sense, so grouping by source
        context = self.graph.get_context('http://dbpedia.org/')

        dbpedia_sparql = SPARQLWrapper.SPARQLWrapper("http://dbpedia.org/sparql")

        start = datetime.now()
        # find dbedia uris referenced by local uris
        res = self.graph.query('''
            PREFIX schema: <%(schema)s>
            PREFIX rdf: <%(rdf)s>
            PREFIX owl: <%(owl)s>
            SELECT DISTINCT ?dbp
            WHERE {
                ?uri rdf:type schema:Person .
                ?uri owl:sameAs ?viaf .
                ?viaf owl:sameAs ?dbp
                FILTER regex(str(?uri), "^http://%(domain)s")
                FILTER regex(str(?dbp), "^http://dbpedia.org")
            }
            ''' % {'schema': rdfns.SCHEMA_ORG, 'rdf': rdflib.RDF,
                   'owl': rdflib.OWL, 'domain': self.current_site.domain}
        )
        logger.info('Found %d DBpedia person(s) in %s',
                    len(res), datetime.now() - start)

        uris = [unicode(r['dbp']).encode('ascii', 'ignore') for r in res]

        if len(uris) >= 5 and ProgressBar and os.isatty(sys.stderr.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')',
                       Bar(), ETA()]
            progress = ProgressBar(widgets=widgets, maxval=len(uris)).start()
            processed = 0
        else:
            progress = None

        for uri in uris:

            wikipedia_url = self.graph.value(uri, rdfns.FOAF.isPrimaryTopicOf)
            if wikipedia_url:
                # skipping; info has already been harvested
                # (every dbpedia page should have a link to its corresponding wikipedia url)
                continue

            try:
                uriref = rdflib.URIRef(uri)
                dbpedia_sparql.setQuery(u'DESCRIBE <%s>' % uriref)
                logger.debug('describing %s', uri)
                # NOTE: DESCRIBE <uri> is the simplest query that's
                # close to what we want and returns a response that
                # can be easily converted to an rdflib graph, but it generates
                # too many results for records like United States, England
                dbpedia_sparql.setReturnFormat(SPARQLWrapper.RDF)

                # convert to rdflib graph, then filter out any triples
                # where our uri is not the subject
                tmp_graph =  dbpedia_sparql.query().convert()

                for predicate in [rdfns.DBPEDIA_OWL.abstract, rdfns.FOAF.isPrimaryTopicOf]: #,
                                  # rdfns.DBPEDIA_OWL.thumbnail]:
                    objects = list(tmp_graph.objects(uriref, predicate))
                    if objects:
                        # if something returns multiple values (i.e. abstract)
                        # find the one in english
                        if len(objects) > 1:
                            for o in objects:
                                if o.language == 'en':
                                    obj = o
                                    break
                        else:
                            obj = objects[0]

                        context.add((uriref, predicate, obj))
                        logger.debug('Adding %s %s %s', uriref, predicate, obj)

            except Exception as err:
                print 'Error getting DBpedia data for %s : %s' % (uri, err)

            if progress:
                processed += 1
                progress.update(processed)

        if progress:
            progress.finish()



# old/deprecated version
class HarvestRelated(object):

    # sources to be harvested
    sources = [
        # NOTE: using tuples to ensure we process in this order,
        # to allow harvesting dbpedia records referenced in viaf/geonames
        # ('viaf', 'http://viaf.org/'),
        ('geonames', 'http://sws.geonames.org/'),
        ('dbpedia', 'http://dbpedia.org/'),
    ]

    def __init__(self, graph):
        self.graph = graph
        self.run()

    def run(self):
        dbpedia_sparql = SPARQLWrapper.SPARQLWrapper("http://dbpedia.org/sparql")

        for name, url in self.sources:
            # find anything that is a subject or object and has a
            # viaf, dbpedia, or geoname uri
            res = self.graph.query('''
                SELECT DISTINCT ?uri
                WHERE {
                    { ?uri ?p ?o }
                UNION
                    { ?s ?p ?uri }
                FILTER regex(str(?uri), "^%s") .
                }
            ''' % url)
            print '%d %s URI%s' % (len(res), name,
                                   's' if len(res) != 1 else '')

            if len(res) == 0:
                continue

            uris = [unicode(r['uri']).encode('ascii', 'ignore') for r in res]


            if len(uris) >= 5 and ProgressBar and os.isatty(sys.stderr.fileno()):
                widgets = [Percentage(), ' (', SimpleProgress(), ')',
                           Bar(), ETA()]
                progress = ProgressBar(widgets=widgets, maxval=len(uris)).start()
                processed = 0
            else:
                progress = None

            for u in uris:
                triple_count = len(list(self.graph.triples((rdflib.URIRef(u), None, None))))

                if triple_count > 5:
                    continue

                # print '%d triples for %s' % (
                #     len(list(self.graph.triples((rdflib.URIRef(u), None, None)))),
                #     u
                #     )

                # g = self.graph.get_context(url)
                # for now, assume if we have data we don't need to update
                # if g and len(g):
                #     print 'already have data for %s, skipping' % u
                #     continue

                # build filename based on URI
                # baseid = u.rstrip('/').split('/')[-1]

                # filename = os.path.join(datadir, '%s.%s' % (baseid, self.format))

                # if already downloaded, don't re-download but add to graph
                # for any secondary related content

                # if os.path.exists(filename):
                #     # TODO: better refinement would be to use modification
                #     # time on the file to download if changed
                #     # (do all these sources support if-modified-since headers?)

                #     # determine rdf format by file extension
                #     basename, ext = os.path.splitext(infile)
                #     fmt = ext.strip('.')
                #     try:
                #         g.parse(location=filename, format=fmt)
                #     except Exception as err:
                #         print 'Error loading file %s : %s' % (filename, err)

                g = rdflib.Graph(self.graph.store, url)

                if name == 'dbpedia':
                    # for dbpedia, use sparql query to get data we care about
                    # (request with content negotation returns extra data where
                    # uri is the subject and is also slower)
                    try:
                        dbpedia_sparql.setQuery('DESCRIBE <%s>' % u)
                        # NOTE: DESCRIBE <uri> is the simplest query that's
                        # close to what we want and returns a response that
                        # can be easily converted to an rdflib graph, but it generates
                        # too many results for records like United States, England
                        dbpedia_sparql.setReturnFormat(SPARQLWrapper.RDF)

                        # convert to rdflib graph, then filter out any triples
                        # where our uri is not the subject
                        tmp_graph =  dbpedia_sparql.query().convert()
                        for triple in tmp_graph:
                            s, p, o = triple
                            if s == rdflib.URIRef(u):
                                g.add(triple)
                                # tmp_graph.remove(triple)

                        if not len(g):
                            print 'Error: DBpedia query returned no triples for %s' % u
                            continue

                    except Exception as err:
                        print 'Error getting DBpedia data for %s : %s' % (u, err)
                        continue


                else:
                    # Use requests with content negotiation to load the data
                    data = requests.get(u, headers={'accept': 'application/rdf+xml'})

                    if data.status_code == requests.codes.ok:
                        # also add to master graph so we can download related data
                        # i.e.  dbpedia records for VIAF persons
                        # ONLY download related data for viaf (sameas dbpedia)
                        # (geonames rdf may reference multiple dbpedia without any sameAs)
                        # if name == 'viaf':

                        g.parse(data=data.content)

                        # tmp_graph = rdflib.Graph()
                        # tmp_graph.parse(data=data.content)

                    else:
                        print 'Error loading %s : %s' % (u, data.status_code)

                    # if tmp_graph:
                    #     with open(filename, 'w') as datafile:
                    #         try:
                    #             tmp_graph.serialize(datafile, format=self.format)
                    #         except Exception as err:
                    #             print 'Error serializing %s : %s' % (u, err)


                if progress:
                    processed += 1
                    progress.update(processed)

            if progress:
                progress.finish()



class LocalRDF(object):
    '''Harvest RDF from local HTML/RDFa fixtures and add information to the larger
    RDF graph. Uses the webpage identifier as context id, if available.
    '''

    def __init__(self, graph, files):
        triple_count = 0
        for filepath in files:
            tmp_graph = rdflib.ConjunctiveGraph()
            # parse the file into a temporary rdf graph
            with open(filepath) as bio:
                tmp_graph.parse(file=bio, format='rdfa')

            # find the identifier we want to use for graph context
            try:
                graph_id = list(tmp_graph.subjects(rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage))[0]
                # create a new context in our data store and copy all the data over
                g = rdflib.Graph(graph.store, graph_id)
            except IndexError:
                # if no webpage/url, create a context with no graph id
                g = rdflib.Graph(graph.store)

            for triple in tmp_graph:
                g.add(triple)

            triple_count += len(g)

        print 'Added %d triples' % triple_count


