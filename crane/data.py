from collections import namedtuple
import logging
import os
import threading
import time
import urlparse
import fnmatch
from flask import json

from . import config


logger = logging.getLogger(__name__)

v1_response_data = {
    'repos': {},
    'images': {},
}

v2_response_data = {
    'repos': {}
}

V1Repo = namedtuple('V1Repo', ['url', 'images_json', 'tags_json', 'url_path', 'protected'])
V2Repo = namedtuple('V2Repo', ['url', 'url_path', 'protected'])
V3Repo = namedtuple('V3Repo', ['url', 'url_path', 'schema2_data', 'protected'])


def load_from_file(path):
    """
    Load one specific repository's metadata from a json file

    :param path:    full path to the json file
    :type  path:    basestring

    :return:    tuple of repo_id (str), repo_tuple (Repo), image_ids (list)
                if the metadata corresponds to v1 registry. If metadata is for
                v2 registry, image_ids will be None.
    :rtype:     tuple

    :raises ValueError: if the "version" value in the metadata is not a supported
                        metadata schema version
    """
    with open(path) as json_file:
        repo_data = json.load(json_file)

    if repo_data['version'] not in (1, 2, 3):
        raise ValueError('metadata version %d not supported' % repo_data['version'])

    repo_id = repo_data['repo-registry-id']
    url_path = urlparse.urlparse(repo_data['url']).path

    if repo_data['version'] == 1:
        image_ids = [image['id'] for image in repo_data['images']]
        repo_tuple = V1Repo(repo_data['url'],
                            json.dumps(repo_data['images']),
                            json.dumps(repo_data['tags']),
                            url_path, repo_data.get('protected', False))
        return repo_id, repo_tuple, image_ids
    elif repo_data['version'] == 2:
        repo_tuple = V2Repo(repo_data['url'],
                            url_path, repo_data.get('protected', False))
        return repo_id, repo_tuple, None
    elif repo_data['version'] == 3:
        repo_tuple = V3Repo(repo_data['url'],
                            url_path,
                            json.dumps(repo_data['schema2_data']),
                            repo_data.get('protected', False))
        return repo_id, repo_tuple, None


def monitor_data_dir(app, last_modified=0):
    """
    Loop forever monitoring the data directory for changes and reload the data if any changes occur
    This checks for updates at the interval defined in the config file (Defaults to 60 seconds)

    :param app: the flask application
    :type  app: flask.Flask
    :param last_modified:   seconds since the epoch; if the data on disk is modified
                            after this time, it must be re-loaded.
    :type  last_modified:   int or float
    """
    data_dir = app.config[config.KEY_DATA_DIR]
    polling_interval = app.config[config.KEY_DATA_POLLING_INTERVAL]
    if not os.path.exists(data_dir):
        logger.error('The data directory specified does not exist: %s' % data_dir)
    while True:
        # Find all the subdirectories
        dirs = [dirpath for (dirpath, _, _) in os.walk(data_dir,
                                                       followlinks=True)]

        # Find the most recent mtime
        if dirs and not last_modified:
            try:
                last_modified = max(os.stat(dir).st_mtime for dir in dirs)
            except OSError:
                # One of the directories no longer exists since the
                # os.walk() call above. Load everything, sleep, and
                # try again.
                pass

        # Load everything
        load_all(app)

        # Wait for something to change
        while True:
            time.sleep(polling_interval)
            if not dirs:
                # The data directory didn't exist before so re-check
                break

            # Check if the modified time on any directory is newer
            # than the most recent change we saw
            try:
                logger.debug('Checking for new metadata files')
                most_recent = max(os.stat(dir).st_mtime for dir in dirs)
                if most_recent > last_modified:
                    last_modified = most_recent
                    break
            except OSError:
                # One of the directories no longer exists
                break


def start_monitoring_data_dir(app):
    """
    Spin off a daemon thread that monitors the data dir for changes and updates the app config
    if any changes occur.  This will guarantee a refresh of the app data the first time it is run

    :param app: the flask application
    :type  app: flask.Flask
    """
    now = time.time()
    # load the data once in a blocking fashion
    load_all(app)
    thread = threading.Thread(target=monitor_data_dir, args=(app, now))
    thread.setDaemon(True)
    thread.start()


def load_all(app):
    """
    Load all metadata files and replace the "response_data" value in this
    module.

    :param app: the flask application
    :type  app: flask.Flask
    """
    global v2_response_data
    v2_repos = {}

    global v1_response_data
    v1_repos = {}
    images = {}

    try:
        data_dir = app.config[config.KEY_DATA_DIR]
        logger.info('loading metadata from %s' % data_dir)
        # scan data dir recursively and pick json files
        paths = [os.path.join(dirpath, f)
                 for dirpath, dirnames, files in os.walk(data_dir,
                                                         followlinks=True)
                 for f in fnmatch.filter(files, '*.json')]
        # load data from each file
        for metadata_file_path in paths:
            repo_id, repo_tuple, image_ids = load_from_file(metadata_file_path)
            if isinstance(repo_tuple, V1Repo):
                v1_repos[repo_id] = repo_tuple
                for image_id in image_ids:
                    images.setdefault(image_id, set()).add(repo_id)
            else:
                v2_repos[repo_id] = repo_tuple

        # make each set immutable
        for image_id in images.keys():
            images[image_id] = frozenset(images[image_id])
        # replace old data structure with new
        v1_response_data = {
            'repos': v1_repos,
            'images': images,
        }
        v2_response_data = {
            'repos': v2_repos
        }
    except Exception, e:
        logger.error('aborting metadata load: %s' % str(e))
