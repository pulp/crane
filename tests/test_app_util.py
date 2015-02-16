import httplib

import mock
from rhsm import certificate, certificate2
import unittest2 as unittest

from crane import app_util
from crane import exceptions
from crane.data import Repo
import demo_data

from .views import base


@app_util.authorize_repo_id
def mock_repo_func(repo_id):
    return 'foo'


@app_util.authorize_image_id
def mock_image_func(image_id, repo_info):
    return 'foo'


class FlaskContextBase(base.BaseCraneAPITest):

    def setUp(self):
        super(FlaskContextBase, self).setUp()
        self.ctx = self.app.test_request_context('/')
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        super(FlaskContextBase, self).tearDown()


class TestAuthorizeRepoId(FlaskContextBase):

    def test_raises_not_found_if_repo_id_none(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_repo_func(None)
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_raises_not_found_if_repo_id_invalid(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_repo_func('bad_id')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    @mock.patch('crane.app_util._get_certificate')
    def test_raises_not_found_if_id_invalid(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_repo_func('qux')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    @mock.patch('crane.app_util._get_certificate')
    def test_passes_if_auth_valid(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        result = mock_repo_func('baz')
        self.assertEquals(result, 'foo')

    @mock.patch('crane.app_util._get_certificate')
    def test_bypass_if_not_protected(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        result = mock_repo_func('redhat/foo')
        self.assertEquals(result, 'foo')

    @mock.patch('crane.app_util._get_certificate')
    def test_auth_fails_if_no_path_matches_credentials(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_repo_func('qux')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)


class TestAuthorizeImageId(FlaskContextBase):

    def test_raises_not_found_if_image_id_none(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_image_func(None)
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_raises_not_found_if_image_id_invalid(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_image_func('invalid')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    @mock.patch('crane.app_util._get_certificate')
    def test_raises_auth_error_if_id_invalid(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        with self.assertRaises(exceptions.HTTPError) as assertion:
            mock_image_func('qux')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    @mock.patch('crane.app_util._get_certificate')
    def test_passes_if_auth_valid(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        result = mock_image_func('baz123')
        self.assertEquals(result, 'foo')

    @mock.patch('crane.app_util._get_certificate')
    def test_bypass_if_not_protected(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert
        result = mock_image_func('xyz789')
        self.assertEquals(result, 'foo')

    @mock.patch('crane.app_util._get_certificate')
    def test_not_authorized(self, mock_get_cert):
        cert = certificate.create_from_file(demo_data.demo_entitlement_cert_path)
        mock_get_cert.return_value = cert

        with self.assertRaises(exceptions.HTTPError) as assertion:
            result = mock_image_func('qux123')
        self.assertEquals(assertion.exception.status_code, httplib.NOT_FOUND)


class TestHandler(unittest.TestCase):

    def test_default_message(self):
        string_value, http_code = app_util.http_error_handler(
            exceptions.HTTPError(httplib.NOT_FOUND))
        self.assertEquals(string_value, httplib.responses[httplib.NOT_FOUND])
        self.assertEquals(http_code, httplib.NOT_FOUND)

    def test_custom_message(self):
        string_value, http_code = app_util.http_error_handler(
            exceptions.HTTPError(httplib.BAD_GATEWAY, 'Foo Error'))
        self.assertEquals(string_value, 'Foo Error')
        self.assertEquals(http_code, httplib.BAD_GATEWAY)


class TestGetCertificate(FlaskContextBase):

    def test_empty_cert(self):
        cert = app_util._get_certificate()
        self.assertEquals(cert, None)

    def test_non_entitlement_cert(self):
        with open(demo_data.demo_no_entitlement_cert_path) as test_cert:
            data = test_cert.read()
        self.ctx.request.environ['SSL_CLIENT_CERT'] = data
        cert = app_util._get_certificate()
        self.assertEquals(cert, None)

    def test_valid_cert(self):
        with open(demo_data.demo_entitlement_cert_path) as test_cert:
            data = test_cert.read()
        self.ctx.request.environ['SSL_CLIENT_CERT'] = data
        cert = app_util._get_certificate()
        self.assertTrue(isinstance(cert, certificate2.EntitlementCertificate))


class TestValidateAndTransformRepoID(unittest.TestCase):
    def test_more_than_one_slash(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            app_util.validate_and_transform_repoid('a/b/c')
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_library_namespace(self):
        ret = app_util.validate_and_transform_repoid('library/centos')

        self.assertEqual(ret, 'centos')

    def test_normal(self):
        ret = app_util.validate_and_transform_repoid('foo/bar')

        self.assertEqual(ret, 'foo/bar')


class TestValidateGetRepositories(unittest.TestCase):

    @mock.patch('crane.app_util.get_data')
    def test_get_repositories(self, mock_get_data):
        repo = Repo(url="",
                    images_json="[{\"id\": \"test-image1\"}, {\"id\": \"test-image2\"}]",
                    tags_json="{\"tag1\": \"test-image1\"}",
                    url_path="",
                    protected=False)
        mock_get_data.return_value = {'repos': {"test-repo": repo}}
        ret = app_util.get_repositories()
        self.assertEqual(ret['test-repo']['image-ids'], ['test-image1', 'test-image2'])
        self.assertEqual(ret['test-repo']['tags'], {'tag1': 'test-image1'})
        self.assertEqual(ret['test-repo']['protected'], False)

    @mock.patch('crane.app_util.get_data')
    def test_get_repositories_empty(self, mock_get_data):
        mock_get_data.return_value = {'repos': {}}
        ret = app_util.get_repositories()
        self.assertEqual(ret, {})
