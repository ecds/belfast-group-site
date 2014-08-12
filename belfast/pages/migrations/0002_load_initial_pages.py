# -*- coding: utf-8 -*-
import os
from south.utils import datetime_utils as datetime
from south.v2 import DataMigration
from django.conf import settings
from django.contrib.flatpages.models import FlatPage

class Migration(DataMigration):

    def forwards(self, orm):
        '''Load pre-defined flatpages content'''
        from django.core.management import call_command
        call_command("loaddata", "belfast/pages/fixtures/initial_flatpages.json")

        # now load html content for specific pages
        html_fixture_dir = os.path.join(settings.BASE_DIR, 'pages', 'fixtures',
            'page_content')

        for doc in ['overview']:
            fp = FlatPage.objects.get(url='/%s/' % doc)
            with open(os.path.join(html_fixture_dir, '%s.html' % doc)) as html:
                fp.content = html.read()
                fp.save()

    def backwards(self, orm):
        # no undo for loading fixtures
        pass

    models = {

    }

    complete_apps = ['pages']
    symmetrical = True
