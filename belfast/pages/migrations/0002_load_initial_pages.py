# -*- coding: utf-8 -*-
import os
import glob
import logging
from south.v2 import DataMigration
from django.conf import settings
from django.contrib.flatpages.models import FlatPage


logger = logging.getLogger(__name__)


class Migration(DataMigration):

    def forwards(self, orm):
        '''Load pre-defined flatpages content'''
        from django.core.management import call_command
        call_command("loaddata", "belfast/pages/fixtures/initial_flatpages.json")

        # now load html content from files for specific pages
        html_fixture_dir = os.path.join(settings.BASE_DIR, 'pages', 'fixtures',
            'page_content')

        # iterate over html files in fixture dir and set flatpage content, if possible
        for doc in glob.glob(os.path.join(html_fixture_dir, '*.html')):
            basename, ext = os.path.splitext(os.path.basename(doc))
            # if filname contains underscores, convert to / for nested URLs
            url = '/%s/' % basename.replace('_', '/')
            try:
                fp = FlatPage.objects.get(url=url)
            except FlatPage.DoesNotExist:
                # if somehow we have an html file that doesn't correspond
                # to an existing flatpage, warn and skip
                logger.warn('No flatpage found for "%s.html" (url)', basename)
                # fp = FlatPage(url=url)
                continue

            with open(doc) as html:
                fp.content = html.read()
                fp.save()

    def backwards(self, orm):
        # no undo for loading fixtures
        pass

    models = {

    }

    complete_apps = ['pages']
    symmetrical = True
