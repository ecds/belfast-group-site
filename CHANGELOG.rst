CHANGELOG
=========

1.0.2
-----

* bugfix: ignore whitespace differences when generating Group sheet
  table of contents

1.0.1
-----

* Last copy editing changes on site text content.
* bugfix: egograph node information view will now return 404 if
  requested without an id instead of causing a 500.


1.0 Initial Release
-------------------


RDF data harvesting and preparation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* A command-line user can run a script to harvest RDFa from a specified URL and save it as RDF XML, in order to keep a current copy of the data for aggregation and use in other context.
* When a command-line user runs the RDFa harvesting script, they can optionally harvest content from related URLs, so that they can gather data for multiple related pages at once.
* A command-line user can run a script to generate RDF for the Belfast Group sheets held by Queens University Belfast so that MARBL and Queens Group sheet information can be aggregated together.
* A command-line user can run a script to "smush" harvested RDf for Belfast Group sheets, so that different copies of the same sheet can be linked together and referenced without duplication.
* A command-line user can run a script to harvest RDF data from DBpedia, VIAF, and GeoNames for persons, places, and organizations referenced in the harvested RDF, so that additional data can be queried or referenced in the new Belfast Group website.
* A user will be able to harvest and prep RDF dataset with a single script so the process is reliable and repeatable.
* When a user runs the script to harvest and prep the Belfast Group RDF dataset,  manuscripts will be recognized and labeled as Belfast Group sheets so that all Belfast Group sheets can easily be identified for display and visualization on the site.
* Custom RDF ontology which includes a Belfast Group Sheet type


Basic Site Functionality
^^^^^^^^^^^^^^^^^^^^^^^^
* A user who comes to the site sees images and text that tells them something
  about the site so they can determine if they are interested.
* A user can navigate to different sections of the site so they can get to
  top-level sections of the site from anywhere in the site
* A user can read an overview essay about the Belfast Group (BG) so they can
  become oriented to the history and context
* A user can view text so they can learn more about the biography of
  selected authors and/or participants in the Belfast Group

Group sheets
^^^^^^^^^^^^

* A user can view a list of documents sorted by author so they can see
  an overview of the content included in the Belfast Group collections.
* A user can read the poems in a single group sheet so they can see the
  drafts of the poems from a single workshop session
* A user viewing a single groupsheet is presented with a brief table of
  contents, author's name, and approximate dates of the group sheet so
  they know more about this specific group sheet
* A user will be able to conduct a keyword search so they can find content
  related to their interest.
* A user can view and bookmark a permanent URL for a group sheet so they
  can return to the same page later.
* After running a search, a user receives a result list of workshop group
  sheets so they can read the material for which they searched.
* When a user accesses a poem via search results, the poem will be displayed
  within the context of the group sheet in which it appears so that the user
  experience remains consistent.
* An anonymous user will be able to search in a consistent manner from any
  page on the site so they can easily find what they are looking for.
* When a user browses the list of workshop group sheets, the titles on each
  sheet are displayed in order so that title sequence reflects the actual document.
* A user browsing the workshop list can access digital editions of
  workshop group sheets so they can read the content.
* A user can use standard wildcards in text searches so they can get
  better results.
* An anonymous user will be able to see the source of the materials (e.g.,
  Seamus Heaney papers) on each group sheet so they know where they might
  find original materials.
* A user will be able to access the TEI XML from the Belfast Group website so
  they can repurpose the data for another application.
* When a user is reading a group sheet, they can see a responsive table of
  contents so they can navigate the document easily and know which poem
  they are currently reading.
* A user can filter the workshop list to show only the workshops with digital
  editions so they can see only the content that can be accessed online.
* When viewing the group sheet list, users will be able to filter displayed
  group sheets using facets so they can narrow down the list to specific
  authors or items available online.
* When viewing an individual group sheet, a user will be able to see the
  source collection(s) where the original document(s) can be found so they can
  know where to find the original(s), should they want to examine it.
* As a user, I want to see dates list of Group sheets displayed as DD
  [Month name] YYYY so I'm not confused about whether it's a US or European
  formatted date.
* As a user, when  I see multiple authors listed for a Group sheet, I want
  to see the authors names listed alphabetically by last name so they are
  easier to find in the list.
* When viewing the list of Group sheets, a user will be able to see the genre
  of untitled works so they have more information about them.
* A user will be able to see anonymously authored group sheets in the list of
  group sheets so they have a better sense of the corpus.
* A user will be able to see Group sheets that are known to be in private
  hands listed on the Group sheet list so they can have as much information as
  is currently known.
* A user will be able to see all of the group sheets with untitled works by
  an author so they can have a sense of the collection as a whole.
