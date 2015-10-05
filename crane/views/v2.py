from __future__ import absolute_import
from functools import partial
import httplib
import urllib2

from flask import Blueprint, json, current_app, redirect

from crane import app_util, exceptions
from crane.api import repository


section = Blueprint('v2', __name__, url_prefix='/v2')


def url_construct(name_component, path_component):
    """
    Returns the url for redirection based on name of the repo and
    appending it with path provided by path_component

    :param name_component: name of the repository
    :type name_component: basestring

    :param path_component: the relative path
    :type path_component: basestring

    :return: the complete url for redirection
    :rtype: basestring
    """
    base_url = repository.get_path_for_repo(name_component)
    if not base_url.endswith('/'):
        base_url += '/'
    url = base_url + path_component
    return url


def process_redirect(name, path):
    """
    Redirects the client to the path from where the file can be accessed.

    :param name:    name of the repository. The combination of username and repo specifies
                    a repo id
    :type  name:    basestring

    :param path: the relative path
    :type path:  basestring

    :return:    302 redirect response
    :rtype:     flask.Response
    """
    url = url_construct(name, path)
    return redirect(url)


def process_response(name, path, post_process=None):
    """
    Process a response based on whether response is a simple
    redirect or 200 OK with tags as body
    :param name:    name of the repository. The combination of username and
                    repo specifies a repo id
    :type  name:    basestring

    :param path: the relative path
    :type path:  basestring

    :param post_process: function to be called for post processing
    :type post_process: function

    :return: response
    :rtype: flask.response
    """
    url = url_construct(name, path)
    response = urllib2.urlopen(url, timeout=1).read()
    if post_process:
        response = post_process(response, extra={"name": name,
                                                 "file_path": path})
    return response


def tag_list(response, extra=None):
    """
    Return JSON document containing list of tags
    :param response: response to be processed
    :type response: httplib.response

    :param extra: dictionary containing values for name
                  and relative path
    :type extra:  dict

    :return: response with JSON document having tags as body
    :rtype: flask.response
    """
    tags = json.loads(response)
    tags_wrap = {"name": extra["name"], "tags": tags}
    return current_app.make_response(json.dumps(tags_wrap))


def get_manifest(response, extra=None):
    """
    Adds the docker-content-digest header to the response
    :param response: response to be processed
    :type response: httplib.response

    :param extra: dictionary containing values for name
                  and relative path
    :type extra:  dict

    :return: response
    :rtype: flask.response
    """
    reference = extra["file_path"].split("/")[1]
    tags = repository.get_v2_tags_for_repo(extra["name"])
    if reference in tags:
        digest = tags[reference]
    else:
        digest = reference
    response = current_app.make_response(response)
    response.headers['Docker-Content-Digest'] = digest
    return response


READONLY_API = {"manifests/": partial(process_response,
                                      post_process=get_manifest),
                "blobs/": process_redirect,
                "tags/list": partial(process_response,
                                     post_process=tag_list)}


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
    full_path = '/'.join([name, file_path])
    name_component, path_component = app_util.validate_and_transform_repo_name(full_path)

    if not any([value in path_component for value in READONLY_API.keys()]):
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    for path_tmpl in READONLY_API:
        if path_component.startswith(path_tmpl):
            return READONLY_API[path_tmpl](name_component, path_component)


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
