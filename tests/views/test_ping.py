import json
import unittest

import crane.app


class TestPing(unittest.TestCase):
    def setUp(self):
        self.app = crane.app.create_app().test_client()

    def test_response(self):
        response = self.app.get('/v1/_ping')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Docker-Registry-Config'], 'common')
        self.assertEqual(response.headers['X-Docker-Registry-Standalone'], 'True')
        self.assertEqual(response.headers['X-Docker-Registry-Version'], '0.6.6')

        # the real docker-registry has only "True" as the body
        self.assertEqual(json.loads(response.data), True)
