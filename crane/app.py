from flask import Flask

from .views import v1
from . import config, data


def create_app():
    """
    Creates the flask app, loading blueprints and the configuration.

    :return:    flask app
    :rtype:     Flask
    """
    app = Flask(__name__)
    app.register_blueprint(v1.section)
    config.load(app)
    data.load_all(app)
    return app
