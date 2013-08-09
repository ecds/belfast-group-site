import glob
import rdflib
import os
import re
import sys
import time

# from progressbar import ProgressBar, Bar, Percentage, ETA, SimpleProgress

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand

from belfast import rdfns
from belfast.util import rdf_data, normalize_whitespace
from belfast.groupsheets.models import ArchivalCollection, GroupSheet
from belfast.groupsheets.rdfmodels import get_rdf_groupsheets
from belfast.people.models import Person
from belfast.people.rdfmodels import BelfastGroup




class Command(BaseCommand):
    '''load rdf data and map it into the database as django models'''
    help = __doc__

    v_normal = 1

    def handle(self, *filenames, **options):
        self.verbosity = options['verbosity']

        # load rdf data
        self.graph = rdf_data()

        self.people()
        self.archival_collections()
        # TODO: needs author rel
        self.groupsheets()

    def people(self):
        if self.verbosity >= self.v_normal:
            print '\nPeople connected to the Belfast Group'

        for person in BelfastGroup().connected_people:
            # for now, don't bother updating if already in db
            if person.viaf_uri and Person.objects.filter(viaf=person.viaf_uri).count():
                continue

            if not (person.firstname or person.lastname):
                print 'error: no first/last name for %s - name = %s' % (person, person.name)
                continue
            p = Person(first_name=person.firstname, last_name=person.lastname,
                       dbpedia=person.dbpedia_uri, viaf=person.viaf_uri)
            if 'viaf.org' in person.identifier:
                p.viaf = unicode(person.identifier)
            p.save()

            if self.verbosity >= self.v_normal:
                print '  %s' % p.name

        # print summary/total ?

    def archival_collections(self):
        if self.verbosity >= self.v_normal:
            print '\nArchival collections'

        # find a list of unique archival collections
        for coll in self.graph.subjects(predicate=rdflib.RDF.type,
                                        object=rdfns.ARCH.Collection):

            name = normalize_whitespace(self.graph.value(coll, rdfns.SCHEMA_ORG.name))
            if isinstance(coll, rdflib.BNode):
                # get parent webpage with url
                for webpage in self.graph.subjects(rdfns.SCHEMA_ORG.about, coll):
                    if (webpage, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                        url = self.graph.value(webpage, rdfns.SCHEMA_ORG.URL)
                        break
                    print webpage, url

            else:
                url = unicode(coll)

            # if it already exists in db, do nothing
            if ArchivalCollection.objects.filter(url=url).count():
                continue

            ArchivalCollection(url=url, name=name).save()
            # TODO: short name

            if self.verbosity >= self.v_normal:
                print '  %s - %s' % (name, url)


    def groupsheets(self):
        for gs in get_rdf_groupsheets():

            # if already in db, do nothing
            # FIXME: only digitized groupsheets have a url!
            # -- how to differentiate/uniquify non-digitized?
            if GroupSheet.objects.filter(url=gs.url).count():
                continue


            # - first find author relation
            try:
                print 'looking for person by viaf = ', gs.author.viaf_uri
                author = Person.objects.get(viaf=gs.author.viaf_uri)
            except ObjectDoesNotExist:
                print 'error: could not find author', gs.author
                print '%s %s' % (gs.author.firstname, gs.author.lastname)
                continue

            sheet = GroupSheet(title_list=gs.titles, date=gs.date,
                               author=author, url=gs.url,
                               tei_id=gs.groupsheet_id)


            # TODO: num pages, genre?
            sheet.save()

            # link to archival collections
            # (has to be saved & have db id before adding many-to-many rel)
            for url in gs.sources.keys():
                try:
                    arch = ArchivalCollection.objects.get(url=url)
                    sheet.sources.add(arch)
                except ObjectDoesNotExist:
                    print 'Could not find ArchivalCollection for %s' % url

            if sheet.sources.count() == 0:
                print 'Error: no sources found for groupsheet %s - %s' % \
                       (sheet.author.name, sheet.title_list)

            sheet.save()





