import logging

from flask import request
from rhsm import certificate
from rhsm import certificate2

from crane import exceptions
from crane import data


logger = logging.getLogger(__name__)


def error_handler_not_found(error):
    """
    Processing method for turning a NotFoundException into the appropriate
    values for processing in Flask.
    """
    return str(error), 404


def error_handler_auth_error(error):
    """
    Processing method for turning an AuthorizationFailed into the appropriate
    values for processing in Flask.
    """
    return str(error), 403


def authorize_repo_id(func):
    """
    Authorize that a particular certificate has access to any directory
    containing the repository identified by repo_id
    """
    def wrapper(repo_id, *args, **kwargs):
        response_data = get_data()
        repo_tuple = response_data['repos'].get(repo_id)
        if repo_tuple is None:
            raise exceptions.NotFoundException()
        if repo_tuple.protected:
            cert = _get_certificate()
            if not cert or not cert.check_path(repo_tuple.url_path):
                raise exceptions.AuthorizationFailed()

        return func(repo_id, *args, **kwargs)

    return wrapper


def authorize_image_id(func):
    """
    Authorize that a particular certificate has access to any repo
    containing the specified image id
    """
    def wrapper(image_id, *args, **kwargs):
        response_data = get_data()
        image_repos = response_data['images'].get(image_id)
        if image_repos is None:
            raise exceptions.NotFoundException()

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
            raise exceptions.AuthorizationFailed()

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
