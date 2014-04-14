from ConfigParser import ConfigParser
import logging
import os


logger = logging.getLogger(__name__)


DEFAULT_CONFIG_PATH = '/etc/crane.conf'

config_defaults = {
    'debug': 'false',
}


def load(app):
    """
    Load the configuration and apply it to the app.

    :param app: a flask app
    :type  app: Flask

    :raises:    IOError iff a non-default config path is specified but does not exist
    """
    config_path = os.environ.get('CRANE_CONFIG_PATH') or DEFAULT_CONFIG_PATH
    parser = ConfigParser(defaults=config_defaults)
    try:
        parser.readfp(open(config_path))
        logger.info('config loaded from %s' % config_path)
    except IOError:
        if config_path != DEFAULT_CONFIG_PATH:
            logger.error('config file not found at path %s' % config_path)
            raise
        # if the user did not specify a config path and there is not a file
        # at the default path, just use the default settings.
        logger.info('no config specified or found, so using defaults')

    # adding the empty section will allow defaults to be used below
    if not parser.has_section('general'):
        parser.add_section('general')

    app.config['DEBUG'] = parser.getboolean('general', 'debug')
