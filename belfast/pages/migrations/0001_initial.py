# -*- coding: utf-8 -*-
import os
from south.utils import datetime_utils as datetime
from south.v2 import DataMigration
from django.conf import settings
from django.contrib.flatpages.models import FlatPage

class Migration(DataMigration):

    def forwards(self, orm):
        # place-holder migration, since there are no local models defined
        # in belfast.pages
        # (defined to allow undo/redo of initial page data migration)
        pass

    def backwards(self, orm):
        pass

    models = {

    }

    complete_apps = ['pages']
    symmetrical = True
