from flask import Flask

from .views import v1
from . import config


def create_app():
    """
    Creates the flask app, loading blueprints and the configuration.

    :return:    flask app
    :rtype:     Flask
    """
    app = Flask(__name__)
    app.register_blueprint(v1.section)
    config.load(app)
    return app


if __name__ == '__main__': # pragma: no cover
    create_app().run(port=5001)
