from django.conf.urls import patterns, url
from django.contrib.flatpages import views as fpviews


urlpatterns = patterns('',
    url(r'^overview/$', fpviews.flatpage, {'url': '/overview/'},
        name='overview'),
    url(r'^biographies/$', fpviews.flatpage, {'url': '/biographies/'},
        name='bios'),
    url(r'^credits/$', fpviews.flatpage, {'url': '/credits/'},
        name='credits'),
)