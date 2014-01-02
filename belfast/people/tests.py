from django.test import TestCase
from django.core.urlresolvers import reverse
from mock import patch
from networkx.readwrite import gexf
from os import path
import rdflib

from belfast.people.rdfmodels import RdfPerson, RdfLocation, RdfOrganization

FIXTURE_DIR = path.join(path.dirname(path.abspath(__file__)), 'fixtures')


class PeopleViewsTest(TestCase):
    graph = rdflib.Graph()
    graph.parse(path.join(FIXTURE_DIR, 'testdata.rdf'))

    nx_graph = gexf.read_gexf(path.join(FIXTURE_DIR, 'testdata.gexf'))

    def setUp(self):
        self.person = RdfPerson(self.graph,
                                rdflib.URIRef('http://example.com/people/michael-longley/'))

    @patch('belfast.people.rdfmodels.network_data')
    @patch('belfast.people.rdfmodels.rdf_data')
    @patch('belfast.people.views.rdf_data')
    def test_profile(self, mockrdfv, mockrdfm, mocknx):
        # needs to be mocked in view and rdfmodel
        # test against fixture rdf/gexf data
        mockrdfm.return_value = mockrdfv.return_value = self.graph
        mocknx.return_value = self.nx_graph

        # currently, id format is viaf:####
        # - not in domain:id format
        response = self.client.get(reverse('people:profile',
                                           kwargs={'id': 'not-a-viaf-id'}))
        self.assertEqual(404, response.status_code,
                         'profile should return 404 for invalid person id')

        # test person from fixture data
        response = self.client.get(reverse('people:profile',
                                           kwargs={'id': 'michael-longley'}))
        self.assertEqual(200, response.status_code,
                         'profile should return 200 for valid person id')
        # spot-check profile info
        self.assertContains(
            response, '<h1>%s</h1>' % self.person.name, html=True,
            msg_prefix='name should be used for profile page title')
        self.assertContains(
            response, 'Born %s' % self.person.birthdate,
            msg_prefix='birthdate should be included if present')
        self.assertContains(
            response, self.person.dbpedia_description,
            msg_prefix='dbpedia description should be included on profile')
        self.assertContains(
            response, '<p><b>Occupation:</b> %s</p>' % self.person.occupation[0],
            msg_prefix='occupations should be listed')
        # locations
        for loc in self.person.locations:
            # for some reason, dbpedia name isn't coming through in test data
            # just skip it for now
            if loc.name is None:
                continue

            self.assertContains(
                response, loc.name,
                msg_prefix='location %s should be listed on profile' % loc.name)

        # connected people
        for p in self.person.connected_people:
            self.assertContains(
                response, p.fullname,
                msg_prefix='connected person name %s should be listed on profile'
                % p.fullname)

        # connected orgs
        for o in self.person.connected_organizations:
            self.assertContains(
                response, o.name,
                msg_prefix='connected organization %s should be listed on profile'
                % o.name)


class RdfPersonTest(TestCase):
    graph = rdflib.Graph()
    graph.parse(path.join(FIXTURE_DIR, 'testdata.rdf'))

    nx_graph = gexf.read_gexf(path.join(FIXTURE_DIR, 'testdata.gexf'))

    def setUp(self):
        self.person = RdfPerson(self.graph,
                                rdflib.URIRef('http://example.com/people/michael-longley/'))

    def test_basic_properties(self):
        self.assertEqual('Michael Longley', unicode(self.person.name))
        self.assertEqual('Longley', unicode(self.person.lastname))
        self.assertEqual('Michael', unicode(self.person.firstname))
        self.assertEqual('Michael Longley', self.person.fullname)
        # birth date is just a string for now...
        self.assertEqual('1939-07-27', unicode(self.person.birthdate))
        self.assertEqual('Poet', unicode(self.person.occupation[0]))
        self.assertEqual(rdflib.URIRef('http://viaf.org/viaf/39398205/'),
                         self.person.viaf_uri)
        self.assertEqual(rdflib.URIRef('http://dbpedia.org/resource/Michael_Longley'),
                         self.person.dbpedia_uri)


    def test_locations(self):
        birthplace = self.person.birthplace
        self.assert_(isinstance(birthplace, RdfLocation))
        self.assertEqual('Belfast, Northern Ireland', unicode(birthplace.name))

        # set of home and work locations
        locations = self.person.locations
        print 'locations = ', locations
        self.assertEqual(5, len(locations))
        self.assert_(isinstance(locations[0], RdfLocation))
        loc_names = [unicode(l.name) for l in locations]
        self.assert_('Belfast' in loc_names)
        self.assert_('Dublin' in loc_names)
        self.assert_('London' in loc_names)

    def test_dbpedia_description(self):
        self.assertEqual('Michael Longley, CBE (born 27 July 1939) is a Northern Irish poet from Belfast.',
                         unicode(self.person.dbpedia_description))

    @patch('belfast.people.rdfmodels.network_data')
    @patch('belfast.people.rdfmodels.rdf_data')
    def test_connected_people(self, mockrdf, mocknx):
        # test against fixture rdf/gexf data
        mockrdf.return_value = self.graph
        mocknx.return_value = self.nx_graph
        # NOTE: current nx gexf based on viaf uri instead of local one
        # TODO: regenerate text fixture (at least gexf) based on current process
        person = RdfPerson(self.graph, rdflib.URIRef('http://viaf.org/viaf/39398205/'))
        people = person.connected_people
        self.assert_(isinstance(people.keys()[0], RdfPerson))
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

    @patch('belfast.people.rdfmodels.network_data')
    @patch('belfast.people.rdfmodels.rdf_data')
    def test_connected_organizations(self, mockrdf, mocknx):
        # test against fixture rdf/gexf data
        mockrdf.return_value = self.graph
        mocknx.return_value = self.nx_graph
        # same note as above for gexf / local uri
        person = RdfPerson(self.graph, rdflib.URIRef('http://viaf.org/viaf/39398205/'))
        orgs = person.connected_organizations
        self.assert_(isinstance(orgs.keys()[0], RdfOrganization))
        names = dict((unicode(o.name), rels) for o, rels in orgs.iteritems())
        self.assert_('Belfast Group' in names)
        self.assert_('Royal Society of Literature' in names)
        self.assert_('Seamus Heaney' not in names)
        self.assert_('affiliation' in names['Belfast Group'])
