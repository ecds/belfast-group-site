from os import path
from eulxml import xmlmap
from eulxml.xmlmap import teimap
import unittest
from django.core.urlresolvers import reverse
from django.test import TestCase
from eulexistdb import testutil
from lxml import etree

from belfast.groupsheets.models import GroupSheet, Contents, \
    Poem
from belfast.groupsheets.templatetags.tei import format_tei

FIXTURE_DIR = path.join(path.dirname(path.abspath(__file__)), 'fixtures')

class GroupSheetTest(unittest.TestCase):
    # test xmlobject for TEI GroupSheet

    simmons_xml = path.join(FIXTURE_DIR, 'simmons1.xml')

    def setUp(self):
        # load the fixture file as a generic tei document
        self.tei = xmlmap.load_xmlobject_from_file(self.simmons_xml,
                                                   teimap.Tei)
        # find the first groupsheet via xpath and load
        groups = self.tei.node.xpath('//t:text/t:group/t:group',
            namespaces={'t': teimap.TEI_NAMESPACE})
        self.groupsheet = GroupSheet(groups[0])

    def test_fields(self):
        self.assertEqual('simmons1_1035', self.groupsheet.id)
        self.assertEqual('POEMS BY JAMES SIMMONS', self.groupsheet.title)
        self.assertEqual('James Simmons', self.groupsheet.author)
        self.assertEqual('1963-1966', self.groupsheet.date)

        # test contents sub xmlobject
        self.assert_(isinstance(self.groupsheet.toc, Contents))
        self.assertEqual('Workshop Poems', self.groupsheet.toc.title)
        self.assertEqual(6, len(self.groupsheet.toc.items))
        self.assertEqual('''Drinker's Blues''', self.groupsheet.toc.items[0])
        self.assertEqual('Fahan Strand', self.groupsheet.toc.items[1])
        self.assertEqual('The Ulster Soldier Boy', self.groupsheet.toc.items[-1])

        # test poem sub-xmlobject
        self.assert_(isinstance(self.groupsheet.poems[0], Poem))
        poem = self.groupsheet.poems[0]
        self.assertEqual('simmons1_109', poem.id)
        self.assertEqual('''DRINKER'S BLUES''', poem.title)
        self.assertEqual('James Simmons', poem.byline)


class GroupsheetViewsTest(testutil.TestCase):
    # for now, load all files in the fixture dir to eXist for testing
    exist_fixtures = {'directory': FIXTURE_DIR}

    def test_view_sheet(self):
        response = self.client.get(reverse('groupsheets:view',
                                           kwargs={'id': 'bogus-id'}))
        self.assertEqual(404, response.status_code,
            'view sheet should return 404 for non-existent document id')

        response = self.client.get(reverse('groupsheets:view',
                                           kwargs={'id': 'simmons1_1035'}))

        # basic investigation that view logic is functional
        # not testing template display here
        self.assertEqual(200, response.status_code,
            'view should should not 404 for id that is loaded in eXist')
        self.assert_('document' in response.context,
            'document should be included in template context')
        self.assert_(isinstance(response.context['document'], GroupSheet),
            'document in template context should be a group sheet')


class FormatTeiTestCase(unittest.TestCase):
    # test tei_format template tag explicitly
    LINEGROUP = '''<lg xmlns="%s" type="stanza">
          <l>I will arise and go now, and go to Innisfree</l></lg>''' \
          % teimap.TEI_NAMESPACE
    HEAD = '''<head xmlns="%s">Lake Isle of Innisfree</head>''' \
          % teimap.TEI_NAMESPACE
    EPIGRAPH = '''<epigraph xmlns="%s">
       <p>Man to the hills, woman to the shore. (Gaelic proverb)</p>
       </epigraph>''' % teimap.TEI_NAMESPACE
    QUOTE = '''<q xmlns="%s">(For Eavan)</q>''' % teimap.TEI_NAMESPACE
    INDENT = '<l xmlns="%s" rend="indent5">All harbors wrecked</l>' % \
       teimap.TEI_NAMESPACE

    # '{%s}q' % TEI_NAMESPACE: ('<blockquote>', '</blockquote>'),
    def setUp(self):
        # place-holder content node
        self.content = xmlmap.XmlObject(etree.fromstring(self.LINEGROUP))

    def test_linegroup(self):
        format = format_tei(self.content)
        self.assert_(format.startswith('<div class="linegroup">'))
        self.assert_(format.endswith('</div>'))

    def test_line(self):
        lnode = list(self.content.node.iterchildren())[0]
        self.content.node = lnode
        format = format_tei(self.content)
        self.assert_(format.startswith('<p>'))
        self.assert_(format.endswith('</p>'))

    def test_head(self):
        self.content.node = etree.fromstring(self.HEAD)
        format = format_tei(self.content)
        self.assertEqual('<strong>Lake Isle of Innisfree</strong>',
                         format)

    def test_epigraph(self):
        self.content.node = etree.fromstring(self.EPIGRAPH)
        format = format_tei(self.content)
        self.assert_(format.startswith('<div class="epigraph">'))
        self.assert_(format.endswith('</div>'))

    def test_quote(self):
        self.content.node = etree.fromstring(self.QUOTE)
        format = format_tei(self.content)
        self.assertEqual('<blockquote>(For Eavan)</blockquote>',
                         format)

    def test_indent(self):
        self.content.node = etree.fromstring(self.INDENT)
        format = format_tei(self.content)
        self.assert_(format.startswith('<span style="padding-left:2.5em">'))
        self.assert_(format.endswith('</span>'))

