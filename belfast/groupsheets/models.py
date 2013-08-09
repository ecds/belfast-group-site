from django.db import models
import logging

from belfast.groupsheets.fields import SeparatedValuesField

logger = logging.getLogger(__name__)


class DbGroupSheet(models.Model):
    title_list = SeparatedValuesField(token='|')
    date = models.CharField(max_length=50)
    # or should poems be separate? where we have data: uri, places, etc
    author = models.ForeignKey(Person)   # possibly multiple?


class ArchivalCollection(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
