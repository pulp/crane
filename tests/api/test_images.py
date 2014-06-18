from ..test_app_util import FlaskContextBase
from crane import exceptions
from crane.api import images


class TestGetImageFileUrl(FlaskContextBase):

    def test_invalid_filename(self):
        self.assertRaises(exceptions.NotFoundException, images.get_image_file_url,
                          'def456', 'bad_file')

    def test_invalid_image_id(self):
        self.assertRaises(exceptions.NotFoundException, images.get_image_file_url,
                          'bad_image_id', 'ancestry')

    def test_repo_url_missing_trailing_slash(self):
        result = images.get_image_file_url('def456', 'ancestry')
        expected = 'http://cdn.redhat.com/bar/baz/images/def456/ancestry'
        self.assertEquals(result, expected)

    def test_repo_url_with_trailing_slash(self):
        result = images.get_image_file_url('abc123', 'ancestry')
        expected = 'http://cdn.redhat.com/foo/bar/images/abc123/ancestry'
        self.assertEquals(result, expected)
