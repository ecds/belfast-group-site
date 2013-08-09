from django.db import models
import logging

from belfast.groupsheets.fields import SeparatedValuesField
from belfast.people.models import Person

logger = logging.getLogger(__name__)

class ArchivalCollection(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()


class GroupSheet(models.Model):
    title_list = SeparatedValuesField(token='|')
    # or should poems be separate? where we have data: uri, places, etc
    date = models.CharField(max_length=50)
    # or should poems be separate? where we have data: uri, places, etc
    author = models.ForeignKey(Person)   # possibly multiple?
    # one to many archival collection

