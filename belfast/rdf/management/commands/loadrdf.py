#!/usr/bin/env python

# script to dump rdf data from rdf database

from optparse import make_option
import sys

from rdflib import ConjunctiveGraph

from django.core.management.base import BaseCommand
from belfast.util import rdf_data


class Command(BaseCommand):
    '''Load serialized RDF data in the configured rdf database'''
    help = __doc__

    v_normal = 1

    # NOTE: currently belfast data can only be exported successfully in XML
    # and trix serialization formats; leaving here for convenience
    option_list = BaseCommand.option_list + (
        make_option('-f', '--format',
            choices=('xml', 'n3', 'turtle', 'nt', 'pretty-xml', 'trix'),
            default='xml',
            help='RDF import format (default: xml)'),
    )

    def handle(self, filename, *args, **options):
        graph = rdf_data()
        size = len(graph)
        verbosity = options.get('verbosity', self.v_normal)

        graph.parse(filename, format=options['format'])

        if verbosity >= self.v_normal:
            print >> sys.stderr, "Loaded %d triples" % (len(graph) - size)
