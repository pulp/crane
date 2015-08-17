from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from contextlib import contextmanager
import logging
import os

import pkg_resources


_logger = logging.getLogger(__name__)


# the default location for a user-defined config file
CONFIG_PATH = '/etc/crane.conf'
# the environment variable whose value can override the CONFIG_PATH
CONFIG_ENV_NAME = 'CRANE_CONFIG_PATH'
# the environment variable whose value can override the debug setting
DEBUG_ENV_NAME = 'CRANE_DEBUG'
# the resource path for the config file containing default values
DEFAULT_CONFIG_RESOURCE = 'data/default_config.conf'

# general app settings
SECTION_GENERAL = 'general'
KEY_DEBUG = 'debug'
KEY_DATA_DIR = 'data_dir'
KEY_DATA_POLLING_INTERVAL = 'data_dir_polling_interval'
KEY_ENDPOINT = 'endpoint'

# google search appliance settings
SECTION_GSA = 'gsa'
SECTION_SOLR = 'solr'
KEY_URL = 'url'


def load(app):
    """
    Load the configuration and apply it to the app.

    :param app: a flask app
    :type  app: Flask

    :raises IOError: iff a non-default config path is specified but does not exist
    """
    # load default values from the included default config file
    try:
        with pkg_resources.resource_stream(__package__, DEFAULT_CONFIG_RESOURCE) as default_config:
            parser = ConfigParser()
            parser.readfp(default_config)
        read_config(app, parser)
    except IOError:
        _logger.error('could not open default config file')
        raise

    # load user-specified config values
    config_path = os.environ.get(CONFIG_ENV_NAME) or CONFIG_PATH
    try:
        with open(config_path) as config_file:
            parser = ConfigParser()
            parser.readfp(config_file)
        read_config(app, parser)
        _logger.info('config loaded from %s' % config_path)
    except IOError:
        if config_path != CONFIG_PATH:
            _logger.error('config file not found at path %s' % config_path)
            raise
        # if the user did not specify a config path and there is not a file
        # at the default path, just use the default settings.
        _logger.info('no config specified or found, so using defaults')


def read_config(app, parser):
    """
    Read the configuration from the parser, and apply it to the app

    :param app:     a flask app
    :type  app:     Flask
    :param parser:  a ConfigParser that has a file already loaded
    :type  parser:  ConfigParser
    """
    # "general" section settings
    with supress(NoSectionError):
        app.config['DEBUG'] = parser.getboolean(SECTION_GENERAL, KEY_DEBUG)

        # parse other "general" section values
        for key in (KEY_DATA_DIR, KEY_ENDPOINT):
            with supress(NoOptionError):
                app.config[key] = parser.get(SECTION_GENERAL, key)

        # parse "general" section values as integers
        for key in (KEY_DATA_POLLING_INTERVAL, ):
            with supress(NoOptionError):
                app.config[key] = int(parser.get(SECTION_GENERAL, key))

    app.config['DEBUG'] = app.config.get('DEBUG') or \
        os.environ.get(DEBUG_ENV_NAME, '').lower() == 'true'

    # "gsa" (Google Search Appliance) section settings
    with supress(NoSectionError):
        section = app.config.setdefault(SECTION_GSA, {})

        for key in (KEY_URL,):
            with supress(NoOptionError):
                section[key] = parser.get(SECTION_GSA, key)

    # "solr" section settings
    with supress(NoSectionError):
        section = app.config.setdefault(SECTION_SOLR, {})

        for key in (KEY_URL,):
            with supress(NoOptionError):
                section[key] = parser.get(SECTION_SOLR, key)


@contextmanager
def supress(*exceptions):
    """
    backported from python 3.4, because it's simple and awesome

    https://docs.python.org/3.4/library/contextlib.html#contextlib.suppress

    :param exceptions:  list of Exception or subclasses
    :type  exceptions:  list
    """
    try:
        yield
    except exceptions:
        pass
