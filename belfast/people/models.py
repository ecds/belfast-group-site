from django.db import models
import rdflib

from belfast.util import rdf_data
from belfast.groupsheets.rdfmodels import RdfArchivalCollection
from belfast.people.rdfmodels import RdfPerson


class ProfilePicture(models.Model):
    # Fields: creator, title, date, publisher, publisher URL, collection, statement of permissions
    person_uri = models.URLField(verbose_name='Person', unique=True)
    # TODO: require unique for now so we don't get more than one pic per person?
    img = models.ImageField(upload_to='profile/', verbose_name='Image')
    title = models.CharField(max_length=255,
        help_text='Title or caption to be shown with the image')
    date = models.CharField(max_length=255,
        help_text='Date of the photo, if known', blank=True)
    collection_uri = models.URLField(blank=True, null=True,
        help_text='Archival collection where the original picture was found',
        verbose_name='Archival Collection')
    creator = models.CharField(max_length=255,
        help_text='Photographer or whoever else is responsible for creating the image, if known',
        blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    publisher_url = models.URLField(blank=True,
        verbose_name='Publisher Website', help_text='Provide publisher URL, if known')
    permissions = models.TextField(help_text='Statement of Permissions')


    def __unicode__(self):
        return self.title

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




