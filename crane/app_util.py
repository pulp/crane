import httplib
import logging
from functools import wraps

from flask import request
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
        request.crane_data = data.response_data

    return request.crane_data