* When viewing the Group sheets list a user will see the Group sheets ordered
  by author, then by title so the information is easier to scan through.
* As a user, when I browse the group sheets and filter by digital edition, I
  want to be able to remove that filter so I can try other filters.
* When filtering by author for the group sheets, the filter name should
  remain last-name first when applied.
* When reading a group sheet by multiple authors, all authors are clearly
  listed in the heading and title of the group sheet and the table of contents
  so the user knows clearly which poems are written by which authors.
* A user can view a list of documents grouped by time period so they can get
  a sense of the chronology of the Belfast Group’s work.
* When a user browses group sheets, they will be able to see all authors
  of each group sheet so they can see when a document includes work by multiple
  authors.
* When a user is using facets to browse the group sheets, a multi-authored
  group sheet will appear when any of the authors are selected for the facets
  so the user can find all the group sheets by a particular author.
* When a user browses group sheets on an individual author page, they will be
  able to see multiple authors listed for a group sheet, if they exist, so the
  user better understands the contents of the document.


Profile pages
^^^^^^^^^^^^^

* A user will be able to view a profile page for individuals in and related
  to the Belfast Group so they will be able to learn more about the people involved.
* When viewing a profile page, a user will be able to see a dynamically generated
  list of a poet's connections so they can learn about relationships between
  members of the group and/or other organizations.
* When viewing a profile page, a user will be able to see a dynamically
  generated visualization of a person's connections so they can see the people
  and organizations to which the person is connected.
* A user will be able to see a dynamically generated social network graph
  of the connections between individuals, locations, and organizations within
  our data so they can see how the group was connected.
* When viewing a profile page, a user will be able to see a dynamic list
  of the poet's group sheets so they can see the extent of the poet's
  contributions to the Belfast Group workshops.
* When viewing a profile page, a user will be able to link to individual group
  sheets to which a poet has contributed so they can quickly get additional information about/by the poet.
* When viewing a profile page, a user will be able to read an RDF-generated
  biography from the MARBL finding aids so they can have more specific information
  about the individual.
* When viewing a profile page and its RDF-generated biography from the DBpedia
  entry, a user will be able to link to the original Wikipedia entry so they
  can get more information about individual.
* When a user goes to a poet's profile, they can see an image of the poet so
  they know what the poet looks like.
* As a user, I want to see profiles for people who were involved in the group
  but might not have group sheets so I can get a sense of the whole of the group.
* When viewing the list of connections on an individual profile, a user will be
  able to click on a link to the various URIs (VIAF, geonames, DBpedia) so they
  can better understand the linked data that undergirds the project.
* When browsing the list of connections on an individual's profile, the user
  will see them organized by strength of connection to the person profiled so
  they will have an additional way to understand the connection.
* When browsing the list of connections on an individual profile, a user will
  be able to click on the name of individual who have profiles on the site to
  get to their profile so it is easier to navigate across the site.
* When browsing the list of connections or viewing the network graph on an
  author's profile, users will see people mentioned in the TEI group sheets
  listed, so that connections through an author's writing will be more visible.
* When reading a profile a user will not find extraneous information derived
  from our RDF data so they are not confused by the site's information and
  interactions.
* When browsing the list of profiles, a user will be able to see thumbnails of
  authors who have profile pictures so they have more visual information about them.
* When there is not a RDF-generated biography from MARBL finding aids available
  for a profile page a user will see biographical a user will see biographical
  data from DBpedia, so there is something to read on the site.
* When on the bio page, the user will only see profiles of individuals who have
  a finding aid or a DBpedia entry so they only get results that have content.
* When browsing the list of profiles on the bios page, a user will see names
  for people who did not author group sheets but owned them, where ownership
  can be inferred from the archival collections, so the user can see information
  about the wider network of the Belfast Group.
* When viewing a profile page and its RDF-generated biography from the MARBL
  finding aids, a user will be able to link to the original finding aid so
  they can get more information about the collection.
* When visiting a profile page a user will be able to see a picture of the
  poet so they will have a visual sense of the person.

Network Graphs
^^^^^^^^^^^^^^
* When a user is viewing a force-directed graph on the Belfast site, they see
  labels for each node so they can more easily see where entities fall in the network.
* When a user is looking at an ego graph, they can easily identify the node
  representing the profiled individual, so that they can see where the person
  fits in their own network.
* A user will be able to see an ego graph of the Belfast Group with one degree
  of further connection so they can understand the connectedness of individuals
  who are also connected to the BG.
* When viewing network visualizations, a user will be able to hover over a node
  to view the node's label so they know what the node represents.
* When viewing network visualizations, a user will be able to turn on labels for
  all nodes so they can see all of the labels at once.
