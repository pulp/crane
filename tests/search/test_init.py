import inspect
import unittest2

import mock

from crane import config, search
from crane.search import SearchBackend, GSA


class TestLoadConfig(unittest2.TestCase):
    def test_default(self):
        mock_app = mock.MagicMock()
        mock_app.config = {}

        search.load_config(mock_app)

        # make sure the default backend is used when no settings are present
        # in the config
        self.assertIsInstance(search.backend, SearchBackend)
        # make sure it is not a subclass of SearchBackend
        self.assertIs(inspect.getmro(search.backend.__class__)[0], SearchBackend)

    def test_gsa(self):
        mock_app = mock.MagicMock()
        fake_url = 'http://pulpproject.org/search'
        mock_app.config = {
            config.SECTION_GSA + '_' + config.KEY_URL: fake_url,
        }

        search.load_config(mock_app)

        self.assertIsInstance(search.backend, GSA)
        self.assertEqual(search.backend.url, fake_url)
