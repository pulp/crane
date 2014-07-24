import unittest

import mock

from crane import config
import demo_data


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.app = mock.MagicMock()
        self.app.config = {}

    @mock.patch('os.environ.get', return_value='/dev/null', spec_set=True)
    def test_defaults(self, mock_get):
        """
        test that when no config options are specified, default values get used.
        """
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is False)
        self.assertEqual(self.app.config.get(config.KEY_DATA_DIR), '/var/lib/crane/metadata/')
        self.assertEqual(self.app.config.get(config.KEY_ENDPOINT), '')
        self.assertEqual(self.app.config.get(config.KEY_DATA_POLLING_INTERVAL), 60)
        configured_gsa_url = self.app.config.get(config.SECTION_GSA, {}).get(config.KEY_URL)
        self.assertEqual(configured_gsa_url, '')

    @mock.patch('pkg_resources.resource_stream', side_effect=IOError, spec_set=True)
    def test_defaults_not_found(self, mock_resource_stream):
        self.assertRaises(IOError, config.load, self.app)

    @mock.patch('os.environ.get', return_value='/a/b/c/idontexist', spec_set=True)
    def test_file_not_found(self, mock_get):
        """
        test that when no config file is found, and no path was specified,
        default values get used.
        """
        self.assertRaises(IOError, config.load, self.app)

    @mock.patch('os.environ.get', return_value=demo_data.demo_config_path, spec_set=True)
    def test_demo_config(self, mock_get):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is True)

        configured_gsa_url = self.app.config.get(config.SECTION_GSA, {}).get(config.KEY_URL)
        self.assertEqual(configured_gsa_url, 'http://pulpproject.org/search')


class TestSupress(unittest.TestCase):
    def test_supression(self):
        with config.supress(ValueError):
            raise ValueError

    def test_does_not_over_supress(self):
        with config.supress(TypeError):
            self.assertRaises(ValueError, int, 'notanint')

    def test_supress_multiple(self):
        with config.supress(TypeError, ValueError):
            raise ValueError
