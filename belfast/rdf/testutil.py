import os
from django.conf import settings
import rdflib
import shutil
import sys

# when nose is available, define a plugin
try:

    from nose.plugins.base import Plugin

    class RdfTestDatabase(Plugin):

        def begin(self):
            self.stored_rdf_database = getattr(settings, "RDF_DATABASE", None)

            if getattr(settings, "RDF_TEST_DATABASE", None) is not None:
                settings.RDF_DATABASE = settings.RDF_TEST_DATABASE
            else:
                default_test_db = os.path.join(settings.BASE_DIR, 'test-belfastrdf.bdb')
                settings.RDF_DATABASE = default_test_db
                # NOTE: it would be nice to generate the testdb name from the original
                # rdf db name, but requires path parsing (not worth the trouble at the moment)
                # settings.RDF_DATABASE = getattr(settings, 'RDF_DATABASE', default_test_db)

            print >> sys.stderr, "Creating test RDF Database: %s" % \
                settings.RDF_DATABASE

            # create empty rdf db
            graph = rdflib.ConjunctiveGraph('Sleepycat')
            graph.open(settings.RDF_DATABASE, create=True)

            # track that we are in test mode, so db wrapper can skip closing
            settings.RDF_DATABASE_TESTMODE = True

        def finalize(self, result):
            print >> sys.stderr, "Removing test RDF Database: %s" % settings.RDF_DATABASE
            shutil.rmtree(settings.RDF_DATABASE)
            if self.stored_rdf_database is not None:
                # print >> sys.stderr, "Restoring RDF Database: %s" \
                #     % self.stored_rdf_database
                settings.RDF_DATABASE = self.stored_rdf_database

            settings.RDF_DATABASE_TESTMODE = False

        def help(self):
            return 'Setup and use a test RDF database for tests.'

except ImportError:
    pass
