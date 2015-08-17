import os
import unittest

import mock

from crane import config
import demo_data


basepath = os.path.dirname(__file__)

gsa_config_path = os.path.join(basepath, 'data/gsa/crane.conf')
solr_config_path = os.path.join(basepath, 'data/solr/crane.conf')


class TestLoad(unittest.TestCase):
    def setUp(self):
        self.app = mock.MagicMock()
        self.app.config = {}

    @mock.patch('os.environ.get', new={config.CONFIG_ENV_NAME: '/dev/null'}.get,
                spec_set=True)
    def test_defaults(self):
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
        configured_solr_url = self.app.config.get(config.SECTION_SOLR, {}).get(config.KEY_URL)
        self.assertEqual(configured_solr_url, '')

    @mock.patch('os.environ.get', new={config.CONFIG_ENV_NAME: solr_config_path}.get,
                spec_set=True)
    def test_solr_url(self):
        config.load(self.app)

        self.assertEqual(self.app.config.get(config.SECTION_SOLR, {}).get(config.KEY_URL),
                         'http://foo/bar')

    @mock.patch('os.environ.get', new={config.CONFIG_ENV_NAME: gsa_config_path}.get,
                spec_set=True)
    def test_gsa_url(self):
        config.load(self.app)

        self.assertEqual(self.app.config.get(config.SECTION_GSA, {}).get(config.KEY_URL),
                         'http://foo/bar')

    @mock.patch('pkg_resources.resource_stream', side_effect=IOError, spec_set=True)
    def test_defaults_not_found(self, mock_resource_stream):
        self.assertRaises(IOError, config.load, self.app)

    @mock.patch('os.environ.get', return_value='/a/b/c/idontexist', spec_set=True)
    def test_file_not_found(self, mock_get):
        self.assertRaises(IOError, config.load, self.app)

    @mock.patch('crane.config.CONFIG_PATH', new='/a/b/c/idontexist')
    def test_default_config_path_doesnt_exist(self):
        config.load(self.app)

    @mock.patch('os.environ.get', new={config.CONFIG_ENV_NAME: demo_data.demo_config_path}.get,
                spec_set=True)
    def test_demo_config(self):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is True)

        configured_gsa_url = self.app.config.get(config.SECTION_GSA, {}).get(config.KEY_URL)
        self.assertEqual(configured_gsa_url, 'http://pulpproject.org/search')

    @mock.patch('crane.config.CONFIG_PATH', new='/a/b/c/idontexist')
    @mock.patch('os.environ.get', new={config.DEBUG_ENV_NAME: 'true'}.get, spec_set=True)
    def test_debug_env_variable_true(self):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is True)

    @mock.patch('crane.config.CONFIG_PATH', new='/a/b/c/idontexist')
    @mock.patch('os.environ.get', new={config.DEBUG_ENV_NAME: 'False'}.get, spec_set=True)
    def test_debug_env_variable_false(self):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is False)

    @mock.patch('crane.config.CONFIG_PATH', new='/a/b/c/idontexist')
    @mock.patch('os.environ.get', new={config.DEBUG_ENV_NAME: 'True'}.get, spec_set=True)
    def test_debug_env_variable_wrong_case(self):
        config.load(self.app)

        self.assertTrue(self.app.config.get('DEBUG') is True)


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
