crane
=====

.. image:: https://travis-ci.org/pulp/crane.svg?branch=master
   :target: https://travis-ci.org/pulp/crane

.. image:: https://coveralls.io/repos/pulp/crane/badge.png?branch=master
   :target: https://coveralls.io/r/pulp/crane?branch=master

What is Crane?
--------------

Crane is a small read-only web application that provides enough of the docker
registry API to support "docker pull". Crane does not serve the actual image
files, but instead serves 302 redirects to some other location where files are
being served. A base file location URL can be specified per-repository.

Crane loads its data from json files stored on disk. It does not have a
database or use any other services. The json files can be generated with pulp
by publishing a docker repository.

Crane is a flask app written in Python. It is very easy to deploy and has a
small footprint, so it is a great way to provide a read-only "docker pull" API
that redirects to a static file service.

Advanced users can configure a search appliance to support "docker search" and
can setup repository protection using SSL certificates.

Configuration
-------------

A config file will be loaded from the path found in environment variable
``CRANE_CONFIG_PATH``. If not specified, the default location of
``/etc/crane.conf`` will be used.

The following options should go under a section named ``[general]``

debug
  ``true`` or ``false``, which sets Flask's ``DEBUG`` config option. Defaults to
  ``false``. If the environment variable ``CRANE_DEBUG`` has the value ``true``,
  that will also put crane in debug mode regardless of the setting in the config
  file.

data_dir
  full path to the directory from which metadata files should be loaded. defaults
  to ``/var/lib/crane/metadata/``

data_dir_polling_interval
  The number of seconds between checks for updates to metadata files in the ``data_dir``.
  This defaults to checking once every 60 seconds.

endpoint
  hostname and optional port, in the form ``hostname:port``, where crane
  is deployed. This is the value that will be returned for the
  ``X-Docker-Endpoint`` header. defaults to the host and port used by the
  requesting client


Example:

::

  [general]
  debug: true
  data_dir: /mnt/nfs/
  endpoint: localhost:5000


Search
------

Only one of the following search backends should be configured. If multiple
backends are configured, crane will attempt to use the first one whose configuration
it finds, and the discovery order is not guaranteed to be consistent.

GSA
~~~

The API supporting ``docker search`` can be enabled by configuring a Google
Search Appliance for use by crane. In crane's configuration file, a section
``[gsa]`` must exist with key ``url``. The URL will be used in a GET request,
and a query parameter ``q`` will be added with a search term.

Example:

::

  [gsa]
  url: https://path/to/my/search?x=1&y=2

.. warning:: crane does not currently verify the SSL certificate of the GSA

The XML returned by the GSA must contain values for ``portal_name`` and
``portal_short_description``, which will be turned into the name and
description returned by crane's search API.

Solr
~~~~

The API supporting ``docker search`` can be enabled by configuring a Solr
deployment for use by crane. In crane's configuration file, a section
``[solr]`` must exist with key ``url``. The URL will be used in a GET request,
and it must contain the string ``{0}`` as a placeholder where the search string
will be inserted.

Example:

::

  [solr]
  url: https://path/to/my/search?x={0}

.. warning:: crane does not currently verify the SSL certificate of the Solr service

The JSON returned by the request must contain the following minimum data
structure. Any additional keys and values will be ignored.

::

  {
    "response": {
      "docs": [
        {
          "allTitle": "pulp/worker",
          "ir_description": "A short description to display in the terminal"
        }
      ]
    }
  }


Deployment
----------

Sample apache configuration files are available in ``/usr/share/crane/`` when
installed via RPM, or in the ``deployment/`` directory if looking at the source.
You can copy one of them into your apache ``conf.d`` directory and optionally
modify it to fit your needs.


Repository Data
---------------

To change what data crane is using, add or remove files in the configured
``data_dir`` as necessary. The changes will be loaded automatically the next time the
``data_dir`` is polled for changes. This poll runs at the interval set by
``data_dir_polling_interval``. Auto loading of changes monitors file creation and deletion.
If a file is modified in place you may have to restart the web server in order for the change
to be loaded.

Data Format
-----------

Crane expects to find files in the configured ``data_dir`` whose names end in
``.json``. Nothing else about the file names is important to crane. Each file
contains metadata about a docker repository.

These files are produced by a publish action in
`Pulp <http://www.pulpproject.org>`_.
