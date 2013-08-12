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
from django.db.models import Q

from belfast import rdfns
from belfast.util import rdf_data, normalize_whitespace
from belfast.groupsheets.models import ArchivalCollection, GroupSheet
from belfast.groupsheets.rdfmodels import get_rdf_groupsheets
from belfast.people.models import Person, Place
from belfast.people.rdfmodels import BelfastGroup, find_places


class Command(BaseCommand):
    '''load rdf data and map it into the database as django models'''
    help = __doc__

    v_normal = 1

    def handle(self, *filenames, **options):
        self.verbosity = options['verbosity']

        # load rdf data
        self.graph = rdf_data()

        self.people()
        self.places()
        self.archival_collections()
        self.groupsheets()

    def people(self):
        if self.verbosity > self.v_normal:
            print '\nPeople connected to the Belfast Group'

        counts = {'add': 0, 'existing': 0, 'error': 0}

        for person in BelfastGroup().connected_people:
            # for now, don't bother updating if already in db
            if person.viaf_uri and Person.objects.filter(viaf=person.viaf_uri).count():
                counts['existing'] += 1
                continue

            if not (person.firstname or person.lastname):
                print 'error: no first/last name for %s - name = %s' % (person, person.name)
                counts['error'] += 1
                continue

            p = Person(first_name=person.firstname, last_name=person.lastname,
                       dbpedia=person.dbpedia_uri, viaf=person.viaf_uri)
            if 'viaf.org' in person.identifier:
                p.viaf = unicode(person.identifier)
            p.save()
            counts['add'] += 1

            if self.verbosity > self.v_normal:
                print '  %s' % p.name

        if self.verbosity >= self.v_normal:
            print '%(add)d people added, %(existing)d already in the database, %(error)d errors' % \
                counts


    def places(self):
        if self.verbosity > self.v_normal:
            print '\nPlaces anywhere in the dataset'

        counts = {'add': 0, 'existing': 0, 'error': 0}

        for place in find_places():
            # for now, don't bother updating if already in db
            # uri should either by geonames or dbpedia uri
            if Place.objects.filter(
                                    Q(geonames=place.identifier) |
                                    Q(dbpedia=place.identifier)
                                    ).count():
                counts['existing'] += 1
                continue

            if not (place.latitude or place.longitude):
                print 'Error no lat/long for %s - %s' % (place, place.identifier)
                counts['error'] += 1
                continue

            p = Place(name=normalize_whitespace(unicode(place)),
                      latitude=place.latitude,
                      longitude=place.longitude)

            if 'geonames.org' in place.identifier:
                p.geonames = unicode(place.identifier)
            if 'dbpedia.org' in place.identifier:
                p.dbpedia = unicode(place.identifier)
            p.save()
            counts['add'] += 1

            if self.verbosity > self.v_normal:
                print '  %s' % p.name

        if self.verbosity >= self.v_normal:
            print '%(add)d places added, %(existing)d already in the database, %(error)d errors' % \
                counts

    def archival_collections(self):
        if self.verbosity > self.v_normal:
            print '\nArchival collections'

        counts = {'add': 0, 'existing': 0, 'error': 1}

        # find a list of unique archival collections
        for coll in self.graph.subjects(predicate=rdflib.RDF.type,
                                        object=rdfns.ARCH.Collection):

            name = normalize_whitespace(self.graph.value(coll, rdfns.SCHEMA_ORG.name))
            if isinstance(coll, rdflib.BNode):
                # get parent webpage with url
                for webpage in self.graph.subjects(rdfns.SCHEMA_ORG.about, coll):
                    if (webpage, rdflib.RDF.type, rdfns.SCHEMA_ORG.WebPage) in self.graph:
                        # NOTE: schema.org/url no longer in findingaids records?
                        # should be set for consistency, but use pid identifier instead
                        url = self.graph.value(webpage, rdfns.SCHEMA_ORG.URL)
                        if url is None and unicode(webpage).startswith('http://'):
                            url = unicode(webpage)
                        break
            else:
                url = unicode(coll)

            if not url:
                print 'Error: no url for %s' % name
                counts['error'] += 1
                continue

            # if it already exists in db, do nothing
            if ArchivalCollection.objects.filter(url=url).count():
                counts['existing'] += 1
                continue

            ArchivalCollection(url=url, name=name).save()
            # TODO: short name
            counts['add'] += 1

            if self.verbosity > self.v_normal:
                print '  %s - %s' % (name, url)

        if self.verbosity >= self.v_normal:
            print '%(add)d archival collections added, %(existing)d already in the database, %(error)d errors' % \
                counts


    def groupsheets(self):
        if self.verbosity > self.v_normal:
            print '\nBelfast Group Sheets'

        counts = {'add': 0, 'existing': 0, 'error': 0}
        rdf_groupsheets = get_rdf_groupsheets()
        print '%d group sheets found in RDF data' % len(rdf_groupsheets)
        for gs in rdf_groupsheets:

            # if already in db, do nothing
            if GroupSheet.objects.filter(alt_uri=unicode(gs.identifier)).count():
                counts['existing'] += 1
                continue

            if gs.url is not None and GroupSheet.objects.filter(url=gs.url).count():
                print 'Error: url %s is in the db but alt-id %s is not (indicates possible de-dupe error)' % \
                    (gs.url, gs.identifier)
                if self.verbosity > self.v_normal:
                    dbgs = GroupSheet.objects.get(url=gs.url)
                    print 'Author & titles for %s (alt uri %s): ' % (dbgs.url, dbgs.alt_uri)
                    print '  %s - %s' % (dbgs.author.name, dbgs.author.viaf)
                    print '  %s' % dbgs.titles
                    print 'Author & titles for %s' % unicode(gs.identifier)
                    print '  %s - %s' % (gs.author.name, gs.author.identifier)
                    print '  ' + ', '.join(gs.titles)


                counts['error'] += 1
                continue

            # - first find author relation
            author = None
            if gs.author.viaf_uri is not None:
                try:
                    author = Person.objects.get(viaf=gs.author.viaf_uri)
                except ObjectDoesNotExist:
                    print 'error: could not find author %s (%s %s)' % \
                        (gs.author, gs.author.firstname, gs.author.lastname)

            # TODO: add non-viaf authors ?
            # also possible to have anonymous (one case?)
            if author is None:
                counts['error'] += 1
                continue

            sheet = GroupSheet(title_list=gs.titles, date=gs.date,
                               author=author, url=gs.url,
                               tei_id=gs.groupsheet_id,
                               alt_uri=gs.identifier)

            # TODO: num pages, genre?
            sheet.save()
            counts['add'] += 1

            # link to archival collections
            # (has to be saved & have db id before adding many-to-many rel)
            for url in gs.sources.keys():
                print 'source url = ', url
                try:
                    arch = ArchivalCollection.objects.get(url=url)
                    sheet.sources.add(arch)
                except ObjectDoesNotExist:
                    print 'Could not find ArchivalCollection for %s' % url

            if sheet.sources.count() == 0:
                print 'Error: no sources found for groupsheet %s - %s' % \
                       (sheet.author.name, sheet.title_list)

            sheet.save()

        if self.verbosity >= self.v_normal:
            print '%(add)d group sheets added, %(existing)d already in the database, %(error)d errors' % \
                counts


    # TODO (maybe) - connections

        # connections between people, places etc
        # people -> people
        # people -> organizations
        # people -> places
        # places -> organizations

        # places -> text/poetry/groupsheet
        # people -> text/poetry/groupsheet


