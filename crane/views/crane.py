"""
Non-public view for use by admins to see a list of repositories served by crane.
"""
from flask import Blueprint, current_app, json

from .. import app_util


section = Blueprint('crane', __name__, url_prefix='/crane')


@section.route('/repositories')
def repositories():
    """
    Returns a json document containing a dictionary of repositories served by crane
    and keyed by the repo-registry-id which is unique for each repository.

    TODO: Implement html view. We should return it as the default view and
          following json response should be returned if request.headers['Content-Type']
          is 'application/json'

    :return:    json string containing a list of docker repositories
    :rtype:     basestring
    """
    repo_data = app_util.get_repositories()
    response = current_app.make_response(json.dumps(repo_data))
    response.headers['Content-Type'] = 'application/json'

    return response
