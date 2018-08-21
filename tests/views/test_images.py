from . import base


class TestImagesRedirect(base.BaseCraneAPITest):
    def test_invalid_file_name(self):
        response = self.test_client.get('/v1/images/abc123/notvalid')

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))

    def test_ancestry(self):
        response = self.test_client.get('/v1/images/abc123/ancestry')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertEqual(response.headers['Location'],
                         'http://cdn.redhat.com/foo/bar/images/abc123/ancestry')

    def test_json(self):
        response = self.test_client.get('/v1/images/abc123/json')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertEqual(response.headers['Location'],
                         'http://cdn.redhat.com/foo/bar/images/abc123/json')

    def test_layer(self):
        response = self.test_client.get('/v1/images/abc123/layer')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertEqual(response.headers['Location'],
                         'http://cdn.redhat.com/foo/bar/images/abc123/layer')

    def test_image_does_not_exist(self):
        response = self.test_client.get('/v1/images/idontexist/layer')

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))

    def test_image_url_without_trailing_slash(self):
        """
        Make sure that if the metadata has a url without a trailing slash,
        everything still works.
        """
        response = self.test_client.get('/v1/images/def456/layer')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        self.assertEqual(response.headers['Location'],
                         'http://cdn.redhat.com/bar/baz/images/def456/layer')


class TestImagesServeContent(base.BaseCraneAPITestServeContent):
    def test_ancestry(self):
        response = self.test_client.get('/v1/images/abc123/ancestry')
        self.verify_200(response, 'foo/abc123/ancestry', 'application/json', v1=True)

    def test_json(self):
        response = self.test_client.get('/v1/images/abc123/json')
        self.verify_200(response, 'foo/abc123/json', 'application/json', v1=True)

    def test_layer(self):
        response = self.test_client.get('/v1/images/abc123/layer')
        self.verify_200(response, 'foo/abc123/layer', 'application/octet-stream', v1=True)

    def test_json_does_not_exist(self):
        response = self.test_client.get('/v1/images/def456/json')

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))

    def test_image_does_not_exist(self):
        response = self.test_client.get('/v1/images/idontexist/layer')

        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
