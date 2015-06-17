import json
import unittest

import mock

import crane.app


class TestUsers(unittest.TestCase):
    def setUp(self):
        with mock.patch('crane.app.init_logging'):
            self.app = crane.app.create_app().test_client()

    def test_post(self):
        response = self.app.post('/v1/users/')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Docker-Registry-Config'], 'common')
        self.assertEqual(response.headers['X-Docker-Registry-Version'], '0.6.6')

        self.assertEqual(json.loads(response.data), 'User Created')

    def test_get(self):
        response = self.app.get('/v1/users/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/json')
        self.assertEqual(response.headers['X-Docker-Registry-Config'], 'common')
        self.assertEqual(response.headers['X-Docker-Registry-Version'], '0.6.6')

        self.assertEqual(json.loads(response.data), 'OK')
