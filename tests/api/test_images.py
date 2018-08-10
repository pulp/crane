import httplib
import os

from crane import exceptions, config
from crane.api import images

from ..test_app_util import FlaskContextBase


class TestGetImageFileUrl(FlaskContextBase):

    def test_invalid_filename(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            images.get_image_file_url('def456', 'foo')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_invalid_image_id(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            images.get_image_file_url('bad_image_id', 'ancestry')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_repo_url_missing_trailing_slash(self):
        result = images.get_image_file_url('def456', 'ancestry')
        expected = 'http://cdn.redhat.com/bar/baz/images/def456/ancestry'
        self.assertEquals(result, expected)

    def test_repo_url_with_trailing_slash(self):
        result = images.get_image_file_url('abc123', 'ancestry')
        expected = 'http://cdn.redhat.com/foo/bar/images/abc123/ancestry'
        self.assertEquals(result, expected)


class TestGetImageFilePath(FlaskContextBase):

    def test_invalid_filename(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            images.get_image_file_path('def456', 'foo')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_invalid_image_id(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            images.get_image_file_path('bad_image_id', 'ancestry')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def dir_v1(self, rel_path):
        return os.path.join(self.app.config[config.KEY_SC_CONTENT_DIR_V1], rel_path)

    def test_repo_path_ancestry(self):
        result = images.get_image_file_path('abc123', 'ancestry')
        expected = (self.dir_v1('foo/abc123/ancestry'), 'application/json')
        self.assertEquals(result, expected)

    def test_repo_path_layer(self):
        result = images.get_image_file_path('abc123', 'layer')
        expected = (self.dir_v1('foo/abc123/layer'), 'application/octet-stream')
        self.assertEquals(result, expected)
