from django.db import models
import logging

from belfast.groupsheets.fields import SeparatedValuesField
from belfast.people.models import Person

logger = logging.getLogger(__name__)




class ArchivalCollection(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(unique=True)

    # TODO: short name?

    class Meta:
        verbose_name = 'Archival Collection'

    def __unicode__(self):
        return self.name


class GroupSheet(models.Model):
    # title_list = models.TextField(max_length=255)
    title_list = SeparatedValuesField(token='|')
    url = models.URLField(unique=True, blank=True, null=True)
    tei_id = models.CharField(max_length=30, blank=True, null=True)

    # or should poems be separate? where we have data: uri, places, etc
    date = models.CharField(max_length=50, blank=True, null=True)
    # or should poems be separate? where we have data: uri, places, etc
    author = models.ForeignKey(Person)   # possibly multiple?
    # many to many archival collection
    sources = models.ManyToManyField(ArchivalCollection)

    # todo: time period (BG phase 1/2)

    class Meta:
        verbose_name = 'Group Sheet'

    # FIXME: for some reason this was breaking admin edit form (?)
    # def __unicode__(self):
    #     return self.titles or ''

    def titles(self):
        return ', '.join(self.title_list)



