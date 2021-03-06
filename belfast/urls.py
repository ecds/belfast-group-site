from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView
from django.views.generic.base import RedirectView
from django.contrib.sitemaps import FlatPageSitemap

from belfast.pages import views as pages_views
from belfast.sitemaps import OtherViewsSitemap
from belfast.groupsheets.sitemaps import GroupSheetsSitemap, XmlDocumentsSitemap
from belfast.people.sitemaps import ProfileSitemap

# enable django db-admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', pages_views.site_index, name='site-index'),
    url(r'^groupsheets/', include('belfast.groupsheets.urls',
        namespace='groupsheets')),
    url(r'^people/', include('belfast.people.urls',
        namespace='people')),
    url(r'^network/', include('belfast.network.urls',
        namespace='network')),
    url(r'^', include('belfast.pages.urls')),
    # add redirect for favicon at root of site
    (r'^favicon\.ico$', RedirectView.as_view(url='/static/img/favicon.ico', permanent=True)),
    # Examples:
    # url(r'^$', 'belfast.views.home', name='home'),
    # url(r'^belfast/', include('belfast.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^tinymce/', include('tinymce.urls')),


    # belfast group rdf ontology
    #   http://belfastgroup.library.emory.edu/ontologies/2013/6/belfastgroup/
    url(r'^ontologies/2013/6/belfastgroup/$',
        TemplateView.as_view(template_name='bg-ontology.xml',
        content_type='text/xml'), name='bg-ontology'),
    url(r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt',
        content_type='text/plain'), name='robots.txt'),
)

# xml sitemaps for search-engine discovery
sitemaps = {
    'groupsheets': GroupSheetsSitemap,
    'xmlgroupsheets': XmlDocumentsSitemap,
    'profiles': ProfileSitemap,
    'flatpages': FlatPageSitemap,
    'other': OtherViewsSitemap
}

urlpatterns += patterns('django.contrib.sitemaps.views',
    (r'^sitemap\.xml$', 'index', {'sitemaps': sitemaps}),
    (r'^sitemap-(?P<section>.+)\.xml$', 'sitemap', {'sitemaps': sitemaps}),
)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
