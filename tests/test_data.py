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
        self.assertEqual(repo_tuple.protected, False)

        images = json.loads(repo_tuple.images_json)
        self.assertTrue({'id': 'abc123'} in images)
        self.assertTrue({'id': 'xyz789'} in images)
        tags = json.loads(repo_tuple.tags_json)
        self.assertEqual(tags.get('latest'), 'abc123')

    def test_demo_file_v2(self):
        repo_id, repo_tuple, image_ids = data.load_from_file(demo_data.foo_v2_metadata_path)

        self.assertEqual(repo_id, 'redhat/foo2')
        self.assertEqual(repo_tuple.url, 'http://cdn.redhat.com/foo/bar')
        self.assertEqual(repo_tuple.url_path, '/foo/bar')
        self.assertEqual(repo_tuple.protected, False)

    def test_demo_file_v3(self):
        repo_id, repo_tuple, image_ids = data.load_from_file(demo_data.foo_v3_metadata_path)

        self.assertEqual(repo_id, 'redhat/foo')
        self.assertEqual(repo_tuple.url, 'http://cdn.redhat.com/foo/bar')
        self.assertEqual(repo_tuple.url_path, '/foo/bar')
        self.assertEqual(repo_tuple.protected, False)

        schema2_data = json.loads(repo_tuple.schema2_data)
        self.assertTrue('sha256:a1d963a97357110bdbfc70767a495c8df6ddfa9bda4da3183165ca73c3b99'
                        '0d2' in schema2_data)
        self.assertTrue('1.25.1-musl' in schema2_data)

    def test_demo_file_v4(self):
        repo_id, repo_tuple, image_ids = data.load_from_file(demo_data.foo_v4_metadata_path)

        self.assertEqual(repo_id, 'redhat/zoo')
        self.assertEqual(repo_tuple.url, 'http://cdn.redhat.com/zoo/bar')
        self.assertEqual(repo_tuple.url_path, '/zoo/bar')
        self.assertEqual(repo_tuple.protected, False)

        schema2_data = json.loads(repo_tuple.schema2_data)
        self.assertTrue('sha256:a1d963a97357110bdbfc70767a495c8df6ddfa9bda4da3183165ca73c3b99'
                        '0d2' in schema2_data)
        self.assertTrue('1.25.1-musl' in schema2_data)
        manifest_list_data = json.loads(repo_tuple.manifest_list_data)
        self.assertTrue('bar' in manifest_list_data)
        self.assertTrue('sha256:a90b7a658d44eadc569a296d45217115e61add1a7ae0958f084841c5f3ce7'
                        '956' in manifest_list_data)
        manifest_list_amd64 = json.loads(repo_tuple.manifest_list_amd64_tags)
        self.assertTrue('bar' in manifest_list_amd64.keys())
        expected = ["sha256:c55544de64a01e157b9d931f5db7a16554a14be19c367f91c9a8cdc46db086bf", 2]
        self.assertEqual(manifest_list_amd64['bar'], expected)

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
                         'http://access.redhat.com/webassets/docker/bar/baz/images')

    @mock.patch('os.walk', return_value=[
               (demo_data.metadata_good_path_v3, ('', ), ('foo_v3.json', ))])
    def test_with_v3_metadata_good(self, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the Repo namedtuple is in the right place
        self.assertTrue(isinstance(data.v2_response_data['repos'].get('redhat/foo'), data.V3Repo))
        # spot-check a value
        self.assertEqual(data.v2_response_data['repos'].get('redhat/foo').url,
                         'http://cdn.redhat.com/foo/bar')

    @mock.patch('os.walk', return_value=[
               (demo_data.metadata_good_path_v4, ('', ), ('zoo_v4.json', ))])
    def test_with_v4_metadata_good(self, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the Repo namedtuple is in the right place
        self.assertTrue(isinstance(data.v2_response_data['repos'].get('redhat/zoo'), data.V4Repo))
        # spot-check a value
        self.assertEqual(data.v2_response_data['repos'].get('redhat/zoo').url,
                         'http://cdn.redhat.com/zoo/bar')

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
        (demo_data.metadata_bad_path, ('',), ('invalid_link.json1',))])
    def test_with_metadata_bad_link(self, mock_error, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.v1_response_data['repos'], {})
        self.assertEqual(data.v1_response_data['images'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)

    @mock.patch.object(data.logger, 'error', spec_set=True)
    @mock.patch('os.walk', return_value=[
                (demo_data.metadata_bad_path_v2, ('', ), ('invalid_link_2.json', ))])
    def test_with_wrong_path(self, mock_error, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.v2_response_data['repos'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)

    @mock.patch.object(data.logger, 'error', spec_set=True)
    @mock.patch('os.walk', return_value=[
        (demo_data.metadata_bad_path_v2, ('',), ('wrong_version_2.json1',))])
    def test_with_wrong_path_v2_bad_link(self, mock_error, mock_walk):
        mock_app = mock.MagicMock()

        data.load_all(mock_app)

        # make sure the response data was not changed
        self.assertEqual(data.v2_response_data['repos'], {})

        # make sure an error was logged
        self.assertEqual(mock_error.call_count, 1)


class StopTest(Exception):
    pass


class TestMonitorDataDir(unittest.TestCase):

    def setUp(self):
        self.working_dir = tempfile.mkdtemp()
        self.app = mock.Mock(config={config.KEY_DATA_DIR: self.working_dir,
                                     config.KEY_DATA_POLLING_INTERVAL: 60})
        self.test_file = os.path.join(self.working_dir, 'test.file')
        open(self.test_file, 'w').close()
        self.test_dir = os.path.join(self.working_dir, 'testdir')
        self.test_file_in_dir = os.path.join(self.test_dir, 'test.file')
        os.mkdir(self.test_dir)
        open(self.test_file_in_dir, 'w').close()

        # Set the timestamps to be in the past
        for path in [self.test_file_in_dir,
                     self.test_dir,
                     self.test_file,
                     self.working_dir]:
            st = os.stat(path)
            os.utime(path, (st.st_atime, st.st_mtime - 1))

        self.helper_method_call_count = 0

    def tearDown(self):
        shutil.rmtree(self.working_dir, ignore_errors=True)

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_initial_load(self, mock_time, mock_load_all):
        mock_time.sleep.side_effect = StopTest()
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertTrue(mock_load_all.called)

    def _add_file_with_path(self, path):
        if self.helper_method_call_count < 2:
            self.helper_method_call_count += 1
            # First sleep: no action
            # Second sleep: add file
            if self.helper_method_call_count == 2:
                open(path, 'w').close()

            return mock.DEFAULT

        # Third sleep: stop test
        raise StopTest()

    def _add_file(self, *args, **kwargs):
        return self._add_file_with_path(os.path.join(self.working_dir,
                                                     'test1.file'))

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_addition(self, mock_time, mock_load_all):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._add_file
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _add_file_in_dir(self, *args, **kwargs):
        return self._add_file_with_path(os.path.join(self.test_dir,
                                                     'test2.file'))

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_addition_in_dir(self, mock_time, mock_load_all):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._add_file_in_dir
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _remove_file_with_path(self, path):
        if self.helper_method_call_count < 2:
            self.helper_method_call_count += 1
            # First sleep: no action
            # Second sleep: remove file
            if self.helper_method_call_count == 2:
                os.unlink(path)

            return mock.DEFAULT

        # Third sleep: stop test
        raise StopTest()

    def _remove_file(self, *args, **kwargs):
        return self._remove_file_with_path(self.test_file)

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_remove(self, mock_time, mock_load_all):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._remove_file
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _remove_file_in_dir(self, *args, **kwargs):
        return self._remove_file_with_path(self.test_file_in_dir)

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_remove_in_dir(self, mock_time, mock_load_all):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._remove_file_in_dir
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _remove_dir(self, *args, **kwargs):
        if self.helper_method_call_count < 2:
            self.helper_method_call_count += 1
            # First sleep: no action
            # Second sleep: remove file
            if self.helper_method_call_count == 2:
                shutil.rmtree(self.test_dir)

            return mock.DEFAULT

        # Third sleep: stop test
        raise StopTest()

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time')
    def test_monitor_remove_dir(self, mock_time, mock_load_all):
        mock_time.sleep.return_value = 0
        mock_time.sleep.side_effect = self._remove_dir
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)

    def _create_data_dir(self, *args, **kwargs):
        if self.helper_method_call_count < 2:
            self.helper_method_call_count += 1
            # First sleep: no action
            # Second sleep: remove file
            if self.helper_method_call_count == 2:
                os.mkdir(os.path.join(self.working_dir, 'idontexist'))

            return mock.DEFAULT

        # Third sleep: stop test
        raise StopTest()

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time.sleep')
    def test_data_dir_does_not_exist(self, mock_sleep, mock_load_all):
        mock_sleep.side_effect = self._create_data_dir
        self.app.config[config.KEY_DATA_DIR] = os.path.join(self.working_dir,
                                                            'idontexist')

        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertTrue(mock_load_all.call_count > 0)

    def _raise_oserror(self, *args, **kwargs):
        raise OSError

    def _only_sleep_once(self, *args, **kwargs):
        if self.helper_method_call_count:
            raise StopTest()

        self.helper_method_call_count += 1
        return mock.DEFAULT

    @mock.patch('crane.data.load_all')
    @mock.patch('crane.data.time.sleep')
    @mock.patch('os.stat')
    def test_monitor_dir_removed_on_init(self, mock_stat, mock_sleep,
                                         mock_load_all):
        mock_sleep.side_effect = self._only_sleep_once
        mock_stat.side_effect = self._raise_oserror
        self.assertRaises(StopTest, data.monitor_data_dir, self.app)
        self.assertEquals(mock_load_all.call_count, 2)


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
