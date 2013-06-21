from django.conf.urls import patterns, include, url
from belfast.pages import views as pages_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', pages_views.site_index, name='site-index'),
    url(r'^group-sheets/', include('belfast.groupsheets.urls',
        namespace='groupsheets')),
    url(r'^people/', include('belfast.people.urls',
        namespace='people')),
    url(r'^', include('belfast.pages.urls')),
    # Examples:
    # url(r'^$', 'belfast.views.home', name='home'),
    # url(r'^belfast/', include('belfast.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^tinymce/', include('tinymce.urls')),
)
