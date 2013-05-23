.. _DEPLOYNOTES:

DEPLOYNOTES
===========

Initial setup
-------------

* Install python dependencies (virtualenv is recommended)::

  pip install -r pip-install-req.txt

* Copy ``belfast/localsettings.py.dist`` to ``belfast/localsettings.py``
  and customize as needed.

* Initialize the database::

  python manage.py syncdb

* Load fixtures for initial required flat pages::

  python manage.py loaddata belfast/pages/fixtures/initial_flatpages.json

* Check out a copy of the Belfast Group RDF data from
  https://github.com/emory-libraries-disc/belfast-group-data
  and configure the location of the ``data`` directory
  in ``localsettings.py`` as **RDF_DATA_DIR**.
