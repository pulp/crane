import json

from tests.views import base


class TestPath(base.BaseCraneAPITest):
    def test_invalid_repo_name(self):
        response = self.test_client.get('/v2/no/name/test')
        parsed_response_data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('application/json'))
        self.assertEqual(parsed_response_data['errors'][0]['code'], '404')
        self.assertEqual(parsed_response_data['errors'][0]['message'], 'Not Found')

    def test_valid_repo_name_for_manifest(self):
        # #3303: verify multi-valued headers too
        # manifest lists are evaluated first, so pass a longer media type that
        # matches the manifest list as a prefix
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.list.v2+jsonjunk,application/vnd.docker.distribution.manifest.v2+json'}  # noqa
        response = self.test_client.get('/v2/redhat/zoo/manifests/1.25.1-musl', headers=headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('zoo/bar/manifests/2/1.25.1-musl' in response.headers['Location'])

    def test_valid_repo_name_for_manifest_list(self):
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.list.v2+json'}
        response = self.test_client.get('/v2/redhat/zoo/manifests/latest', headers=headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('zoo/bar/manifests/list' in response.headers['Location'])

    def test_valid_repo_name_for_manifest_digest(self):
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        response = self.test_client.get('/v2/redhat/foo/manifests/123456789', headers=headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('foo/bar/manifests/1' in response.headers['Location'])

    def test_valid_repo_name_for_manifest_list_digest(self):
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.list.v2+json'}
        response = self.test_client.get('/v2/redhat/foo/manifests/123456789', headers=headers)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('foo/bar/manifests/1' in response.headers['Location'])

    def test_valid_repo_name_for_tags(self):
        response = self.test_client.get('/v2/redhat/foo/tags/latest')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('foo/bar/tags/latest' in response.headers['Location'])

    def test_valid_repo_name_for_blobs(self):
        response = self.test_client.get('/v2/redhat/foo/blobs/123')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('foo/bar/blobs/123' in response.headers['Location'])

    def test_valid_repo_name_without_trailing_slash(self):
        response = self.test_client.get('/v2/redhat/foo/blobs/123')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('/bar/blobs/123' in response.headers['Location'])

    def test_valid_repo_name_when_name_has_no_slashes(self):
        response = self.test_client.get('/v2/registry/blobs/123')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertTrue('/registry/blobs/123' in response.headers['Location'])

    def test_repo_name_without_manifest_or_tags_or_blobs(self):
        response = self.test_client.get('/v2/foo/test')
        parsed_response_data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('application/json'))
        self.assertEqual(parsed_response_data['errors'][0]['code'], '404')
        self.assertEqual(parsed_response_data['errors'][0]['message'], 'Not Found')
