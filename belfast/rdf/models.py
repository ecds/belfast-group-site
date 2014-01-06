import rdflib

from belfast import rdfns
from belfast.rdf import rdfmap

class RdfResource(rdflib.resource.Resource):
    '''Generic RDF :class:`~rdflib.resource.Resource` base class with
    common functionality, to be extended for specific rdf models.'''

    rdf_types =  rdfmap.ValueList(rdflib.RDF.type)
    # should be usable to confirm resource is expected type,
    # similar to requisite content models check in eulfedora
    # (requires naming convention for expected type...)

    def __repr__(self):
        # custom repr more readable than the default for rdflib resource
        return '<%s %s>' % (self.__class__.__name__, str(self))

    _name = rdfmap.Value(rdfns.SCHEMA_ORG.name)

    @property
    def name(self):
        l = self.graph.preferredLabel(self.identifier)
        return l if l else self._name


