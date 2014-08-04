#!/usr/bin/env python

# script to harvest and prep entire dataset, start to finish

from optparse import make_option
import os
import rdflib
import shutil

from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site

from belfast.rdf.harvest import HarvestRdf, Annotate, LocalRDF # HarvestRelated
from belfast.rdf.qub import QUB
from belfast.rdf.clean import SmushGroupSheets, IdentifyGroupSheets, \
    InferConnections, ProfileUris
from belfast.rdf import nx

class Command(BaseCommand):
    '''Harvest and prep Belfast Group RDF dataset'''
    help = __doc__

    v_normal = 1

    option_list = BaseCommand.option_list + (
        make_option('-H', '--harvest', action='store_true', help='Harvest RDFa'),
        make_option('--no-cache', action='store_true',
                    help='Request no cache when harvesting RDFa data',
                    default=False),
        make_option('-q', '--queens', action='store_true',
            help='Convert Queens University Belfast collection to RDF'),
        make_option('-i', '--identify', action='store_true',
            help='Identify Group sheets'),
        make_option('-s', '--smush', action='store_true',
            help='Smush groupsheet URIs and generate local profile URIs'),
        make_option('-r', '--related', action='store_true',
            help='Harvest related RDF from VIAF, GeoNames, and DBpedia'),
        make_option('-c', '--connect', action='store_true',
            help='Infer and make connections implicit in the data'),
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

    # harvest from production EmoryFindingAids site
    harvest_urls = ['http://findingaids.library.emory.edu/documents/%s/' % e
                    for e in eadids]

    rdf_fixture_dir = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures')

    # local html+rdfa fixtures; convert to graph via rdfa,
    # and add with webpage url as graph identifier
    local_rdf_fixtures = [
       os.path.join(rdf_fixture_dir, 'BelfastGroup_biographies.html'),
       os.path.join(rdf_fixture_dir, 'ednalongley_bio.html'),
       os.path.join(rdf_fixture_dir, 'pakenham_privatecoll.html'),
    ]

    QUB_input = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures', 'QUB_ms1204.html')
    # FIXME: can we find a better url for the Queen's Belfast Group collection ?
    # QUB_URL = 'http://www.qub.ac.uk/directorates/InformationServices/TheLibrary/FileStore/Filetoupload,312673,en.pdf'
    # NOTE: using version defined on the QUB class (currently same url)

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']

        # harvest from the current configured site
        current_site = Site.objects.get(id=settings.SITE_ID)
        self.harvest_urls.extend(['http://%s/groupsheets/%s/' % (current_site.domain.rstrip('/'), i)
                                  for i in self.tei_ids])

        # if specific steps are specified, run only those
        # otherwise, run all steps
        all_steps = not any([options['harvest'], options['queens'],
                             options['related'], options['smush'],
                             options['gexf'], options['identify'],
                             options['connect']])

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
            # inaccurate; also harvesting tei from local site

            HarvestRdf(self.harvest_urls,
                       find_related=True, verbosity=self.verbosity,
                       graph=graph, no_cache=options['no_cache'])
            # local info from RDF data - additional bios, Group sheet in private collection
            self.stdout.write('-- Adding RDF data from local fixtures')
            LocalRDF(graph, self.local_rdf_fixtures)

        if all_steps or options['queens']:
            self.stdout.write('-- Converting Queens University Belfast Group collection description to RDF')
            QUB(self.QUB_input, verbosity=self.verbosity, graph=graph,
                url=QUB.QUB_BELFAST_COLLECTION)

        if all_steps or options['identify']:
            # identify groupsheets in the data and add local groupsheet type if not present
            self.stdout.write('-- Identifying groupsheets')
            IdentifyGroupSheets(graph)

        if all_steps or options['smush']:
            # smush any groupsheets in the data
            self.stdout.write('-- Smushing groupsheet URIs and generating local profile URIs')
            # NOTE: might be nice to smush *after* cleaning up author names, but for some reason
            # that results in a number of authors/groupsheets getting dropped
            SmushGroupSheets(graph)
            ProfileUris(graph)

        if all_steps or options['related']:
            self.stdout.write('-- Annotating graph with related information from VIAF, GeoNames, and DBpedia')
            Annotate(graph)

        if all_steps or options['connect']:
            # infer connections
            self.stdout.write('-- Inferring connections: groupsheet time period, owner, authors affiliated with group')
            InferConnections(graph)
            # TODO: groupsheet owner based on source collection

        if all_steps or options['gexf']:
            # generate gexf
            self.stdout.write('-- Generating network graphs and saving as GEXF')
            nx.Rdf2Gexf(graph, settings.GEXF_DATA['full'])
            nx.BelfastGroupGexf(graph, settings.GEXF_DATA['bg1'])

        graph.close()

