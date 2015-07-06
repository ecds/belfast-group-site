from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from belfast.groupsheets.rdfmodels import TeiGroupSheet, TeiDocument


class GroupSheetsSitemap(Sitemap):
    # sitemap for TEI groupsheets and browse list of groupsheets

    # No known/reliable change frequency; probably won't change...
    # changefreq = 'yearly'

    extra_pages = ['list']

    def items(self):
        results = TeiGroupSheet.objects.only('id', 'last_modified').all()
        # convert querystring result into a list to allow combining
        return self.extra_pages + [r for r in results]

    def location(self, groupsheet):
        if isinstance(groupsheet, basestring):
            return reverse('groupsheets:%s' % groupsheet)
        return reverse('groupsheets:view', args=[groupsheet.id])

    def lastmod(self, groupsheet):
        if isinstance(groupsheet, basestring):
            return None
            # NOTE: possibly date of current released version of the code?

        return groupsheet.last_modified


class XmlDocumentsSitemap(Sitemap):
    # sitemap for XML documents that comprise the groupsheets

    def items(self):
        results = TeiDocument.objects.only('document_name', 'last_modified').all()
        return results

    def location(self, document):
        return reverse('groupsheets:xml', args=[document.document_name])

    def lastmod(self, document):
        return document.last_modified