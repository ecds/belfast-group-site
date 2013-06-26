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

  * Run ``smush-rdf.py`` to de-dupe group sheets in the data::

      ./scripts/smush-rdf.py data/*.xml

  * Run ``harvest-related.py`` to download related RDF (VIAf, DBpedia, etc)::

      ./scripts/harvest-related.py data/*.xml -o data

  * Run ``rdf2gexf.py`` script on Belfast Group RDF data to
    generate and save a Network Graph fle, e.g.::

      ./scripts/rdf2gexf.py data/*.xml -o belfast-group-data.gexf

    Configure the resulting file in the ``localsettings.py``
    as **GEXF_DATA**.

* Ensure that a cache is configured in ``localsettings.py``


