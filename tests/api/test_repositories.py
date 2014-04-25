import json
import os
import unittest

import crane.app
from crane import config, data


metadata_good_path = os.path.join(os.path.dirname(__file__), '../data/metadata_good/')


class TestRepository(unittest.TestCase):
    def setUp(self):
        self.app = crane.app.create_app()
        self.app.config[config.KEY_DATA_DIR] = metadata_good_path
        data.load_all(self.app)
        self.test_client = self.app.test_client()

    def tearDown(self):
        """
        reset response data
        """
        data.response_data = {
            'repos': {},
            'images': {},
        }

    def test_images(self):
        response = self.test_client.get('/v1/repositories/foo/images')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Docker-Registry-Config'], 'common')
        self.assertEqual(response.headers['X-Docker-Registry-Version'], '0.6.6')

        self.assertEqual(json.loads(response.data), ['abc123', 'xyz789'])

    def test_images_404(self):
        response = self.test_client.get('/v1/repositories/idontexist/images')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers['Content-Type'], 'text/html')

    def test_tags(self):
        response = self.test_client.get('/v1/repositories/foo/tags')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Docker-Registry-Config'], 'common')
        self.assertEqual(response.headers['X-Docker-Registry-Version'], '0.6.6')

        self.assertEqual(json.loads(response.data), {'latest': 'abc123'})

    def test_tags_404(self):
        response = self.test_client.get('/v1/repositories/idontexist/tags')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers['Content-Type'], 'text/html')
