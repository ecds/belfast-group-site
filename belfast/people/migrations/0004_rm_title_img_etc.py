# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'ProfilePicture.img'
        db.delete_column(u'people_profilepicture', 'img')

        # Deleting field 'ProfilePicture.title'
        db.delete_column(u'people_profilepicture', 'title')

        # Deleting field 'ProfilePicture.thumbnail'
        db.delete_column(u'people_profilepicture', 'thumbnail')


    def backwards(self, orm):
        # Adding field 'ProfilePicture.img'
        db.add_column(u'people_profilepicture', 'img',
                      self.gf('django.db.models.fields.files.ImageField')(default='temp img', max_length=100),
                      keep_default=False)

        # Adding field 'ProfilePicture.title'
        db.add_column(u'people_profilepicture', 'title',
                      self.gf('django.db.models.fields.CharField')(default='temp title', max_length=255),
                      keep_default=False)

        # Adding field 'ProfilePicture.thumbnail'
        db.add_column(u'people_profilepicture', 'thumbnail',
                      self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True),
                      keep_default=False)


    models = {
        u'django_image_tools.image': {
            'Meta': {'object_name': 'Image'},
            'alt_text': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'caption': ('django.db.models.fields.TextField', [], {}),
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'credit': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'filename': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'subject_position_horizontal': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'subject_position_vertical': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '120'}),
            'was_upscaled': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'people.profilepicture': {
            'Meta': {'object_name': 'ProfilePicture'},
            'collection_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'profilepicture_set'", 'to': u"orm['django_image_tools.Image']"}),
            'permissions': ('django.db.models.fields.TextField', [], {}),
            'person_uri': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'publisher_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'})
        }
    }

    complete_apps = ['people']
