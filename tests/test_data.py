import json
import os
import shutil
import tempfile
import time
import unittest

import mock

from crane import config, data
import demo_data


def _reset_response_data():
    """
    reset response data
    """
    data.v1_response_data = \
        {
            'repos': {},
            'images': {},
        }
    data.v2_response_data = \
        {
            'repos': {}
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


class TestLoadAll(unittest.TestCase):

    def setUp(self):
        _reset_response_data()

    def tearDown(self):
        """
        reset response data
        """
        _reset_response_data()

    @mock.patch('os.walk', return_value=[
                (demo_data.metadata_good_path, ('', ),
                 ('bar.json', 'baz.json', 'foo.json', 'nop.json', 'qux.json'))])
    def test_with_metadata_good(self, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # verify that images data is correct
        self.assertTrue('abc123' in data.v1_response_data['images'])
        self.assertEqual(data.v1_response_data['images']['abc123'], frozenset(['redhat/foo']))
        self.assertTrue('xyz789' in data.v1_response_data['images'])
        self.assertEqual(data.v1_response_data['images']['xyz789'], frozenset(['redhat/foo']))

        # make sure the Repo namedtuple is in the right place
        self.assertTrue(isinstance(data.v1_response_data['repos'].get('redhat/foo'), data.V1Repo))
        # spot-check a value
        self.assertEqual(data.v1_response_data['repos'].get('redhat/foo').url,
                         'http://cdn.redhat.com/foo/bar/images/')

    @mock.patch('os.walk', return_value=[
                (demo_data.metadata_good_path_v2, ('', ), ('bar.json', ))])
    def test_with_v2_metadata_good(self, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the Repo namedtuple is in the right place
        self.assertTrue(isinstance(data.v2_response_data['repos'].get('bar'), data.V2Repo))
        # spot-check a value
        self.assertEqual(data.v2_response_data['repos'].get('bar').url,
                         'http://cdn.redhat.com/bar/baz/images')

    @mock.patch.object(data.logger, 'error', spec_set=True)
    @mock.patch('os.walk', return_value=[
                (demo_data.metadata_bad_path, ('', ), ('wrong_version.json', ))])
    def test_with_metadata_bad(self, mock_error, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.v1_response_data['repos'], {})
        self.assertEqual(data.v1_response_data['images'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)

    @mock.patch.object(data.logger, 'error', spec_set=True)
    @mock.patch('os.walk', return_value=[
                (demo_data.metadata_bad_path_v2, ('', ), ('wrong_version_2.json', ))])
    def test_with_wrong_path(self, mock_error, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.v2_response_data['repos'], {})

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

    @mock.patch('crane.data.time.sleep')
    def test_data_dir_does_not_exist(self, mock_sleep):
        class MyException(Exception):
            pass
        mock_sleep.side_effect = MyException()
        self.app.config[config.KEY_DATA_DIR] = '/a/b/c/idontexist'

        self.assertRaises(MyException, data.monitor_data_dir, self.app)


class StartMonitoringDataDirTests(unittest.TestCase):

    @mock.patch('crane.data.time.time')
    @mock.patch('crane.data.threading.Thread')
    def test_monitoring_initialization(self, mock_thread, mock_time):
        mock_time.return_value = time.time()
        mock_app = mock.Mock()
        data.start_monitoring_data_dir(mock_app)
        mock_thread.assert_called_once_with(target=data.monitor_data_dir,
                                            args=(mock_app, mock_time.return_value))
        created_thread = mock_thread.return_value
        created_thread.setDaemon.assert_called_once_with(True)
        self.assertTrue(created_thread.start.called)
