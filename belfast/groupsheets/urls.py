from django.conf.urls import patterns, include, url
from belfast.groupsheets import views

urlpatterns = patterns('',
    url(r'^(?P<id>[a-z0-9_-]+)/$', views.view_sheet, name='view'),
)
