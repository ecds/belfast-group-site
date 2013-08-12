import logging
from django.db import models
from django.utils.text import slugify
import rdflib

from belfast.util import rdf_data
from belfast.people.rdfmodels import RdfPerson

logger = logging.getLogger(__name__)


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField()
    # links to other records
    dbpedia = models.URLField(max_length=255, blank=True, null=True, unique=True)
    viaf = models.URLField(max_length=255, blank=True, null=True, unique=True)

    class Meta:
        verbose_name_plural = "people"

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def name(self):
        return '%s %s' % (self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        # generate slug if not set
        if not self.slug:
            self.slug = slugify(self.name)
        super(Person, self).save(*args, **kwargs)

    @property
    def uriref(self):
        if self.viaf:
            return rdflib.URIRef(self.viaf)
        if self.dbpedia:
            return rdflib.URIRef(self.dbpedia)

    @property
    def rdfinfo(self):
        return RdfPerson(rdf_data(), self.uriref)




class Place(models.Model):
    name = models.CharField(max_length=255)
    # slug ?
    dbpedia = models.URLField(max_length=255, blank=True, null=True, unique=True)
    geonames = models.URLField(max_length=255, blank=True, null=True, unique=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __unicode__(self):
        return self.name



