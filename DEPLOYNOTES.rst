.. _DEPLOYNOTES:

DEPLOYNOTES
===========

Initial setup
-------------


* Install python dependencies (virtualenv is recommended)::

    pip install -r pip-install-req.txt

.. Note::

   Setting up the virtualenv and installing dependencies is handled
   automatically by the fabric deploy script when deploying to QA or production.
   This should be run as ``fab deploy -H hostname`` from a development
   instance of the project.

* Copy ``belfast/localsettings.py.dist`` to ``belfast/localsettings.py``
  and customize as needed.

* Initialize the database and load initial html site content::

    python manage.py syncdb
    python manage.py migrate

* Manually create an eXist collection and load the TEI Belfast Group Sheet
  content. Load the index configuration and index the content::

    python manage.py existdb load-index
    python manage.py existdb reindex

* Configure the site to run under Apache with mod WSGI (see ``apache/belfast.conf``
  for an apache site configuration starting point).

* Configure **MEDIA_ROOT** and **MEDIA_URL** in ``localsettings.py``;
  when running under apache, you must configure **STATIC** and **MEDIA**
  directories to be served out at the appropriate url.

* Log in to the Django admin site and configure the default **Site**
  to match the domain where the application is deployed.

* Configure your **rdf** database connection under **DATABASES** and set
  **GEXF_DATA** in ``localsettings.py``; run manage command to harvest
  and prepare the RDF data for the site::

    python manage.py prep_dataset


Developer Notes
^^^^^^^^^^^^^^^

* Install python development dependencies, required for running unit tests,
  generating documentation, etc.::

    pip install -r pip-dev-req.txt


* Installing bsddb3 requires the berkeley DB library, and on OSX the pip install
  may require explicitly specifying the local path to Berkeley DB::

    brew install berkeley-db
    BERKELEYDB_DIR=$(brew --cellar)/berkeley-db/5.3.28 pip install bsddb3

* Running the tests requires the **REUSE_DB** setting because of the RDF
  database:

     env REUSE_DB=1 ./manage.py test



1.1
---

* Run ``python manage.py migrate`` for up to date Django migrations.
* Update configurations for eXist 2.2 in ``localsettings.py``; if loading
  data to a brand new collection, you may need to load and reindex::

    python existdb load-index
    python existdb reindex