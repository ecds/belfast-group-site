## descriptors for RDF
# intended for use with rdflib.resource.Resource
import rdflib

# rename to rdfmap?

# consider taking multiple predicates (assume OR; perhaps also assume order for single)

class Value(object):
    """A data descriptor that gets rdf a single value.
    """

    def __init__(self, predicate, datatype=None):
        self.predicate = predicate
        self.datatype = datatype

    def __get__(self, obj, objtype=None):
        val = obj.value(self.predicate)
        if self.datatype is not None:
            val = rdflib.Literal(val, datatype=self.datatype)
            return val.toPython()
        else:
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


class List(object):

    data = []

    def __init__(self, predicate):
        self.predicate = predicate

    def __get__(self, obj, objtype=None):  # objtype is class of object, e.g. RdfPerson
        # FIXME: why does this work on the class but not as descriptor?!
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
