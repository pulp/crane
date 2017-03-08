from __future__ import absolute_import
import httplib
import os
from flask import Blueprint, json, current_app, redirect, request

from crane import app_util, exceptions
from crane.api import repository


section = Blueprint('v2', __name__, url_prefix='/v2')


@section.after_request
def add_common_headers(response):
    """
    Add headers to a response.

    All 200 responses get a content type of 'application/json', and all others
    retain their default.

    Headers are added to make this app look like the actual docker-registry.

    :param response:    flask response object for a request
    :type  response:    flask.Response

    :return:    a response object that has the correct headers
    :rtype:     flask.Response
    """
    # if response code is 200, assume it is JSON
    if response.status_code == 200:
        response.headers['Content-Type'] = 'application/json'
        response.headers['Docker-Distribution-API-Version'] = 'registry/2.0'
    return response


@section.route('/')
def v2():
    """
    Provides version support information for /v2 requests.

    :return: Empty JSON document in the response body
    :rtype:  flask.response
    """
    # "{}" is what the real docker-registry puts in the response body
    response = current_app.make_response(json.dumps({}))
    return response


@section.route('/<path:relative_path>')
def name_redirect(relative_path):
    """
    Redirects the client to the path from where the file can be accessed.

    :param relative_path: the relative path after /v2/.
    :type relative_path:  basestring

    :return:    302 redirect response
    :rtype:     flask.Response
    """
    name_component, path_component = app_util.validate_and_transform_repo_name(relative_path)
    base_url = repository.get_path_for_repo(name_component)
    if not base_url.endswith('/'):
        base_url += '/'

    if 'manifests' in path_component:
        schema2_data_json = repository.get_schema2_data_for_repo(name_component)
        if schema2_data_json:
            schema2_data = json.loads(schema2_data_json)
            manifest, identifier = path_component.split('/')
            # if it is a newer docker client it sets accept headers to manifest schema 1, 2 and list
            # if it is an older docker client, he doesnot set any of accept headers
            accept_headers = request.headers.get('Accept')
            schema2_mediatype = 'application/vnd.docker.distribution.manifest.v2+json'
            if schema2_mediatype in accept_headers and identifier in schema2_data:
                path_component = os.path.join(manifest, '2', identifier)
            else:
                path_component = os.path.join(manifest, '1', identifier)
    url = base_url + path_component
    return redirect(url)


@section.errorhandler(exceptions.HTTPError)
def handle_error(error):
    """
    Creates a v2 compatible error response.

    :param error:   exception raised to indicate that an HTTP error response
                    should be generated and returned.
    :type  error:   crane.exceptions.HTTPError

    :return:    error details in json within response body.
    :rtype:     flask.response
    """
    data = {"errors": [dict(code=str(error.status_code),
                            message=error.message or httplib.responses[error.status_code])]}
    response = current_app.make_response(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    response.status_code = error.status_code
    return response
