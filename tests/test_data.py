import json
import os
import shutil
import tempfile
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

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.response_data['repos'], {})
        self.assertEqual(data.response_data['images'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)


class TestMonitorDataDir(unittest.TestCase):

    def setUp(self):
        self.working_dir = tempfile.mkdtemp()
        self.app = mock.Mock(config={config.KEY_DATA_DIR: self.working_dir,
                                     config.KEY_DATA_POLLING_INTERVAL: 60})
        self.test_file = os.path.join(self.working_dir, 'test.file')
        open(self.test_file, 'w').close()
        self.helper_method_called = False

    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_initial_load(self, mock_time, mock_load_all):
        mock_time.sleep.side_effect = Exception()
        self.assertRaises(Exception, data.monitor_data_dir, self.app)
        self.assertTrue(mock_load_all.called)

    def _add_file(self, *args, **kwargs):
        test_file_add = os.path.join(self.working_dir, 'test1.file')
        if not self.helper_method_called:
            self.helper_method_called = True
            open(test_file_add, 'w').close()
            return mock.DEFAULT
        raise Exception()

    @mock.patch('crane.data.os.stat')
    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_addition(self, mock_time, mock_load_all, mock_stat):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._add_file
        mock_stat.side_effect = [mock.Mock(st_mtime=1), mock.Mock(st_mtime=1),
                                 mock.Mock(st_mtime=5)]
        self.assertRaises(Exception, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _remove_file(self, *args, **kwargs):
        if not self.helper_method_called:
            self.helper_method_called = True
            os.unlink(self.test_file)
            return mock.DEFAULT
        raise Exception()

    @mock.patch('crane.data.os.stat')
    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_remove(self, mock_time, mock_load_all, mock_stat):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._remove_file
        mock_stat.side_effect = [mock.Mock(st_mtime=1), mock.Mock(st_mtime=1),
                                 mock.Mock(st_mtime=5)]
        self.assertRaises(Exception, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)


class StartMonitoringDataDirTests(unittest.TestCase):

    @mock.patch('crane.data.threading.Thread')
    def test_monitoring_initialization(self, mock_thread):
        mock_app = mock.Mock()
        data.start_monitoring_data_dir(mock_app)
        mock_thread.assert_called_once_with(target=data.monitor_data_dir,
                                            args=(mock_app,))
        created_thread = mock_thread.return_value
        created_thread.setDaemon.assert_called_once_with(True)
        self.assertTrue(created_thread.start.called)
