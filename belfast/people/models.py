from django.db import models
from django.core.files import File
from PIL import Image
import rdflib
import tempfile

from belfast.util import rdf_data
from belfast.groupsheets.rdfmodels import RdfArchivalCollection
from belfast.people.rdfmodels import RdfPerson


class ProfilePicture(models.Model):
    # Fields: creator, title, date, publisher, publisher URL, collection, statement of permissions
    person_uri = models.URLField(verbose_name='Person', unique=True)
    # TODO: require unique for now so we don't get more than one pic per person?
    img = models.ImageField(upload_to='profile/', verbose_name='Image')
    thumbnail = models.ImageField(upload_to='profile/thumb/', blank=True,
        null=True, editable=False)
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

    image_size = (350, 350)
    thumbnail_size = (128, 128)

    def save(self, *args, **kwargs):
        # override save method to resize image and generate thumbnail

        image_update = False
        # if pk is set, this is an update to an existing model;
        # check if the image is being changed
        if self.pk:
            orig = ProfilePicture.objects.get(pk=self.pk)
            if self.img != orig.img:
                image_update = True

        if not self.pk or image_update:
            self.resize_image()

        if self.img and not self.thumbnail or image_update:
            self.generate_thumbnail()

        super(ProfilePicture, self).save(*args, **kwargs)


    def resize_image(self):
        return self._resize_imagefield(self.image_size, self.img)

    def generate_thumbnail(self):
        return self._resize_imagefield(self.thumbnail_size, self.thumbnail)

    def _resize_imagefield(self, size, field):
        image = Image.open(self.img)
        # NOTE: using thumbnail for both resize/thumb
        # because it resizes the current image rather than resize,
        # which returns a new Image object
        image.thumbnail(size, Image.ANTIALIAS)
        tmp = tempfile.NamedTemporaryFile(suffix='.png')
        image.save(tmp.name, 'png')
        content = File(tmp)
        field.save('%s.png' % self.rdfperson.slug, content, save=False)




