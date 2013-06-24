from django.test import TestCase
from django.core.urlresolvers import reverse
from mock import patch
from networkx.readwrite import gexf
from os import path
import rdflib

from belfast.people.models import RdfPerson, RdfLocation

FIXTURE_DIR = path.join(path.dirname(path.abspath(__file__)), 'fixtures')


class PeopleViewsTest(TestCase):

    def test_profile(self):
        # currently, id format is viaf:####
        # - not in domain:id format
        response = self.client.get(reverse('people:profile',
                                           kwargs={'id': 'not-a-viaf-id'}))
        self.assertEqual(404, response.status_code,
                         'profile should return 404 for invalid person id')
        # - domain not viaf
        response = self.client.get(reverse('people:profile',
                                           kwargs={'id': 'dbpedia:1234'}))
        self.assertEqual(404, response.status_code,
                         'profile should return 404 for unsupported person id')
        # valid viaf id but not a person
        response = self.client.get(reverse('people:profile',
                                           kwargs={'id': 'viaf:127261399'}))
        self.assertEqual(404, response.status_code,
                         'profile should return 404 for non-person id')


class RdfPersonTest(TestCase):
    graph = rdflib.Graph()
    graph.parse(path.join(FIXTURE_DIR, 'testdata.rdf'))

    nx_graph = gexf.read_gexf(path.join(FIXTURE_DIR, 'testdata.gexf'))

    def setUp(self):
        self.person = RdfPerson(self.graph,
                                rdflib.URIRef('http://viaf.org/viaf/39398205/'))

    def test_basic_properties(self):
        self.assertEqual('Michael Longley', unicode(self.person.name))
        self.assertEqual('Longley', unicode(self.person.lastname))
        self.assertEqual('Michael', unicode(self.person.firstname))
        self.assertEqual('Michael Longley', self.person.fullname)
        # birth date is just a string for now...
        self.assertEqual('1939-07-27', unicode(self.person.birthdate))
        self.assertEqual('Poet', unicode(self.person.occupation[0]))
        self.assertEqual('viaf:39398205', self.person.short_id)

    def test_locations(self):
        birthplace = self.person.birthplace
        self.assert_(isinstance(birthplace, RdfLocation))
        self.assertEqual('Belfast, Northern Ireland', unicode(birthplace.name))

        # set of home and work locations
        locations = self.person.locations
        self.assertEqual(4, len(locations))
        self.assert_(isinstance(locations[0], RdfLocation))
        loc_names = [unicode(l.name) for l in locations]
        self.assert_('Belfast' in loc_names)
        self.assert_('Dublin' in loc_names)
        self.assert_('London' in loc_names)

    def test_dbpedia_description(self):
        self.assertEqual('Michael Longley, CBE (born 27 July 1939) is a Northern Irish poet from Belfast.',
                         unicode(self.person.dbpedia_description))

    @patch('belfast.people.models.network_data')
    @patch('belfast.people.models.rdf_data')
    def test_connected_people(self, mockrdf, mocknx):
        # test against fixture rdf/gexf data
        mockrdf.return_value = self.graph
        mocknx.return_value = self.nx_graph
        people = self.person.connected_people
        # convert into dict of string, list for easier testing
        names = dict((unicode(p.name), rels) for p, rels in people.iteritems())
        self.assert_('Edna Longley' in names)
        self.assert_('Seamus Heaney' in names)
        self.assert_('Arthur Terry' in names)
        # orgs should be filtered out
        self.assert_('Belfast Group' not in names)
        # relations:
        self.assert_('spouse' in names['Edna Longley'])
        self.assert_('colleague' in names['Seamus Heaney'])
        self.assert_('knows' in names['Seamus Heaney'])
