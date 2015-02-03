import logging

from .. import config
from .base import SearchBackend
from .gsa import GSA
from .solr import Solr


_logger = logging.getLogger(__name__)


# default to a backend that will always return 404
backend = SearchBackend()


def load_config(app):
    """
    parse the search config and instantiate a search backend if one is
    configured. sets the global "backend" value to be the new backend.

    :param app: flask application
    :type  app: flask.Flask
    """
    global backend

    gsa_url = app.config.get(config.SECTION_GSA, {}).get(config.KEY_URL)
    if gsa_url:
        backend = GSA(gsa_url)
        _logger.info('using GSA search backend')
        return
    solr_url = app.config.get(config.SECTION_SOLR, {}).get(config.KEY_URL)
    if solr_url:
        backend = Solr(solr_url)
        _logger.info('using solr search backend')
        return

    # reset to default if the config previously had one configured, but changed.
    _logger.info('no search backend configured')
    backend = SearchBackend()
