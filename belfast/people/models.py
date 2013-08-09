import logging

from django.db import models
from django.utils.text import slugify

logger = logging.getLogger(__name__)


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField()
    # links to other records
    dbpedia = models.CharField(max_length=255, blank=True, null=True, unique=True)
    viaf = models.CharField(max_length=255, blank=True, null=True, unique=True)

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



    # todo: generate slug when saving new and unset (i.e. not via admin)



