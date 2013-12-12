#!/usr/bin/env python

# script to harvest and prep entire dataset, start to finish

from optparse import make_option
import os
import rdflib
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.utils.text import slugify

from belfast import rdfns
from belfast.data.harvest import HarvestRdf, Annotate # HarvestRelated
from belfast.data.qub import QUB
from belfast.data.clean import SmushGroupSheets, IdentifyGroupSheets, \
    InferConnections
from belfast.data.nx import Rdf2Gexf

# FIXME: belfast.data app probably shouldn't rely on belfast.people...
from belfast.people.rdfmodels import BelfastGroup, get_belfast_people, RdfPerson


class Command(BaseCommand):
    '''Harvest and prep Belfast Group RDF dataset'''
    help = __doc__

    v_normal = 1

    option_list = BaseCommand.option_list + (
        make_option('-H', '--harvest', action='store_true', help='Harvest RDFa'),
        make_option('-q', '--queens', action='store_true',
            help='Convert Queens University Belfast collection to RDF'),
        make_option('-r', '--related', action='store_true',
            help='Harvest related RDF from VIAF, GeoNames, and DBpedia'),
        make_option('-i', '--identify', action='store_true',
            help='Identify group sheets'),
        make_option('-s', '--smush', action='store_true',
            help='Smush groupsheet URIs'),
        make_option('-c', '--connect', action='store_true',
            help='Infer and make connections implicit in the data'),
        make_option('-l', '--local-uris', action='store_true',
            help='Generate local URIs and add them to the graph based on existing data'),
        make_option('-g', '--gexf', action='store_true',
            help='Generate GEXF network graph data'),
        make_option('-x', '--clear', action='store_true',
            help='Clear all current RDF data and start fresh'),
    )

    # eadids for documents with tagged names
    eadids = ['longley744', 'ormsby805', 'irishmisc794', 'carson746',
              'heaney960', 'heaney653', 'muldoon784', 'simmons759',
              'hobsbaum1013', 'mahon689', 'fallon817', 'grennan1150',
              'heaney-hammond1019', 'hughes644', 'mcbreen1088',
              'monteith789', 'deane1210']

    # RDF from TEI group sheets
    tei_ids = ['longley1_10244', 'longley1_10353', 'heaney1_10407',
               'carson1_1035', 'longley1_10202', 'heaney1_10415',
               'heaney1_10365', 'heaney1_10163', 'heaney1_10199',
               'heaney1_10236', 'heaney1_10269', 'longley1_1042',
               'heaney1_10442', 'hobsbaum1_1040', 'heaney1_10116',
               'heaney1_1078', 'heaney1_1041', 'muldoon2_10121',
               'muldoon2_1079', 'muldoon2_1040', 'longley1_10120',
               'longley1_10158', 'longley1_1079', 'longley1_10282',
               'longley1_10316', 'simmons1_1035', 'simmons1_1069',
               'hobsbaum1_1047']

    # for now, harvest from test FA site
    harvest_urls = ['http://findingaids.library.emory.edu/documents/%s/' % e
                    for e in eadids]
    # using local dev urls for now
    harvest_urls.extend(['http://localhost:8000/groupsheets/%s/' % i for i in tei_ids])

    QUB_input = os.path.join(settings.BASE_DIR, 'data', 'fixtures', 'QUB_ms1204.html')
    # FIXME: can we find a better url for the Queen's Belfast Group collection ?
    QUB_URL = 'http://www.qub.ac.uk/directorates/InformationServices/TheLibrary/FileStore/Filetoupload,312673,en.pdf'

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        # if specific steps are specified, run only those
        # otherwise, run all steps
        all_steps = not any([options['harvest'], options['queens'],
                             options['related'], options['smush'],
                             options['gexf'], options['identify'],
                             options['connect'], options['local_uris']])

        # initialize graph persistence
        graph = rdflib.ConjunctiveGraph('Sleepycat')
        graph.open(settings.RDF_DATABASE, create=True)
        # if clear is specified, remove the entire db
        if options['clear']:
            if self.verbosity >= self.v_normal:
                print 'Removing %d contexts and %d triples from the current RDF graph' % \
                      (len(list(graph.contexts())), len(graph))
            # can't find a reliable way to remove all triples and contexts
            # so close the graph, remove everything, and start over
            graph.close()
            shutil.rmtree(settings.RDF_DATABASE)
            graph.open(settings.RDF_DATABASE, create=True)

        if all_steps or options['harvest']:
            self.stdout.write('-- Harvesting RDF from EmoryFindingAids related to the Belfast Group')

            HarvestRdf(self.harvest_urls,
                       find_related=True, verbosity=0,
                       graph=graph)

        if all_steps or options['queens']:
            self.stdout.write('-- Converting Queens University Belfast Group collection description to RDF')
            QUB(self.QUB_input, verbosity=0, graph=graph, url=self.QUB_URL)

        # FIXME: still needs some work
        if all_steps or options['related']:
            # FIXME: no longer quite accurate or what we need;
            # to keep rdf dataset as small as possible, should *only* grab attributes
            # we actually need to run the site
            self.stdout.write('-- Annotating graph with related information from VIAF, GeoNames, and DBpedia')
            Annotate(graph)
            # HarvestRelated(graph)   # old harvest , which is pulling too much data

        if all_steps or options['identify']:
            # smush any groupsheets in the data
            self.stdout.write('-- Identifying groupsheets')
            IdentifyGroupSheets(graph)

        if all_steps or options['smush']:
            # smush any groupsheets in the data
            self.stdout.write('-- Smushing groupsheet URIs')
            SmushGroupSheets(graph)

        if all_steps or options['connect']:
            # infer connections
            self.stdout.write('-- Inferring connections: groupsheet authors affiliated with group')
            InferConnections(graph)
            # TODO: groupsheet owner based on source collection

        if all_steps or options['gexf']:
            # generate gexf
            self.stdout.write('-- Generating network graph and saving as GEXF')
            Rdf2Gexf(graph, settings.GEXF_DATA)

        # TODO: create rdf profiles with local uris; get rid of person db model
        if all_steps or options['local_uris']:
            self.stdout.write('-- Generating local URIs based on the data')
            self.local_uris(graph)

        graph.close()

    def local_uris(self, graph):
        current_site = Site.objects.get(id=settings.SITE_ID)
        # generate local uris for persons who will have profile pages on the site

        # contexts(triple=None) # contexts by triple
        # for person in get_belfast_people():
        #     print person

        # return


        # NOTE: possibly iterate through people referenced in QUB first
        # should give us a good first-pass at good versions of names
        # and help clean up blank nodes for people without viaf/dbpedia ids
        # gqub = graph.get_context(self.QUB_URL)


        # local URIs for people in the group
        new_uris = {}
        # qub = graph.get_context(self.QUB_URL)
        for ctx in graph.contexts():
        # for ctx in [qub]:
            ctx_uris = {}
            for subject in ctx.subjects(rdflib.RDF.type, rdfns.SCHEMA_ORG.Person):
                person = RdfPerson(graph, subject)
                if not person.name:
                    print '** ERROR: no name for ', subject
                    continue
                # FIXME: utility method?
                uri = 'http://%s%s' % (
                    current_site.domain,
                    reverse('people:profile', args=[slugify(person.name)])
                    )

                print subject, ' ', person.name, ' ', uri
                # skip if already converted
                if uri == str(subject):
                    continue

                uriref = rdflib.URIRef(uri)
                # "smush" - convert all author identifiers to local uris
                # convert bnodes to local URIs so we can group authors
                # bnodes should only be converted in current context
                ctx_uris[subject] = uriref
                # other uris should be converted throughout the graph
                if not isinstance(subject, rdflib.BNode):
                    new_uris[subject] = uriref

                # set type to person (FIXME: redundant once smushed?)
                # ctx.add((uriref, rdflib.namespace.RDF.type, rdfns.SCHEMA_ORG.Person))
                # add preferred label for local use
                # FIXME: ensure name is firstname lastname and not all caps
                name = (uriref, rdflib.namespace.SKOS.preferredLabel, person.name)
                if name not in graph:
                    ctx.add(name)

                # check if not in graph already somewhere?
                if person.viaf_uri:
                    ctx.add((uriref, rdflib.OWL.sameAs, rdflib.URIRef(person.viaf_uri)))
                if person.dbpedia_uri:
                    ctx.add((uriref, rdflib.OWL.sameAs, rdflib.URIRef(person.dbpedia_uri)))


            # iterate over all triples in the old graph and convert
            # any uris in the new_uris dictionary to the smushed identifier
            # FIXME: copied from clean.py ; make re-usable function?
            for s, p, o in ctx:
                orig_s = s
                orig_o = o
                s = ctx_uris.get(s, s)
                o = ctx_uris.get(o, o)

                if orig_s != s or orig_o != o:
                    # if changed remove old version, add new version
                    ctx.remove((orig_s, p, orig_o))
                    ctx.add((s, p, o))





