What is Crane?
--------------

Crane is a small read-only web application that provides enough of the docker
registry API to support "docker pull". Crane does not serve the actual image
files, but instead serves 302 redirects to some other location where files are
being served. A base file location URL can be specified per-repository.

Crane loads its data from json files stored on disk. It does not have a
database or use any other services. The json files can be generated with Pulp
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
  full path to the directory from which metadata files should be loaded. The app files may
  optionally be in the root ``data_dir``, or in subdirectories as desired. defaults
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


.. Note::

   Ensure that Apache is listening on the specified port.


.. Note::
   The path specified in `data_dir` should be a shared mount point between Crane and Pulp.
   This mount point should be readable and writable by Pulp. Crane only needs read access
   to this mount.



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
and a query parameter ``q`` will be added with a search term. This is available
only for V1 docker content.

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
will be inserted. The search returns both results containing both V1
as well as V2 docker content.

Example:

::

  [solr]
  url: https://path/to/my/search?x={0}

.. warning:: crane does not currently verify the SSL certificate of the Solr service

The JSON returned by the request must contain the following minimum data
structure. ``ir_automated``, ``ir_official``, and ``ir_stars`` are optional and
will default to ``False``, ``False``, and ``0`` respectively.

::

  {
    "response": {
      "docs": [
        {
          "allTitle": "pulp/worker",
          "ir_description": "A short description to display in the terminal",
          "ir_automated": true,
          "ir_official": true,
          "ir_stars": 7
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


Crane Admin
-----------

A list of repositories served by Crane can be obtained by opening ``/crane/repositories``
or ``/crane/repositories/v1`` for repositories with v1 content and ``/crane/repositories/v2``
for repositories with v2 content in a web browser or with ``curl``. The default Apache
configuration distributed with Crane restricts access to this URL from ``localhost`` only;
when accessed from a web browser, repositories and some basuc info is listed on a web page.
This URL accepts an optional "Accept" header. When "application/json" is specified, the application
responds with JSON. Here is an example of repository with v1 content:

.. code-block:: json

    {
        "pulpdemo-busybox": {
            "image_ids": [
                "2982ec56c8d910121e7594ca7890b062f6d37fadf7575f6a6f3adbabbafac9f5",
                "2aed48a4e41d3931167146e9b7492aa5639e7f6478be9eac584726ecec6824ed",
                "492dad4279bae5bb73648efe9bf467b2cfa8bab1d593595226e3e7a95d9f6c35",
                "4986bf8c15363d1c5d15512d5266f8777bfba4974ac56e3270e7760f6f0a8125",
                "511136ea3c5a64f264b78b5433614aec563103b4d4702f3ba7d4d2698e22c158",
                "618b1fc306b06d11e192812ede4c685dcbf886d2a0189e9a552c550fd7663df0",
                "df7546f9f060a2268024c8a230d8639878585defcc1bc6f79d2728a13957871b",
                "e8a999563c473139dc74d02eefb7b13ffea63799bc05b8936b9ad7119b37742f",
                "ea13149945cb6b1e746bf28032f02e9b5a793523481a0a18645fc77ad53c4ea2",
                "f6169d24347d30de48e4493836bec15c78a34f08cc7f17d6a45a19d68dc283ac"
            ],
            "protected": false,
            "tags": {
                "buildroot-2013.08.1": "2982ec56c8d910121e7594ca7890b062f6d37fadf7575f6a6f3adbabbafac9f5",
                "buildroot-2014.02": "2aed48a4e41d3931167146e9b7492aa5639e7f6478be9eac584726ecec6824ed",
                "latest": "4986bf8c15363d1c5d15512d5266f8777bfba4974ac56e3270e7760f6f0a8125",
                "ubuntu-12.04": "492dad4279bae5bb73648efe9bf467b2cfa8bab1d593595226e3e7a95d9f6c35",
                "ubuntu-14.04": "f6169d24347d30de48e4493836bec15c78a34f08cc7f17d6a45a19d68dc283ac"
            }
        },
        "pulpdemo-busybox2": {
            "image_ids": [
                "2982ec56c8d910121e7594ca7890b062f6d37fadf7575f6a6f3adbabbafac9f5",
                "2aed48a4e41d3931167146e9b7492aa5639e7f6478be9eac584726ecec6824ed",
                "492dad4279bae5bb73648efe9bf467b2cfa8bab1d593595226e3e7a95d9f6c35",
                "4986bf8c15363d1c5d15512d5266f8777bfba4974ac56e3270e7760f6f0a8125",
                "511136ea3c5a64f264b78b5433614aec563103b4d4702f3ba7d4d2698e22c158",
                "618b1fc306b06d11e192812ede4c685dcbf886d2a0189e9a552c550fd7663df0",
                "df7546f9f060a2268024c8a230d8639878585defcc1bc6f79d2728a13957871b",
                "e8a999563c473139dc74d02eefb7b13ffea63799bc05b8936b9ad7119b37742f",
                "ea13149945cb6b1e746bf28032f02e9b5a793523481a0a18645fc77ad53c4ea2",
                "f6169d24347d30de48e4493836bec15c78a34f08cc7f17d6a45a19d68dc283ac"
            ],
            "protected": false,
            "tags": {
                "buildroot-2013.08.1": "2a4d48a4e51d39a1167146e9b7492aa5639e7f6478be9eac584726ecec6824ed",
                "latest": "4986bf8c15363d1c5d15512d5266f8777bfba4974ac56e3270e7760f6f0a8125",
                "ubuntu-12.04": "492dad4279bae5bb73648efe9bf467b2cfa8bab1d593595226e3e7a95d9f6c35",
                "ubuntu-14.04": "f6169d24347d30de48e4493836bec15c78a34f08cc7f17d6a45a19d68dc283ac"
            }
        }
    }


User Authentication
-------------------

Basic username/passphrase authentication may be configured using standard Apache configuration.
End-users access images by client command ``docker login <crane-registry-uri>``. End-users who
``docker pull <image>`` before logging in will be prompted for username/passphrase.

Crane does not manage users. They must be managed with an ``.htpasswd`` file. The ``htpasswd``
tool is available to manage the ``.htpasswd`` file. See `Apache htpasswd documentation <http://httpd.apache.org/docs/current/programs/htpasswd.html>`_.

Configuration may be enabled through an Apache config or ``.htaccess`` file. See `Apache htaccess documentation <https://httpd.apache.org/docs/current/howto/htaccess.html>`_.

Example ``.htaccess`` file:

.. code-block:: none

    AuthType Basic
    AuthName "Authentication Required"
    AuthUserFile /path/to/.htpasswd
    Require valid-user

Example ``apache.conf`` file:

.. code-block:: none

    <VirtualHost *>
        WSGIScriptAlias / /usr/share/crane/crane.wsgi
        <Location /crane>
            Require host localhost
            AuthType Basic
            AuthName "Docker Registry Repository"
            AuthUserFile /path/to/.htpasswd
            Require valid-user
        </Location>
    </VirtualHost>


Release Notes
-------------

3.1.0

The 3.1.0 release of Crane adds support for the Solr search to return results
containing V1 as well as V2 docker content.

3.0.0

The 3.0.0 release of Crane adds support for the Docker v2 API manifest lists schema version 2.
Crane now supports version 4 of the json data file produced by Pulp. The new version enables
Crane to serve manifest lists. In order to decide to which manifest type to redirect
the request, Crane looks for an optional accept header specified in the request and based on this
information redirects whether to the manifest list or image manifest.

2.1.0

The 2.1.0 release of Crane adds support for the Docker v2 API manifests schema version 2.
Crane now supports version 3 of the json data file produced by Pulp. The new version enables
Crane to serve schema version 2 manifests. In order to decide to wich schema version to redirect
the request, Crane looks for an optional accept header specified in the request and based on this
information redirects whether to schema version 1 or 2.

2.0.0
~~~~~

The 2.0.0 release of Crane adds support for the Docker v2 API, and is capable of working with
pulp_docker's new v2 app file format in addition to the v1 format that it did before. In order to
facilitate supporting both v1 and v2, it was modified to support a folder heirarchy in its data
folder watching feature. It is now possible to create subfolders in crane's data folder to separate
v1 and v2 app files and Crane will autodiscover them and serve them as appropriate.

Attribution
-----------

The image of the crane displayed in the corner of the web interface is used with permission from
user Laitche under `Creative Commons Attribution-Share Alike 3.0 Unported
<http://creativecommons.org/licenses/by-sa/3.0/deed.en>`_ licence. The original file can be found
`here
<http://commons.wikimedia.org/wiki/File:Laitche_Origami_Cranes_-_The_beige_One_-_right.png>`_.
