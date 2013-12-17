import os
from django.conf import settings
from django.test import TestCase
import rdflib

from belfast.rdf.qub import QUB
from belfast import rdfns

class QUBTest(TestCase):

    input = os.path.join(settings.BASE_DIR, 'rdf', 'fixtures', 'QUB_ms1204_test.html')

    def test_rdf_conversion(self):
        # generate rdf from test input and then inspect the result
        graph = rdflib.ConjunctiveGraph()
        QUB(self.input, verbosity=0, graph=graph, url=QUB.QUB_BELFAST_COLLECTION)
        # NOTE: currently not testing top-level collection info

        groupsheets = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.BG.GroupSheet))
        self.assertEqual(3, len(groupsheets),
            'converted RDF should have 3 groupsheets for test input')

        people = list(graph.subjects(predicate=rdflib.RDF.type, object=rdfns.SCHEMA_ORG.Person))
        self.assertEqual(3, len(people),
            'converted RDF should have three people for test input')

        # order in rdf not guaranteed, so identify by last name
        people_by_name = {}
        for p in people:
            last_name = graph.value(p, rdfns.SCHEMA_ORG.familyName)
            people_by_name[str(last_name)] = p

        # authors in test fixture are hobsbaum, bond, croskery
        # test person info, with and without viaf id
        uri = people_by_name['Hobsbaum']
        self.assertEqual('http://viaf.org/viaf/91907300', str(uri))
        self.assertEqual('Philip', str(graph.value(uri, rdfns.SCHEMA_ORG.givenName)))
        self.assertEqual('Philip Hobsbaum', str(graph.value(uri, rdfns.SCHEMA_ORG.name)))

        uri = people_by_name['Bond']
        self.assert_('viaf.org' not in str(uri))
        self.assertEqual('John', str(graph.value(uri, rdfns.SCHEMA_ORG.givenName)))
        self.assertEqual('John Bond', str(graph.value(uri, rdfns.SCHEMA_ORG.name)))

        uri = people_by_name['Croskery']
        self.assert_('viaf.org' not in str(uri))
        self.assertEqual('Lynette', str(graph.value(uri, rdfns.SCHEMA_ORG.givenName)))
        self.assertEqual('Lynette Croskery', str(graph.value(uri, rdfns.SCHEMA_ORG.name)))
        # NOTE: input actually has Croskery, Lynette M.
        # do we care about the middle initial?

        # inspect groupsheets; find by author since order is not guaranteed
        groupsheets_by_author = {}
        for name, uri in people_by_name.iteritems():
            subj = list(graph.subjects(rdfns.DC.creator, uri))
            groupsheets_by_author[name] = subj[0]

        # all groupsheets should have the same types
        for uri in groupsheets_by_author.itervalues():
            rdf_types = list(graph.objects(uri, rdflib.RDF.type))
            self.assert_(rdfns.BG.GroupSheet in rdf_types)
            self.assert_(rdfns.BIBO.Manuscript in rdf_types)
            # TODO: could also test relation to archival collection

        # john bond - untitled short story, 2 pages, no date
        uri = groupsheets_by_author['Bond']
        self.assertEqual(None, graph.value(uri, rdfns.DC.title))
        self.assertEqual('short story', str(graph.value(uri, rdfns.SCHEMA_ORG.genre)))
        self.assertEqual(2, int(graph.value(uri, rdfns.BIBO.numPages)))
        self.assertEqual(None, graph.value(uri, rdfns.DC.date))

        # hobsbaum - single 6 page poem, no date
        uri = groupsheets_by_author['Hobsbaum']
        self.assertEqual('Study in a minor key', str(graph.value(uri, rdfns.DC.title)))
        # genre not picked up for poetry (?)
        # self.assertEqual('poem', str(graph.value(uri, rdfns.SCHEMA_ORG.genre)))
        self.assertEqual(6, int(graph.value(uri, rdfns.BIBO.numPages)))
        self.assertEqual(None, graph.value(uri, rdfns.DC.date))

        # croskery: 3 titles, date, 3 pages, short stories.
        uri = groupsheets_by_author['Croskery']
        rdf_types = list(graph.objects(uri, rdflib.RDF.type))
        # FIXME: blank node?
        title = graph.value(uri, rdfns.DC.title)
        # multiple titles; should be an rdf sequence
        self.assert_(isinstance(title, rdflib.BNode))
        self.assertEqual('The dress', str(graph.value(title, rdflib.RDF.first)))
        title_next = graph.value(title, rdflib.RDF.rest)
        self.assertEqual('The telegram', str(graph.value(title_next, rdflib.RDF.first)))
        title_next = graph.value(title_next, rdflib.RDF.rest)
        self.assertEqual('The daisy chain', str(graph.value(title_next, rdflib.RDF.first)))
        self.assertEqual(rdflib.RDF.nil, graph.value(title_next, rdflib.RDF.rest))
        self.assertEqual('short story', str(graph.value(uri, rdfns.SCHEMA_ORG.genre)))
        self.assertEqual(3, int(graph.value(uri, rdfns.BIBO.numPages)))
        self.assertEqual('1966-03-22', str(graph.value(uri, rdfns.DC.date)))

        # TODO: test anonymous groupsheet handling?
