import httplib
import logging
from functools import wraps

from flask import json, request
from rhsm import certificate
from rhsm import certificate2

from crane import exceptions
from crane import data


logger = logging.getLogger(__name__)


def http_error_handler(error):
    """
    handle HTTPError exceptions and return the associated error message and HTTP
    response code. This uses the response code specified on the exception. It
    will use a message defined on the response object if present, or else it
    will default to the standard message associated with the error code.

    :param error:   exception raised to indicate that an HTTP error response
                    should be generated and returned
    :type  error:   crane.exceptions.HTTPError

    :return:    message and HTTP response code that should be returned in an
                HTTP response.
    :rtype:     basestring, int
    """
    message = error.message or httplib.responses[error.status_code]
    return message, error.status_code


def authorize_repo_id(func):
    """
    Authorize that a particular certificate has access to any directory
    containing the repository identified by repo_id

    :param repo_id: The identifier for the repository
    :type repo_id: str
    :rtype: function
    """

    @wraps(func)
    def wrapper(repo_id, *args, **kwargs):
        # will raise an appropriate exception if not found or not authorized
        repo_is_authorized(repo_id)
        return func(repo_id, *args, **kwargs)

    return wrapper


def repo_is_authorized(repo_id):
    """
    determines if the current request is authorized to read the given repo ID.

    :param repo_id: name of the repository being accessed
    :type  repo_id: basestring

    :raises exceptions.HTTPError: if authorization fails
                                  403: if the user is not authorized
                                  404: if the repo does not exist in this app
    """
    response_data = get_data()
    repo_tuple = response_data['repos'].get(repo_id)

    # if this deployment of this app does not know about the requested repo
    if repo_tuple is None:
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    if repo_tuple.protected:
        cert = _get_certificate()
        if not cert or not cert.check_path(repo_tuple.url_path):
            # return 404 so we don't reveal the existence of repos that the user
            # is not authorized for
            raise exceptions.HTTPError(httplib.NOT_FOUND)


def authorize_image_id(func):
    """
    Authorize that a particular certificate has access to any repo
    containing the specified image id

    :param image_id: The identifier of an image being served by Crane
    :type image_id: str
    :rtype: function
    """

    @wraps(func)
    def wrapper(image_id, *args, **kwargs):
        response_data = get_data()
        image_repos = response_data['images'].get(image_id)
        if image_repos is None:
            raise exceptions.HTTPError(httplib.NOT_FOUND)
        found_match = False

        # Check if an uprotected repo matches the request

        # Check if a protected repo matches the request
        cert = _get_certificate()
        repo_tuple = None

        for repo_id in image_repos:
            repo_tuple = response_data['repos'].get(repo_id)
            # if the repo is unprotected or the path is supported
            if not repo_tuple.protected:
                found_match = True
                break
            elif cert and cert.check_path(repo_tuple.url_path):
                found_match = True
                break

        if not found_match:
            # return 404 so we don't reveal the existence of images that the user
            # is not authorized for
            raise exceptions.HTTPError(httplib.NOT_FOUND)

        return func(image_id, repo_tuple, *args, **kwargs)

    return wrapper


def _get_certificate():
    """
    Get the parsed certificate from the environment

    :rtype: rhsm.certificate2.EntitlementCertificate, or None
    """
    env = request.environ
    pem_str = env.get('SSL_CLIENT_CERT', '')
    if not pem_str:
        return None
    cert = certificate.create_from_pem(pem_str)
    # The certificate may not be an entitlement certificate in which case we also return None
    if not isinstance(cert, certificate2.EntitlementCertificate):
        return None
    return cert


def get_data():
    """
    Get the current data used for processing requests from
    the flask request context.  This is used so the same
    set of data will be used for the entirety of a single request

    :returns: response_data dictionary as defined in crane.data
    :rtype: dict
    """
    if not hasattr(request, 'crane_data'):
        request.crane_data = data.v1_response_data

    return request.crane_data


