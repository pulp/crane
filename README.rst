crane
=====

.. image:: https://travis-ci.org/pulp/crane.svg?branch=master
   :target: https://travis-ci.org/pulp/crane

.. image:: https://coveralls.io/repos/pulp/crane/badge.png?branch=master
   :target: https://coveralls.io/r/pulp/crane?branch=master

Configuration
-------------

A config file will be loaded from the path found in environment variable
``CRANE_CONFIG_PATH``. If not specified, the default location of
``/etc/crane.conf`` will be used.

The following options should go under a section named ``[general]``

debug
  ``true`` or ``false``, which sets Flask's ``DEBUG`` config option. defaults to
  ``false``

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


Deployment
----------

Sample apache configuration files are available in ``/usr/share/crane/`` when
installed via RPM, or in the ``deployment/`` directory if looking at the source.
You can copy one of them into your apache ``conf.d`` directory and optionally
modify it to fit your needs.


Repository Data
---------------

To change what data crane is using, add or remove files in the configured
``data_dir`` as necessary.  The changes will be picked up automatically during the
next polling done at the interval set by ``data_dir_polling_interval``


Data Format
-----------

Crane expects to find files in the configured ``data_dir`` whose names end in
``.json``. Nothing else about the file names is important to crane. Each file
contains metadata about a docker repository.

These files are produced by a publish action in
`Pulp <http://www.pulpproject.org>`_.
