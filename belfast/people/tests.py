from django.test import TestCase
from django.core.urlresolvers import reverse


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

