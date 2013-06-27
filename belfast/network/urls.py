from django.conf.urls import patterns, include, url
from belfast.network import views

urlpatterns = patterns('',
    url(r'^$', views.full, name='full'),
    url(r'^full.json$', views.full_js, name='full-js'),
)
