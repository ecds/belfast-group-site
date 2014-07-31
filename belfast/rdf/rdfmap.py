## descriptors for RDF
# intended for use with rdflib.resource.Resource
import rdflib
from rdflib.collection import Collection

from belfast.util import normalize_whitespace

# rename to rdfmap?

# consider taking multiple predicates (assume OR; perhaps also assume order for single)

# refer to
# http://www.openvest.com/trac/browser/rdfalchemy/trunk/rdfalchemy/descriptors.py
# TODO: cache results in obj.__dict__ ? or is rdf lookup fast enough that's unnecessary?


class Value(object):
    """A data descriptor that gets rdf a single value.
    """

    def __init__(self, predicate, datatype=None, normalize=False):
        self.predicate = predicate
        self.datatype = datatype
        self.normalize = normalize

    def __get__(self, obj, objtype=None):
        val = obj.value(self.predicate)
        # if we got a 'none' return as is (don't convert to "None")
        if val is None:
            return val
        if self.datatype is not None:
            val = rdflib.Literal(val, datatype=self.datatype).toPython()
        elif isinstance(val, rdflib.Literal):
            val = val.toPython()

        if self.normalize:
            val = normalize_whitespace(val)
        return val


class Resource(object):
    '''RDF descriptor to access an RDF resoure for a specified predicate.

    :params predicate: RDF predicate URI to be used for identifying the resource
    :params resource_type: class to be used for initializing RDF resource
        (i.e. a subclass of :class:`belfast.rdf.models.RdfResource` or
        the more general :class:`rdflib.resource.Resource`)
    :params is_object: boolean flag, indicates whether resource is the
        object or subject of the specified predicate (defaults to object)
    '''

    def __init__(self, predicate, resource_type, is_object=True):
        self.predicate = predicate
        self.resource_type = resource_type
        self.is_object = is_object

    def __get__(self, obj, objtype):
        # need to use subjects/objects instead of value to get a resource
        # and for consistency with ResourceList
        if self.is_object:
            meth = obj.objects
        else:
            meth = obj.subjects

        # these methods return multiple; for now just grab the first one
        rels = list(meth(self.predicate))
        # NOTE: could probably use as generator without forcing to list instead?
        if rels:
            return self.resource_type(obj.graph, rels[0].identifier)


class ResourceList(object):
    '''RDF descriptor to access multiple values for the same predicate as a list.

    :params predicate: RDF predicate URI to be used for identifying resources
    :params resource_type: class to be used for initializing RDF resource
        (i.e. a subclass of :class:`belfast.rdf.models.RdfResource` or
        the more general :class:`rdflib.resource.Resource`)
    :params is_object: boolean flag, indicates whether resources are
        objects or subjects of the specified predicate (defaults to object)
    :params sort: optional sort parameter, for sorting results after they are
        identified and initialized as the requested resource type; should be
        a key or lambda that can be passed to :meth:`sorted`

    '''

    def __init__(self, predicate, resource_type, is_object=True, sort=None):
        self.predicate = predicate
        self.resource_type = resource_type
        self.is_object = is_object
        self.sort = sort

    def __get__(self, obj, objtype):
        if self.is_object:
            meth = obj.objects
        else:
            meth = obj.subjects

        results = [self.resource_type(obj.graph, o.identifier)
                   for o in meth(self.predicate)]
        if self.sort:
            return sorted(results, key=self.sort)
        else:
            return results


class Sequence(object):
    '''RDF descriptor for accessing values contained in an rdf sequence
    as a python list.'''

    def __init__(self, predicate):
        self.predicate = predicate

    def __get__(self, obj, obtype):
        # convert from resource to standard blank node
        # since collection doesn't seem to handle resource
        bnode = rdflib.BNode(obj.value(self.predicate))
        # create a collection to allow treating as a list
        # return Collection(self.graph, bnode)
        terms = []
        # create a collection to allow treating as a list
        terms.extend(Collection(obj.graph, bnode))

        return [t.toPython() if isinstance(t, rdflib.Literal) else t
                     for t in terms]

class ValueList(object):

    data = []

    def __init__(self, predicate, transitive=False):
        self.predicate = predicate
        self.transitive = transitive

    def __get__(self, obj, objtype=None):  # objtype is class of object, e.g. RdfPerson
        # TODO: share datatype logic, whitespace normalization with value
        if self.transitive:
            meth = obj.graph.transitive_objects
        else:
            meth = obj.graph.objects

        self.data = [o.toPython() if isinstance(o, rdflib.Literal) else o
                     for o in meth(obj.identifier, rdflib.URIRef(self.predicate))]
        return self.data

    # @property
    # def data(self):
    #     # data in list form - basis for several other list-y functions
    #     return list(obj.objects(self.predicate))

    # NOTE: list methods pretty much copied from xmlmap; probably needs testing/revision

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return str(self.data)

    def __len__(self):
        return len(self.data)

    def __contains__(self, item):
        return item in self.data

    def __iter__(self):
        for d in self.data:
            yield d

    def __eq__(self, other):
        # FIXME: is any other comparison possible ?
        return self.data == other

    def __ne__(self, other):
        return self.data != other

    def _check_key_type(self, key):
        # check argument type for getitem, setitem, delitem
        if not isinstance(key, (slice, int, long)):
            raise TypeError
        assert not isinstance(key, slice), "Slice indexing is not supported"

    def __getitem__(self, key):
        self._check_key_type(key)
        return self.data[key]
