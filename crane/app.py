from flask import Flask

from crane.views import v1
from crane import config, data
from crane import exceptions
from crane import app_util


def create_app():
    """
    Creates the flask app, loading blueprints and the configuration.

    :return:    flask app
    :rtype:     Flask
    """
    app = Flask(__name__)
    app.register_blueprint(v1.section)
    app.register_error_handler(exceptions.AuthorizationFailed, app_util.error_handler_auth_error)
    app.register_error_handler(exceptions.NotFoundException, app_util.error_handler_not_found)

    config.load(app)
    data.load_all(app)
    return app
