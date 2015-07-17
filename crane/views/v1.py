import httplib

from flask import Blueprint, json, current_app, redirect, request

from .. import app_util
from .. import config
from .. import exceptions
from ..api import repository, images
from .. import search as search_package


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


@section.route('/users', methods=['GET', 'POST'])
@section.route('/users/', methods=['GET', 'POST'])
def users():
    """
    Undocumented API path required for docker login when apache configured for auth
    See get_post_users()
    https://github.com/docker/docker-registry/blob/master/docker_registry/index.py
    """
    if request.method == 'GET':
        response = current_app.make_response(json.dumps('OK'))
        response.headers['X-Docker-Registry-Standalone'] = True
        return response
    response = current_app.make_response((json.dumps('User Created'), 201))
    response.headers['Content-Type'] = 'application/json'
    response.headers['X-Docker-Registry-Standalone'] = True
    return response


@section.route('/repositories/<path:repo_id>/images')
def repo_images(repo_id):
    """
    Returns a json document containing a list of image IDs that are in the
    repository with the given repo_id.

    Adds the "X-Docker-Endpoints" header.

    :param repo_id: unique ID for the repository. May contain 0 or 1 of the "/"
                    character.
    :type  repo_id: basestring

    :return:    json string containing a list of image IDs
    :rtype:     basestring
    """
    repo_id = app_util.validate_and_transform_repoid(repo_id)

    images_in_repo = repository.get_images_for_repo(repo_id)
    response = current_app.make_response(images_in_repo)
    # use the configured endpoint if any, otherwise default to the host of
    # the current request.
    configured_endpoint = current_app.config.get(config.KEY_ENDPOINT)
    response.headers['X-Docker-Endpoints'] = configured_endpoint or request.host
    return response


@section.route('/repositories/<path:repo_id>/tags')
def repo_tags(repo_id):
    """
    Returns a json document containing an object that maps tag names to image
    IDs.

    :param repo_id: unique ID for the repository. May contain 0 or 1 of the "/"
                    character. For repo IDs that do not contain a slash, the
                    docker client currently prepends "library/" when making
                    this call. This function strips that off.
    :type  repo_id: basestring

    :return:    json string containing an object mapping tag names to image IDs
    :rtype:     basestring
    """
    repo_id = app_util.validate_and_transform_repoid(repo_id)

    return repository.get_tags_for_repo(repo_id)


@section.route('/repositories/<path:repo_id>/tags/<tag_name>')
def repo_tags_get_tag(repo_id, tag_name):
    """
    Returns a json containing an object that has image id associated with the tag
    name.

    :param repo_id: unique ID for the repository. May contain 0 or 1 of the "/"
                    character. For repo IDs that do not contain a slash, the
                    docker client currently prepends "library/" when making
                    this call. This function strips that off.
    :type  repo_id: basestring

    :param tag_name: name of the tag whose associated image id has to be returned
    :type  tag_name: basestring

    :return:    json string containing an object having image id associated with tag name
    :rtype:     basestring
    """
    repo_id = app_util.validate_and_transform_repoid(repo_id)

    tags = repository.get_tags_for_repo(repo_id)
    image_id = json.loads(tags).get(tag_name)
    if image_id is None:
        raise exceptions.HTTPError(httplib.NOT_FOUND)
    return json.dumps(image_id)


@section.route('/search')
def search():
    """
    Returns a json document containing search results in the format expected
    from the docker index API.

    :return:    json structure containing search results
    :rtype:     basestring

    :raises exceptions.HTTPError:   if "q" is missing in the url's parameters,
                                    raises with 400 response coce
    """
    query = request.args.get('q', '')

    if not query:
        raise exceptions.HTTPError(httplib.BAD_REQUEST, message='parameter "q" is required')

    data = list(search_package.backend.search(query))
    response = {
        'query': query,
        'num_results': len(data),
        'results': data,
    }
    return json.dumps(response)


@section.route('/images/<image_id>/<filename>')
def images_redirect(image_id, filename):
    """
    Redirects (302) the client to a path where it can access the requested file.

    :param image_id:    the full unique ID of a docker image
    :type  image_id:    basestring
    :param filename:    one of "ancestry", "json", or "layer".
    :type  filename:    basestring

    :return:    302 redirect response
    :rtype:     flask.Response
    """
    image_url = images.get_image_file_url(image_id, filename)
    return redirect(image_url)
