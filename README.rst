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
  ``true`` or ``false``, which sets Flask's ``DEBUG`` config option.


Example:

::

  [general]
  debug: true
