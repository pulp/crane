from flask import abort, Blueprint, json, current_app

from .. import data


section = Blueprint('v1', __name__, url_prefix='/v1')


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
    # current stable release of docker-registry
    response.headers['X-Docker-Registry-Version'] = '0.6.6'
    # "common" is documented by docker-registry as a valid config, but I am
    # just guessing that it will work in our case.
    response.headers['X-Docker-Registry-Config'] = 'common'

    return response


@section.route('/_ping')
def ping():
    # "True" is what the real docker-registry puts in the response body
    response = current_app.make_response(json.dumps(True))
    response.headers['X-Docker-Registry-Standalone'] = True
    return response


@section.route('/repositories/<repo_id>/images')
def repo_images(repo_id):
    """
    Returns a json document containing a list of image IDs that are in the
    repository with the given repo_id.

    :param repo_id: unique ID for the repository
    :type  repo_id: basestring

    :return:    json string containing a list of image IDs
    :rtype:     basestring
    """
    try:
        return data.response_data['repos'][repo_id].images_json
    except KeyError:
        abort(404)


@section.route('/repositories/<repo_id>/tags')
def repo_tags(repo_id):
    """
    Returns a json document containing an object that maps tag names to image
    IDs.

    :param repo_id: unique ID for the repository
    :type  repo_id: basestring

    :return:    json string containing an object mapping tag names to image IDs
    :rtype:     basestring
    """
    try:
        return data.response_data['repos'][repo_id].tags_json
    except KeyError:
        abort(404)
