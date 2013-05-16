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