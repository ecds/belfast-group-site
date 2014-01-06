CHANGELOG
=========


Initial Release
---------------

RDF data harvesting and preparation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* A command-line user can run a script to harvest RDFa from a specified URL and save it as RDF XML, in order to keep a current copy of the data for aggregation and use in other context.
* When a command-line user runs the RDFa harvesting script, they can optionally harvest content from related URLs, so that they can gather data for multiple related pages at once.
* A command-line user can run a script to generate RDF for the Belfast Group sheets held by Queens University Belfast so that MARBL and Queens Group sheet information can be aggregated together.
* A command-line user can run a script to "smush" harvested RDf for Belfast Group sheets, so that different copies of the same sheet can be linked together and referenced without duplication.
* A command-line user can run a script to harvest RDF data from DBpedia, VIAF, and GeoNames for persons, places, and organizations referenced in the harvested RDF, so that additional data can be queried or referenced in the new Belfast Group website.
* A user will be able to harvest and prep RDF dataset with a single script so the process is reliable and repeatable.
* When a user runs the script to harvest and prep the Belfast Group RDF dataset,  manuscripts will be recognized and labeled as Belfast Group sheets so that all Belfast Group sheets can easily be identified for display and visualization on the site.

.. Note: not a story but worth mentioning/describing somehow; data or site-specific?
* Custom RDF ontology which includes a Belfast Group Sheet type


Site Functionality (previous/existing?)
^^^^^^^^^^^^^^^^^^
* A user who comes to the site sees images and text that tells them something about the site so they can determine if they are interested.
* A user can navigate to different sections of the site so they can get to top-level sections of the site from anywhere in the site
* A user can read an overview essay about the Belfast Group (BG) so they can become oriented to the history and context
* A user can view text so they can learn more about the biography of selected authors and/or participants in the Belfast Group
* A user can view a list of documents sorted by author so they can see an overview of the content included in the Belfast Group collections.
* A user can read the poems in a single group sheet so they can see the drafts of the poems from a single workshop session
* A user viewing a single groupsheet is presented with a brief table of contents, author's name, and approximate dates of the group sheet so they know more about this specific group sheet
* A user will be able to conduct a keyword search so they can find content related to their interest.
* A user can view and bookmark a permanent URL for a group sheet so they can return to the same page later.
* After running a search, a user receives a result list of workshop group sheets so they can read the material for which they searched.
* When a user accesses a poem via search results, the poem will be displayed within the context of the group sheet in which it appears so that the user experience remains consistent.
* An anonymous user will be able to search in a consistent manner from any page on the site so they can easily find what they are looking for.
* When a user browses the list of workshop group sheets, the titles on each sheet are displayed in order so that title sequence reflects the actual document.
* A user will be able to view a profile page for individuals in and related to the Belfast Group so they will be able to learn more about the people involved.
* When viewing a profile page, a user will be able to see a dynamically generated list of a poet's connections so they can learn about relationships between members of the group and/or other organizations.
* When viewing a profile page, a user will be able to see a dynamically generated visualization of a person's connections so they can see the people and organizations to which the person is connected.
* A user will be able to see a dynamically generated social network graph of the connections between individuals, locations, and organizations within our data so they can see how the group was connected.
* A user browsing the workshop list can access digital editions of workshop group sheets so they can read the content.
* When a user is viewing a force-directed graph on the Belfast site, they see labels for each node so they can more easily see where entities fall in the network.
* When a user is looking at an ego graph, they can easily identify the node representing the profiled individual, so that they can see where the person fits in their own network.
* A user can use standard wildcards in text searches so they can get better results.
* An anonymous user will be able to see the source of the materials (e.g., Seamus Heaney papers) on each group sheet so they know where they might find original materials.
* When viewing a profile page, a user will be able to see a dynamic list of the poet's group sheets so they can see the extent of the poet's contributions to the Belfast Group workshops.
* When viewing a profile page, a user will be able to link to individual group sheets to which a poet has contributed so they can quickly get additional information about/by the poet.
* A user will be able to access the TEI XML from the Belfast Group website so they can repurpose the data for another application.
* A user will be able to harvest RDFa from the Belfast Group website so they can repurpose the data for another application.
* When a user is reading a group sheet, they can see a responsive table of contents so they can navigate the document easily and know which poem they are currently reading
* A user will be able to harvest RDF for Belfast group sheets from the belfast website in a format consistent with group sheet descriptions harvested from EAD so that data about group sheets from different sources can be combined.
* When viewing a profile page, a user will be able to read an RDF-generated biography from the MARBL finding aids so they can have more specific information about the individual.
* When viewing a profile page and its RDF-generated biography from the DBpedia entry, a user will be able to link to the original Wikipedia entry so they can get more information about individual.
* A user will be able to see an ego graph of the Belfast Group with one degree of further connection so they can understand the connectedness of individuals who are also connected to the BG.
* A user can filter the workshop list to show only the workshops with digital editions so they can see only the content that can be accessed online.
* When viewing the group sheet list, users will be able to filter displayed group sheets using facets so they can narrow down the list to specific authors or items available online.
* When a user goes to a poet's profile, they can see an image of the poet so they know what the poet looks like.
* A user will be able to see a chord diagram of connections among the principal members of the Belfast group so they have multiple ways to visualize the dataset.
* A user will be able to view a dynamically generated map of locations mentioned in the poems and EAD so they can understand important locations to the Belfast Group.
* When viewing an individual group sheet, a user will be able to see the source collection(s) where the original document(s) can be found so they can know where to find the original(s), should they want to examine it.
* When viewing network visualizations, a user will be able to hover over a node to view the node's label so they know what the node represents.
* When viewing network visualizations, a user will be able to turn on labels for all nodes so they can see all of the labels at once.
* A user will be able to resize the nodes in network visualizations according to graph properties so they are better able to see relationships at a glance.
* A search engine crawling the Belfast Group website will be able to use XML sitemaps to optimize which pages are crawled and indexed for its search results.
