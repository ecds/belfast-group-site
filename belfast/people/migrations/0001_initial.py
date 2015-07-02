# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_image_tools', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfilePicture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('person_uri', models.URLField(unique=True, verbose_name=b'Person')),
                ('date', models.CharField(help_text=b'Date of the photo, if known', max_length=255, blank=True)),
                ('collection_uri', models.URLField(help_text=b'MARBL Archival collection source for the original picture (for MARBL content)', null=True, verbose_name=b'Archival Collection', blank=True)),
                ('creator', models.CharField(help_text=b'Photographer or whoever else is responsible for creating the image, if known', max_length=255, blank=True)),
                ('creator_url', models.URLField(help_text=b'Photographer website URL, if available', verbose_name=b'Creator Website', blank=True)),
                ('publisher', models.CharField(help_text=b'Name of the publisher, if applicable', max_length=255, blank=True)),
                ('publisher_url', models.URLField(help_text=b'Publisher URL, if known;\n        used with publisher name to generate a link on profile page', verbose_name=b'Publisher Website', blank=True)),
                ('permissions', models.TextField(help_text=b'Statement of Permissions')),
                ('image', models.ForeignKey(related_name='profilepicture_set', to='django_image_tools.Image')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
