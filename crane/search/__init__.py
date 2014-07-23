from .. import config
from .base import SearchBackend
from .gsa import GSA


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

    url = app.config.get(config.SECTION_GSA + '_' + config.KEY_URL)
    if url:
        backend = GSA(url)
        return

    # reset to default if the config previously had one configured, but changed.
    backend = SearchBackend()
