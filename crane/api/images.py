import httplib
import urlparse
import os

from flask import current_app
from crane import exceptions, config
from crane.app_util import authorize_image_id

VALID_IMAGE_FILES = frozenset(['ancestry', 'json', 'layer'])


@authorize_image_id
def get_image_file_url(image_id, repo_info, filename):
    """
    Return the url for a file in an image

    :param image_id: The identifier for the image
    :type image_id: basestring
    :param repo_info: The tuple containing the information about the repository
    :type repo_info: crane.data.Repo
    :param filename: The identifier for the file belonging to the image
    :type filename: basestring
    :returns: url for a file inside an image
    :rtype: str

    :raises NotFoundException: if the file specified is not known
    """
    if filename not in VALID_IMAGE_FILES:
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    base_url = repo_info.url

    if not base_url.endswith('/'):
        base_url += '/'

    return urlparse.urljoin(base_url, '/'.join((image_id, filename)))


@authorize_image_id
def get_image_file_path(image_id, repo_info, filename):
    """
    Return the file path for a file in an image

    :param image_id: The identifier for the image
    :type image_id: basestring
    :param repo_info: The tuple containing the information about the repository
    :type repo_info: crane.data.Repo
    :param filename: The identifier for the file belonging to the image
    :type filename: basestring
    :returns: file path for a file inside an image
    :rtype: tuple

    :raises NotFoundException: if the file specified is not known
    """

    if filename not in VALID_IMAGE_FILES:
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    if filename == 'layer':
        mediatype = 'application/octet-stream'
    else:
        mediatype = 'application/json'

    base_path = current_app.config.get(config.KEY_SC_CONTENT_DIR_V1)

    result = os.path.join(base_path, repo_info.repository, image_id, filename)

    return result, mediatype
