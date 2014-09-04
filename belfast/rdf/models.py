import rdflib

from belfast import rdfns
from belfast.rdf import rdfmap

class RdfResource(rdflib.resource.Resource):
    '''Generic RDF :class:`~rdflib.resource.Resource` base class with
    common functionality, to be extended for specific rdf models.'''

    #: list of rdf:type associated with this resource
    rdf_types =  rdfmap.ValueList(rdflib.RDF.type)
    # should be usable to confirm resource is expected type,
    # similar to requisite content models check in eulfedora
    # (requires naming convention for expected type...)

    def __repr__(self):
        # custom repr more readable than the default for rdflib resource
        return '<%s %s>' % (self.__class__.__name__, str(self))

    _name = rdfmap.Value(rdfns.SCHEMA_ORG.name)

    @property
    def preferred_label(self):
        '''Preferred label for this resource;
        uses :meth:`~rdflib.graph.Graph.preferredLabel`.  If multiple
        preferred labels are found, the first one is used.'''
        labels = self.graph.preferredLabel(self)
        # list of tuples: label type (preflabel or label), value
        if labels:
            return labels[0][1]

    @property
    def name(self):
        'alias for :attr:`preferred_label`'
        l = self.preferred_label
        return l if l else self._name


