from __future__ import absolute_import
from flask import Blueprint, json, current_app, redirect

from crane import app_util
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


@section.route('/<path:name>/<path:file_path>')
def name_redirect(name, file_path):
    """
    Redirects the client to the path from where the file can be accessed.

    :param name:    name of the repository. The combination of username and repo specifies
                    a repo id
    :type  name:    basestring

    :param file_path: the relative path
    :type file_path:  basestring

    :return:    302 redirect response
    :rtype:     flask.Response
    """

    # name, repo_name, path = app_util.validate_and_transform_repo_name(username, repo, file_path)
    full_path = '/'.join([name, file_path])

    name_component, path_component = app_util.validate_and_transform_repo_name(full_path)
    base_url = repository.get_path_for_repo(name_component)
    if not base_url.endswith('/'):
        base_url += '/'
    url = base_url + path_component
    return redirect(url)
