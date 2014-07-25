.. _DEPLOYNOTES:

DEPLOYNOTES
===========

Initial setup
-------------

* Install python dependencies (virtualenv is recommended)::

  pip install -r pip-install-req.txt

.. Note::

   Setting up the virtualenv and installing dependencies is handled by
   the fabric deploy script when deploying to QA or production.

* Copy ``belfast/localsettings.py.dist`` to ``belfast/localsettings.py``
  and customize as needed.

* Initialize the database::

  python manage.py syncdb

* Load fixtures for initial required flat pages::

  python manage.py loaddata belfast/pages/fixtures/initial_flatpages.json

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

* Configure **RDF_DATABASE** and **GEXF_DATA** in ``localsettings.py``;
  run manage command to harvest and prepare the RDF data for the site::

  python manage.py prep_dataset



