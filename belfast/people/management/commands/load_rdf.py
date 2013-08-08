import glob
import rdflib
import os
import sys
import time

from progressbar import ProgressBar, Bar, Percentage, ETA, SimpleProgress

from django.conf import settings
from django.core.management.base import BaseCommand

from belfast.util import rdf_dburi_from_settings

# if possible, make this more efficient so we only re-load what
# has changed or been added since the last load

# FIXME: dbpedia includes a ton of stuff we don't care about
# how to ignore? should we not be ingesting locally?


class Command(BaseCommand):
    '''load rdf data into the database'''
    help = __doc__

    def handle(self, *filenames, **options):
        self.verbosity = options['verbosity']

        # using a persistent store requires a primary identifier
        ident = rdflib.URIRef('http://belfastgroup.ecds.emory.edu/')
        # NOTE: identifier is graph context; can we use this to track
        # originally harvested location?
        datastore = rdflib.plugin.get("SQLAlchemy", rdflib.store.Store)(identifier=ident)
        graph = rdflib.graph.Graph(datastore, identifier=ident)
        dburi = rdf_dburi_from_settings()
        graph.open(dburi, create=True)


        # initalize progress bar
        progress = None

        if filenames:
            total = len(filenames)
        else:
            total = self.count_files()
        # init progress bar if available and we're checking enough objects
        if total > 10 and os.isatty(sys.stderr.fileno()):
            widgets = [Percentage(), ' (', SimpleProgress(), ')',
                       Bar(), ETA()]
            progress = ProgressBar(widgets = widgets, maxval=total).start()
        else:
            prorgress = None

        filecount = 0
        errcount = 0
        total = 0
        start = time.time()

        if filenames:
            for infile in filenames:
                tmp_graph = rdflib.graph.Graph()
                basename, ext = os.path.splitext(infile)
                fmt = ext.strip('.')
                try:
                    tmp_graph.parse(infile, format=fmt)
                    filecount += 1

                    # somehow, rdflib-sqlalchemy doesn't seem able to handle unicode
                    # we're not really using the other language terms,
                    # so just loop thru triples and add to the db, ignoring
                    # whichever ones rdflib-sqlalchemy can't handle
                    triple_error = 0
                    total_triples = len(tmp_graph)
                    for triple in tmp_graph:
                        try:
                            graph.add(triple)
                        except:
                            triple_error += 1

                    if triple_error:
                        print 'Error adding %d triples out of %d' % (triple_error, total_triples)

                except Exception as err:
                    print 'Failed to parse file %s: %s' % (infile, err) # was log error
                    errcount += 1



                total += 1
                if progress is not None:
                    progress.update(total)

        else:

            # TODO: log time it takes to parse and load, totalnumber of files
            for infile in glob.iglob(os.path.join(settings.RDF_DATA_DIR, '*.xml')):
                try:
                    graph.parse(infile, format='xml')
                    filecount += 1
                except Exception as err:
                    print 'Failed to parse file %s: %s' % (infile, err) # was log error
                    errcount += 1

                total += 1
                if progress is not None:
                    progress.update(total)

            # TODO: make secondary data optional?
            for infile in glob.iglob(os.path.join(settings.RDF_DATA_DIR, '*', '*.xml')):
                try:
                    graph.parse(infile, format='xml')
                    filecount += 1
                except Exception as err:
                    print 'Failed to parse file %s: %s' % (infile, err)  # was log error
                    errcount += 1

                total += 1
                if progress is not None:
                    progress.update(total)

        if progress is not None:
            progress.finish()

        print 'Loaded %d RDF documents in %.02f sec (%d errors)' % \
                     (filecount, time.time() - start, errcount)  # was log debug

    def count_files(self):
        total = 0
        subdirs = []
        for name in os.listdir(settings.RDF_DATA_DIR):
            fullpath = os.path.join(settings.RDF_DATA_DIR, name)
            if os.path.isfile(fullpath) and name.endswith('.n3'):
               total += 1
            elif os.path.isdir(fullpath) and not name.startswith('.'):
                subdirs.append(fullpath)

        # TODO: if including secondary
        for sd in subdirs:
            total += len([name for name in os.listdir(sd)
                          if os.path.isfile(os.path.join(sd, name)) and name.endswith('.n3')])

        return total


