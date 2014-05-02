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

All options should go under a section named ``[general]``

debug
  ``true`` or ``false``, which sets Flask's ``DEBUG`` config option. defaults to
  ``false``

data_dir
  full path to the directory from which metadata files should be loaded. defaults
  to ``/var/lib/crane/metadata/``

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


Deployment
----------

Sample apache configuration files are available in ``/usr/share/crane/`` when
installed via RPM, or in the ``deployment/`` directory if looking at the source.
You can copy one of them into your apache ``conf.d`` directory and optionally
modify it to fit your needs.


Repository Data
---------------

To change what data crane is using, add or remove files in the configured
``data_dir`` as necessary, and then reload your web server.


Data Format
-----------

Crane expects to find files in the configured ``data_dir`` whose names end in
``.json``. Nothing else about the file names is important to crane. Each file
contains metadata about a docker repository.

These files are produced by a publish action in
`Pulp <http://www.pulpproject.org>`_.
