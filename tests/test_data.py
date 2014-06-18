import json
import unittest

import mock

from crane import config, data
import demo_data


def _reset_response_data():
    """
    reset response data
    """
    data.response_data = \
        {
            'repos': {},
            'images': {},
        }


class TestLoadFromFile(unittest.TestCase):
    def test_demo_file(self):
        repo_id, repo_tuple, image_ids = data.load_from_file(demo_data.foo_metadata_path)

        self.assertEqual(repo_id, 'redhat/foo')
        self.assertEqual(repo_tuple.url, 'http://cdn.redhat.com/foo/bar/images/')
        self.assertEqual(repo_tuple.url_path, '/foo/bar/images/')

        images = json.loads(repo_tuple.images_json)
        self.assertTrue({'id': 'abc123'} in images)
        self.assertTrue({'id': 'xyz789'} in images)

        tags = json.loads(repo_tuple.tags_json)
        self.assertEqual(tags.get('latest'), 'abc123')

    def test_wrong_version(self):
        self.assertRaises(ValueError, data.load_from_file, demo_data.wrong_version_path)


@mock.patch('glob.glob', spec_set=True)
class TestLoadAll(unittest.TestCase):

    def setUp(self):
        _reset_response_data()

    def tearDown(self):
        """
        reset response data
        """
        _reset_response_data()

    def test_with_metadata_good(self, mock_glob):
        mock_glob.return_value = [demo_data.foo_metadata_path]
        mock_app = mock.MagicMock()
        mock_app.config = config.config_defaults.copy()

        data.load_all(mock_app)

        # verify that images data is correct
        self.assertTrue('abc123' in data.response_data['images'])
        self.assertEqual(data.response_data['images']['abc123'], frozenset(['redhat/foo']))
        self.assertTrue('xyz789' in data.response_data['images'])
        self.assertEqual(data.response_data['images']['xyz789'], frozenset(['redhat/foo']))

        # make sure the Repo namedtuple is in the right place
        self.assertTrue(isinstance(data.response_data['repos'].get('redhat/foo'), data.Repo))
        # spot-check a value
        self.assertEqual(data.response_data['repos'].get('redhat/foo').url,
                         'http://cdn.redhat.com/foo/bar/images/')

    @mock.patch.object(data.logger, 'error', spec_set=True)
    def test_with_metadata_bad(self, mock_error, mock_glob):
        mock_glob.return_value = [demo_data.wrong_version_path]
        mock_app = mock.MagicMock()
        mock_app.config = config.config_defaults.copy()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.response_data['repos'], {})
        self.assertEqual(data.response_data['images'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)

    @mock.patch.object(data.logger, 'error', spec_set=True)
    def test_with_wrong_path(self, mock_error, mock_glob):
        mock_glob.return_value = ['/a/b/c/d.json']
        mock_app = mock.MagicMock()
        mock_app.config = config.config_defaults.copy()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.response_data['repos'], {})
        self.assertEqual(data.response_data['images'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)