def get_v2_data():
    """
    Get the current data used for processing requests from
    the flask request context.  This is used so the same
    set of data will be used for the entirety of a single request.

    :returns: response_data dictionary as defined in crane.data
    :rtype: dict
    """
    if not hasattr(request, 'crane_data_v2'):
        request.crane_data_v2 = data.v2_response_data

    return request.crane_data_v2


def get_repositories():
    """
    Get the current data used for processing requests from the flask request context
    and format it to display basic information about image ids and tags associated
    with each repository.

    Value corresponding to each key(repo-registry-id) is a dictionary itself
    with the following format:
    {'image-ids': [<image-id1>, <image-id2>, ...],
     'tags': {<tag-id1>: <tag1>, <tag-id2>: <tag2>, ...}
     'protected': true/false}

    :return: dictionary keyed by repo-registry-ids
    :rtype: dict
    """
    all_repo_data = get_data().get('repos', {})
    relevant_repo_data = {}
    for repo_registry_id, repo in all_repo_data.items():
        image_ids = [image_json['id'] for image_json in json.loads(repo.images_json)]

        relevant_repo_data[repo_registry_id] = {'image_ids': image_ids,
                                                'tags': json.loads(repo.tags_json),
                                                'protected': repo.protected}

    return relevant_repo_data


def validate_and_transform_repoid(repo_id):
    """
    Validates that the repo ID does not contain more than one slash, and removes
    the default "library" namespace if present.

    :param repo_id: unique ID for the repository. May contain 0 or 1 of the "/"
                    character. For repo IDs that do not contain a slash, the
                    docker client currently prepends "library/" when making
                    this call. This function strips that off.
    :type  repo_id: basestring

    :return:    repo ID without the "library" namespace
    :rtype:     basestring
    """
    # a valid repository ID will have zero or one slash
    if len(repo_id.split('/')) > 2:
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    # for repositories that do not have a "/" in the name, docker will add
    # "library/" to the beginning of the repository path.
    if repo_id.startswith('library/'):
        return repo_id[len('library/'):]
    return repo_id


def name_is_authorized(name):
    """
    Determines if the current request is authorized to read the given repo name.

    :param name: name of the repository being accessed
    :type  name: basestring

    :raises exceptions.HTTPError: if authorization fails
                                  403: if the user is not authorized
                                  404: if the repo does not exist in this app
    """
    v2_response_data = get_v2_data()
    v2_repo_tuple = v2_response_data['repos'].get(name)

    # if this deployment of this app does not know about the requested repo
    if v2_repo_tuple is None:
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    if v2_repo_tuple.protected:
        cert = _get_certificate()
        if not cert or not cert.check_path(v2_repo_tuple.url_path):
            # return 404 so we don't reveal the existence of repos that the user
            # is not authorized for
            raise exceptions.HTTPError(httplib.NOT_FOUND)


def authorize_name(func):
    """
    Authorize that a particular certificate has access to any directory
    containing the repository identified by repo_name.

    :param repo_id: The identifier for the repository
    :type repo_id: str
    :rtype: function
    """

    @wraps(func)
    def wrapper(repo_id, *args, **kwargs):
        # will raise an appropriate exception if not found or not authorized
        name_is_authorized(repo_id)
        return func(repo_id, *args, **kwargs)

    return wrapper


def validate_and_transform_repo_name(path):
    """
    Checks and extracts a repo registry id from the path parameter. The
    repo name is considered to be the substring left of any of the [tags, manifests,
    blobs].

    :param path: value for full path component containing both repo name and file path
    :type path: basestring

    :return: tuple containing extracted name and path components
    :rtype: tuple
    """

    path_components = ['tags', 'manifests', 'blobs']
    name_component = ''
    path_component = ''

    if not any([value in path for value in path_components]):
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    for component in path_components:
        if component in path:
            name_component = path.split(component, 1)[0].strip('/')
            path_component = component + path.split(component, 1)[1]

    return name_component, path_component
