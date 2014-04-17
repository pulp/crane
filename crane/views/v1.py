from flask import Blueprint, json, current_app


section = Blueprint('v1', __name__, url_prefix='/v1')


@section.after_request
def add_common_headers(response):
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
