from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse


from belfast.people.rdfmodels import profile_people, RdfPerson


class ProfileSitemap(Sitemap):
    # sitemap for profiles and browse list of people

    # No known/reliable change frequency; probably won't change much...
    # changefreq = 'yearly'

    extra_pages = ['list']

    def items(self):
        people = profile_people()
        return self.extra_pages + [p for p in people]

    def location(self, item):
        if isinstance(item, basestring):
            return reverse('people:%s' % item)
        return reverse('people:profile', args=[item.slug])

    # TODO: last modified? might be able to get based on last run of dataset
