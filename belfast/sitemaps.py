from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse


class OtherViewsSitemap(Sitemap):
    # sitemap for various urls that are not model/data based
    # but should still be indexed

    views = ['network:force-graph', 'network:chord',
        'network:bg', 'network:map', 'bg-ontology']

    def items(self):
        return self.views

    def location(self, view):
        return reverse(view)

    # no last modified for these views
