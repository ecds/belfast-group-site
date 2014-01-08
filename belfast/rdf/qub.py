from collections import defaultdict
import re
import rdflib
from rdflib.collection import Collection as RdfCollection
from bs4 import BeautifulSoup

from belfast import rdfns


class QUB(object):

    # regex to grab names from description
    NAME_REGEX = re.compile('(?P<last>[A-Z][a-zA-Z]+), (?P<first>[A-Za-z. ]+)')  # include . for initials
    DATE_REGEX = re.compile('Dated (?P<day>\d{2})/(?P<month>\d{2})/(?P<year>\d{4})')
    YEAR_REGEX = re.compile('Dates [^\d]*(?P<year>\d{4})')
    PAGES_REGEX = re.compile('Typescripts?,? (?P<num>\d)(p|pp.)')
    PAREN_REGEX = re.compile(' ?\([^())]+\)')

    NAME_URIS = {
        'Terry, Arthur': 'http://viaf.org/viaf/2490119',
        'Hobsbaum, Philip': 'http://viaf.org/viaf/91907300',
        'Heaney, Seamus': 'http://viaf.org/viaf/109557338',
        'Pakenham, John': 'http://viaf.org/viaf/40930958',
        'Bredin, Hugh T.': 'http://viaf.org/viaf/94376522',   # seems likely (lecturer at Queen's Univ. Belfast)
        'Buller, Norman': 'http://viaf.org/viaf/29058137',
        'McEldowney, Eugene': 'http://viaf.org/viaf/18143404',
        'Longley, Michael': 'http://viaf.org/viaf/39398205',
        'Dugdale, Norman': 'http://viaf.org/viaf/50609413',
        'Simmons, James': 'http://viaf.org/viaf/92591927',
        'Parker, Stewart': 'http://viaf.org/viaf/7497547',
        'MacLaverty, Bernard': 'http://viaf.org/viaf/95151565',
        'Belfast Group': rdfns.BELFAST_GROUP_URI,
    }

    # URI to PDF for Queen's description of their Belfast Group collection
    # FIXME: doesn't seem like the most stable of URIs...
    QUB_BELFAST_COLLECTION = 'http://www.qub.ac.uk/directorates/InformationServices/TheLibrary/FileStore/Filetoupload,312673,en.pdf'

    # URIs not found for:
    #   Croskery, Lynette M.
    #   Stronge, Marilyn
    #   Foster, Rodney  (possibly the Jazz musician born 1939 N. Ireland [still no uri])
    #   Ashton, Victor
    #   Smyth, Paul
    #   Robson, Bryan
    #   Scott, Brian
    #   Bull, Iris  (only one VIAF entry, doesn't seem like the right person)
    #   Sullivan, Ronald
    #   Brophy, Michael (possibly the one born in 1945, http://viaf.org/viaf/70921974 - http://trove.nla.gov.au/work/33952887?versionId=41792823)
    #   Mitchell, Michael
    #   Watton, Joan
    #   Bond, John
    #   Gallagher, Maurice
    #   Harvey, W.J.
    #   Johnston, J. K.

    def __init__(self, file, output_dir=None, verbosity=1, output_format='xml',
                 graph=None, url=None):
        if graph is None:
            graph = rdflib.ConjunctiveGraph()
        self.graph = graph

        # keep track of total number of manuscripts and unique authors,
        # for reporting on what was done
        ms_total = 0
        authors = defaultdict(int)

        # make sure verbosity is an int rather than a string for comparisons
        verbosity = int(verbosity)

        # if this context already exists in the conjunctive graph,
        # remove it to avoid duplicating data
        g = self.graph.get_context(url)
        if g and len(g):
            self.graph.remove_context(g)

        htmlfile = open(file)
        doc = BeautifulSoup(htmlfile)
        # g = rdflib.Graph()
        # create a subgraph context with a shared persistence layer and
        # the specified url as the graph identifier
        # g = rdflib.Graph(graph.store, url)
        # bind namespace prefixes for output
        g.bind('schema', rdfns.SCHEMA_ORG)
        g.bind('bibo', rdfns.BIBO)
        g.bind('dc', rdfns.DC)

        # create a node for the archival collection at Queen's Belfast (no URI)
        coll = rdflib.URIRef(self.QUB_BELFAST_COLLECTION)
        for t in [rdfns.ARCH.Collection, rdfns.SCHEMA_ORG.CreativeWork,
                  rdfns.DCMITYPE.Collection]:
            g.add((coll, rdflib.RDF.type, t))
        g.add((coll, rdfns.SCHEMA_ORG.name, rdflib.Literal(doc.body.h1.text)))
        g.add((coll, rdfns.SCHEMA_ORG.description, rdflib.Literal(doc.body.find(id='about').text)))
        g.add((coll, rdfns.SCHEMA_ORG.about, rdflib.URIRef(self.NAME_URIS['Belfast Group'])))
        # set Hobsbaum as collection creator since these were his materials
        g.add((coll, rdfns.SCHEMA_ORG.creator, rdflib.URIRef(self.NAME_URIS['Hobsbaum, Philip'])))

        # TODO: add information about owning archive ?
        # queen's u belfast mentions some collections are in archives hub... doesn't seem to include this one
        # possibly relevant? http://archiveshub.ac.uk/data/gb247-msgen874-875  (hobsbaum at glasgow)

        for div in doc.find_all('div'):
            # only include typescript content (should be all but one)
            # if 'Typescript' not in div.text:
            #     continue

            # create a blank node for the manuscript object
            msnode = rdflib.BNode()
            g.add((coll, rdfns.SCHEMA_ORG.mentions, msnode))
            g.add((msnode, rdflib.RDF.type, rdfns.BIBO.Manuscript))
            g.add((msnode, rdflib.RDF.type, rdfns.BG.GroupSheet))
            ms_total += 1

            content = list(div.stripped_strings)
            first_line = content[0]
            # first line should start with the author's name (if known)
            # second line *may* include a secondary author, but
            # because we don't know exactly where the second line starts, check all content
            for line in content:
                name_match = self.NAME_REGEX.match(line)
                if name_match:
                    last_name = name_match.group('last').strip()
                    # in some cases the 'Typescript, #pp' looks like a name; exclude
                    if last_name.lower() == 'typescript':
                        continue

                    first_name = name_match.group('first').strip()
                    name_key = '%s, %s' % (last_name, first_name)
                    full_name = '%s %s' % (first_name, last_name)
                    # use known URI if possible
                    if name_key in self.NAME_URIS:
                        author = rdflib.URIRef(self.NAME_URIS[name_key])
                    else:
                        author = rdflib.BNode()

                    # relate person to manuscript as author, include name information
                    g.add((msnode, rdfns.DC.creator, author))
                    g.add((author, rdfns.rdflib.RDF.type, rdfns.SCHEMA_ORG.Person))
                    g.add((author, rdfns.SCHEMA_ORG.name, rdflib.Literal(full_name)))
                    g.add((author, rdfns.SCHEMA_ORG.familyName, rdflib.Literal(last_name)))
                    g.add((author, rdfns.SCHEMA_ORG.givenName, rdflib.Literal(first_name)))

                    if verbosity > 1:
                        print 'Author: %s' % full_name

                    authors[full_name] += 1


            # A *few* items include a date; add it to the RDF when present
            last_line = content[-1]
            if 'Undated' not in last_line:
                date_match = self.DATE_REGEX.match(last_line)
                date = None
                if date_match:
                    date = '%s-%s-%s' % (date_match.group('year'),
                                         date_match.group('month'),
                                         date_match.group('day'))
                else:
                    year_match = self.YEAR_REGEX.match(last_line)
                    if year_match:
                        date = year_match.group('year')

                if date is not None:
                    # NOTE: using dc:date since it's not clear what date this would be
                    # (not necessarily a publication/creation date, e.g. one of the more specific schema.org)
                    g.add((msnode, rdfns.DC.date, rdflib.Literal(date)))

            # collection desription includes notes about poetry, short story, etc.
            # including as genre to avoid losing information
            if 'poem' in first_line.lower():
                g.add((msnode, rdfns.SCHEMA_ORG.genre, rdflib.Literal('poetry')))
            elif 'short story' in div.text.lower() or 'short stories' in div.text.lower():
                g.add((msnode, rdfns.SCHEMA_ORG.genre, rdflib.Literal('short story')))
            # one case is a book chapter...
            # some marked as possible translations?

            # collection description includes number of pages for each; go ahead and include
            pages = self.PAGES_REGEX.search(div.text)
            if pages:
                g.add((msnode, rdfns.BIBO.numPages, rdflib.Literal(pages.group('num'))))

            titles = []
            for italic_text in div.find_all('i'):
                for title in italic_text.stripped_strings:
                    # qub titles include subtitles/dedications in parenthesis,
                    # and "(sic)" in a few places,
                    # which makes de-duping difficult because titles look different.
                    # remove anything in parenthesis, including nested parens
                    while '(' in title:
                        title = self.PAREN_REGEX.sub('', title)

                    titles.append(title)

            if titles and verbosity > 1:
                print 'Titles: %s' % ', '.join(titles)

            # if only one title, no parts
            if len(titles) == 1:
                title = rdflib.Literal(titles[0])
                g.add((msnode, rdfns.DC.title, title))
            # if multiple titles; use rdf sequence to preserve order
            elif titles:
                title_node = rdflib.BNode()
                title_coll = RdfCollection(g, title_node,
                                           [rdflib.Literal(t) for t in titles])
                g.add((msnode, rdfns.DC.title, title_node))
            # if untitled, no dc:title should be added

        # report on what was done
        if verbosity >= 1:
            print 'Identified %d manuscripts by %d authors' % (ms_total,
                len(authors.keys()))


