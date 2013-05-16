from django.conf.urls import patterns, include, url
from django.contrib.flatpages import views as fpviews


urlpatterns = patterns('',
    url(r'^overview/$', fpviews.flatpage, {'url': '/overview/'},
        name='overview'),
    url(r'^biographies/$', fpviews.flatpage, {'url': '/biographies/'},
        name='bios'),
)