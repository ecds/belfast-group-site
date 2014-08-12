# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ProfilePicture'
        db.create_table(u'people_profilepicture', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('person_uri', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
            ('img', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('date', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('collection_uri', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('creator', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('publisher', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('publisher_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('permissions', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'people', ['ProfilePicture'])


    def backwards(self, orm):
        # Deleting model 'ProfilePicture'
        db.delete_table(u'people_profilepicture')


    models = {
        u'people.profilepicture': {
            'Meta': {'object_name': 'ProfilePicture'},
            'collection_uri': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'date': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'permissions': ('django.db.models.fields.TextField', [], {}),
            'person_uri': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'}),
            'publisher': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'publisher_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['people']