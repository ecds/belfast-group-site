import logging
from django.db import models

logger = logging.getLogger(__name__)


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    slug = models.SlugField()

    # dbpedia uri? # viaf uri? # same-as listfield?

    class Meta:
        verbose_name_plural = "people"

    def __unicode__(self):
        return '%s %s' % (self.first_name, self.last_name)

    # todo: generate slug when saving new and unset (i.e. not via admin)



