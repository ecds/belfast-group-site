from djangotoolbox.db.base import NonrelDatabaseFeatures, \
    NonrelDatabaseOperations, NonrelDatabaseWrapper, NonrelDatabaseClient, \
    NonrelDatabaseValidation, NonrelDatabaseIntrospection, \
    NonrelDatabaseCreation

import rdflib
from rdflib.store import NO_STORE, VALID_STORE

import logging


logger = logging.getLogger(__name__)


## NOTE: this is a *bare-minimum* backend, not intended for use with django
# models, but only to allow accessing the database connection and allow django
# to close the database connection automaticcaly


class DatabaseCreation(NonrelDatabaseCreation):
    pass

class DatabaseFeatures(NonrelDatabaseFeatures):
    can_return_id_from_insert = False
    supports_primary_key_on = set()

class DatabaseOperations(NonrelDatabaseOperations):
    compiler_module = __name__.rsplit('.', 1)[0] + '.compiler'

class DatabaseClient(NonrelDatabaseClient):
    pass

class DatabaseValidation(NonrelDatabaseValidation):
    pass

class DatabaseIntrospection(NonrelDatabaseIntrospection):
    pass

class DatabaseWrapper(NonrelDatabaseWrapper):
    def __init__(self, *args, **kwds):
        super(DatabaseWrapper, self).__init__(*args, **kwds)
        self.features = DatabaseFeatures(self)
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.validation = DatabaseValidation(self)
        self.introspection = DatabaseIntrospection(self)

        logger.debug('opening Sleepycat RDF DB connection')
        self.db_connection = rdflib.ConjunctiveGraph('Sleepycat')
        rval = self.db_connection.open(self.settings_dict['NAME'], create=False)

        if rval == NO_STORE:
            # if store doesn't exist yet, go ahead and create it
            logger.debug('Sleepycat RDF DB does not yet exist, creating it')
            self.db_connection.open(self.settings_dict['NAME'], create=True)

        elif rval != VALID_STORE:
            logger.error('Sleepycat RDF DB is not valid')


    def close(self):
        if self.db_connection.store.is_open():
            logger.debug('closing Sleepycat RDF DB connection')
            self.db_connection.close()

