from ConfigParser import ConfigParser
import logging
import os


_logger = logging.getLogger(__name__)


DEFAULT_CONFIG_PATH = '/etc/crane.conf'
CONFIG_ENV_NAME = 'CRANE_CONFIG_PATH'

SECTION_GENERAL = 'general'

KEY_DEBUG = 'debug'
KEY_DATA_DIR = 'data_dir'
KEY_ENDPOINT = 'endpoint'

SECTION_GSA = 'gsa'

KEY_URL = 'url'

config_defaults = {
    KEY_DEBUG: 'false',
    KEY_DATA_DIR: '/var/lib/crane/metadata/',
    KEY_ENDPOINT: '',
    KEY_URL: '',
}

def load(app):
    """
    Load the configuration and apply it to the app.

    :param app: a flask app
    :type  app: Flask

    :raises IOError: iff a non-default config path is specified but does not exist
    """
    config_path = os.environ.get(CONFIG_ENV_NAME) or DEFAULT_CONFIG_PATH
    parser = ConfigParser(defaults=config_defaults)
    try:
        with open(config_path) as config_file:
            parser.readfp(config_file)
        _logger.info('config loaded from %s' % config_path)
    except IOError:
        if config_path != DEFAULT_CONFIG_PATH:
            _logger.error('config file not found at path %s' % config_path)
            raise
        # if the user did not specify a config path and there is not a file
        # at the default path, just use the default settings.
        _logger.info('no config specified or found, so using defaults')

    # adding the empty section will allow defaults to be used below
    for section in [SECTION_GENERAL, SECTION_GSA]:
        if not parser.has_section(section):
            parser.add_section(section)

    # [general] section
    app.config['DEBUG'] = parser.getboolean(SECTION_GENERAL, KEY_DEBUG)
    app.config[KEY_DATA_DIR] = parser.get(SECTION_GENERAL, KEY_DATA_DIR)
    app.config[KEY_ENDPOINT] = parser.get(SECTION_GENERAL, KEY_ENDPOINT)

    # [gsa] section
    app.config[SECTION_GSA + '_' + KEY_URL] = parser.get(SECTION_GSA, KEY_URL)
