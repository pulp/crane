import os
import unittest

import mock

from crane import config

demo_config_path = os.path.join(
    os.path.dirname(__file__),
    'data/demo_config.conf'
)


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.app = mock.MagicMock()
        self.app.config = {}

    @mock.patch('ConfigParser.ConfigParser.readfp', side_effect=IOError, spec_set=True)
    @mock.patch('os.environ.get', return_value=None, spec_set=True)
    def test_defaults(self, mock_get, mock_readfp):
        """
        test that when no config file is found, and no path was specified,
        default values get used.
        """
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is False)

    @mock.patch('os.environ.get', return_value='/a/b/c/idontexist', spec_set=True)
    def test_file_not_found(self, mock_get):
        """
        test that when no config file is found, and no path was specified,
        default values get used.
        """
        self.assertRaises(IOError, config.load, self.app)

    @mock.patch('os.environ.get', return_value=demo_config_path, spec_set=True)
    def test_demo_config(self, mock_get):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is True)