* A user will be able to resize the nodes in network visualizations according
  to graph properties so they are better able to see relationships at a glance.
* When viewing a network visualization of the BG, a user will be able to turn
  off nodes that fall below a certain threshold so it is easier to view the
  interconnectedness of the nodes.
* As a user, when I'm viewing a network graph I want to be able to easily
  distinguish different types of nodes so that I can better understand the graph.
* When a user changes the centrality measures after the graph stabilizes,
  the nodes will resize appropriately so visualization reflects the settings
  appropriately.
* As a user, when I'm looking at a page with network graphs, I want to see
  context-dependent help text that indicates how the graphs work so I understand
  how to use them.
* As a user, I want to see an indication that a network graph is loading so
  that I know I need to wait and that I haven't hit a blank or broken page.
* As a user, I want to see a two-degree ego graph of the Belfast Group so I
  can see additional connections among individuals.
* When viewing a network visualization, a user will be able to move a node on
  the network to a location on the screen and then have it stay in place so
  they can more easily see the connections between the nodes.
* A user will be able to set the labels on the network visualization of the
  BG so they only appear on nodes of a certain size so it is easier to read the labels
* When a user is viewing a force-directed graph they can see more information
  about the nodes in a sidebar panel so they can further investigate the data
  represented by the graph.
* Users can view an alternate network graph of the Belfast Group, based on
  the connections that can be inferred from the group sheets, so they can
  get a sense of the group in its two periods.


Other visualizations
^^^^^^^^^^^^^^^^^^^^
* A user will be able to see a chord diagram of connections among the principal
  members of the Belfast group so they have multiple ways to visualize the dataset.
* A user will be able to view a dynamically generated map of locations
  mentioned in the poems and EAD so they can understand important locations
  to the Belfast Group.
* As a user, I want to be able to click on a name in the chord diagram and
  get more information about that individual and the Group sheets that s/he
  created so I can have more information about him / her.
* When a user looks at the map visualization they will see different icons
  for places based on whether it's referred to in poetry or biographical
  details so they can tell the difference at a glance.
* A user can tell which points on the map are related to particular poets
  so they can get more information when looking at the map.
* When a user clicks on a place in the map visualization they will be able
  to see how it is related to the data set so they can tell if the place is
  related to a poem or to a poet's biography.


Site Text Content
^^^^^^^^^^^^^^^^^
* As a user, I want to be able to read the overview on one page and navigate its
  parts with a table of contents so I can see the whole of the overview.
* As a user, I want to be able to click on footnotes and be taken to the
  reference (and vice versa) so I can navigate the site's information easily.
* When presented with a randomized assortment of photos from profile pages on
  the home page, a user will be able to click on an image in order to get to the
  individual's profile page so the site becomes faster to navigate.
* A user will be able to see introductory text content on the Group Sheets
  browse page so they can have the page's information put in context.
* As a user I see university branding on the site, so that I know that it
  is an Emory University resource.
* When viewing the site, a user will see the footer placed in a consistent
  matter so they have a consistent user interface.
* When a user views network graphs and chord diagram they should display as a
  percentage of the screen rather than a fixed height / width so they can see
  as much information on the screen as possible.

Mobile
^^^^^^

* When a user accesses the group sheets on a mobile device they will be able
  to read and access the table of contents navigation so they can make use of
  all the site's features.
* When a user resizes the networks & maps page, the images remain in their
  containers so the page looks correct.

Data, RDF, etc.
^^^^^^^^^^^^^^^
* A user will be able to harvest RDFa from the Belfast Group website so they
  can repurpose the data for another application.
* A user will be able to harvest RDF for Belfast group sheets from the belfast
  website in a format consistent with group sheet descriptions harvested from
  EAD so that data about group sheets from different sources can be combined.
* A search engine crawling the Belfast Group website will be able to use XML
  sitemaps to optimize which pages are crawled and indexed for its search results.
* A search engine crawling the Belfast Group website will be able to obtain
  basic semantic data about pages on the site and its contents so the search
  engine’s results can be improved.
* As a user, I want to be able to download GEXF files for the site's data so
  I can examine the data in a more configurable interface.
* As a user, I want to be able to find the RDF of the data somewhere so I can
  re-purpose it for other projects.

Admin
^^^^^
* An admin can use the django admin flat pages to edit the text content for
  the network intro page, belfast group network diagrams, and chord diagram
  pages so that the pages are easier to update and maintain.
* When an admin uploads images to the site, thumbnails are automatically
  created for the images so they can used for multiple purposes.
* When an admin uploads pictures for a profile page, the pictures will
  automatically be re-sized so they fit the site's template.
* A site admin can upload images and associate them with people on the site
  so the content will be more complete.

