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
        if self.datatype is not None:
            val = rdflib.Literal(val, datatype=self.datatype).toPython()

        if self.normalize:
            val = normalize_whitespace(val)
        return val


class Resource(object):

    def __init__(self, predicate, resource_type, is_object=True):
        self.predicate = predicate
        self.resource_type = resource_type
        self.is_object = is_object

    def __get__(self, obj, objtype):
        if self.is_object:
            rel = obj.value(self.predicate)
        else:
            rel = obj.subjects(self.predicate)
        if rel:
            return self.resource_type(obj.graph, rel.identifier)


class ResourceList(object):

    def __init__(self, predicate, resource_type, is_object=True):
        self.predicate = predicate
        self.resource_type = resource_type
        self.is_object = is_object

    def __get__(self, obj, objtype):
        if self.is_object:
            meth = obj.objects
        else:
            meth = obj.subjects
        return [self.resource_type(obj.graph, o.identifier)
                for o in meth(self.predicate)]


class Sequence(object):

    def __init__(self, predicate):
        self.predicate = predicate

    def __get__(self, obj, obtype):
        # convert from resource to standard blank node
        # since collection doesn't seem to handle resource
        bnode = rdflib.BNode(obj.value(self.predicate))
        # create a collection to allow treating as a list
        # return Collection(self.graph, bnode)
        titles = []
        # create a collection to allow treating as a list
        titles.extend(Collection(self.graph, bnode))
        return titles


class List(object):

    data = []

    def __init__(self, predicate):
        self.predicate = predicate

    def __get__(self, obj, objtype=None):  # objtype is class of object, e.g. RdfPerson
        self.data = list(obj.objects(rdflib.URIRef(self.predicate)))
        print self.data
        return self.data

    # @property
    # def data(self):
    #     # data in list form - basis for several other list-y functions
    #     return list(obj.objects(self.predicate))

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
