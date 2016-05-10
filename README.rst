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

See the `current development documentation <https://github.com/pulp/crane/tree/master/docs>`_
for more information.
