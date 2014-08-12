from django.db import models
import rdflib

from django_image_tools.models import Image

from belfast.util import rdf_data
from belfast.groupsheets.rdfmodels import RdfArchivalCollection
from belfast.people.rdfmodels import RdfPerson


class ProfilePicture(models.Model):
    # Fields: creator, title, date, publisher, publisher URL, collection, statement of permissions
    person_uri = models.URLField(verbose_name='Person', unique=True)
    image = models.ForeignKey(Image, related_name='profilepicture_set')
    date = models.CharField(max_length=255,
        help_text='Date of the photo, if known', blank=True)
    collection_uri = models.URLField(blank=True, null=True,
        help_text='MARBL Archival collection source for the original picture (for MARBL content)',
        verbose_name='Archival Collection')
    creator = models.CharField(max_length=255,
        help_text='Photographer or whoever else is responsible for creating the image, if known',
        blank=True)
    creator_url = models.URLField(blank=True,
        verbose_name='Creator Website', help_text='''Photographer website URL, if available''')
    publisher = models.CharField(max_length=255, blank=True,
        help_text='Name of the publisher, if applicable')
    publisher_url = models.URLField(blank=True,
        verbose_name='Publisher Website', help_text='''Publisher URL, if known;
        used with publisher name to generate a link on profile page''')
    permissions = models.TextField(help_text='Statement of Permissions')

    def __unicode__(self):
        return self.image.title

    @property
    def rdfperson(self):
        return RdfPerson(rdf_data(), rdflib.URIRef(self.person_uri))

    @property
    def person(self):
        return self.rdfperson.name

    @property
    def rdfcollection(self):
        if self.collection_uri is not None:
            return RdfArchivalCollection(rdf_data(), rdflib.URIRef(self.collection_uri))

    @property
    def collection(self):
        if self.rdfcollection is not None:
            return self.rdfcollection.name

    @property
    def title(self):
        if self.image:
            return self.image.title

    @property
    def thumbnail(self):
        'thumbnail of django-image-tools Image, for use in admin'
        if self.image:
            return self.image.thumbnail
