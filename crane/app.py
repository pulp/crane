import logging
import sys

from flask import Flask

from crane.views import crane, v1, v2
from crane import config
from crane import data
from crane import exceptions
from crane import app_util
from crane import search


def create_app():
    """
    Creates the flask app, loading blueprints and the configuration.

    :return:    flask app
    :rtype:     Flask
    """
    init_logging()

    app = Flask(__name__)
    app.register_blueprint(v1.section)
    app.register_blueprint(v2.section)
    app.register_blueprint(crane.section)
    app.register_error_handler(exceptions.HTTPError, app_util.http_error_handler)

    config.load(app)
    # in case the config says that debug mode is on, we need to adjust the
    # log level
    set_log_level(app)
    data.start_monitoring_data_dir(app)
    search.load_config(app)

    logging.getLogger(__name__).info('application initialized')
    return app


def init_logging():
    """
    setup up logging to use sys.stderr, which will go into the web server's logs.
    """
    logger = logging.getLogger('crane')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)


def set_log_level(app):
    """
    In case the config file says we should be in debug mode, set the log level
    to debug.

    :param app: flask app
    :type  app: flask.Flask
    """
    if app.config['DEBUG']:
        logger = logging.getLogger('crane')
        logger.setLevel(logging.DEBUG)
        logger.debug('debug log level enabled')
