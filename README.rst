README
======

    .. image:: https://requires.io/github/emory-libraries-ecds/belfast/requirements.svg?branch=develop
         :target: https://requires.io/github/emory-libraries-ecds/belfast/requirements/?branch=develop
         :alt: Requirements Status

    .. image:: https://landscape.io/github/emory-libraries-ecds/belfast-group-site/master/landscape.svg?style=flat
       :target: https://landscape.io/github/emory-libraries-ecds/belfast-group-site/master
       :alt: Code Health

    .. image:: https://codeclimate.com/github/emory-libraries-ecds/belfast-group-site/badges/gpa.svg
       :target: https://codeclimate.com/github/emory-libraries-ecds/belfast-group-site
       :alt: Code Climate


Overview
--------

**belfast** is a Django web application created to display poetry drafts and network
graphs related to the Belfast Group, a group of poets and writers who met
to discuss their work in the 1960s and '70s in Northern Ireland.

Features are listed in **CHANGELOG**; installation instructions are in
**DEPLOYNOTES**.

Major dependencies include Django_, rdflib_, and networkx_.

.. _Django: https://www.djangoproject.com/
.. _rdflib: https://github.com/RDFLib/rdflib
.. _networkx: http://networkx.github.io/


License
-------
The code for the
`Belfast Group Poetry|Networks`_
site is distributed under the
`Apache 2.0 License`_.

.. _Belfast Group Poetry|Networks: http://belfastgroup.digitalscholarship.emory.edu
.. _Apache 2.0 License: http://www.apache.org/licenses/LICENSE-2.0

Components
----------

RDF
~~~

:mod:`belfast.rdf` consists of scripts and code for harvesting and preparing
the RDF and network data that is used on the site for generating the network
graphs, list of Group sheets, and profile pages.

Groupsheets
~~~~~~~~~~~

:mod:`belfast.groupsheets` provides display and search access to TEI-encoded
Group sheets in an eXist XML database, along with a browse list of all known
Group sheets, based on the RDF data.

People
~~~~~~

:mod:`belfast.people` provides profile pages for people associated with the
Belfast Group, based on the RDF data.

Network
~~~~~~~

:mod:`belfast.network` has views for presenting network graphs, a map,
and a chord diagram based on the RDF and network data.

Pages
~~~~~

:mod:`belfast.pages` is for html site content pages, which are generally managed
with :mod:`django.contrib.flatpages`, but includes a number of document fixtures
for loading the initial page content and creating named content page URLs
that are used in the site navigation.

