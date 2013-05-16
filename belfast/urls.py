from django.conf.urls import patterns, include, url
from belfast.pages import views as pages_views

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', pages_views.site_index, name='site-index'),
    # Examples:
    # url(r'^$', 'belfast.views.home', name='home'),
    # url(r'^belfast/', include('belfast.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
