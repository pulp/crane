import json
import time
from datetime import datetime

from crane import config
from tests.views import base
import mock

mock_time = mock.Mock()
mock_time.return_value = time.mktime(datetime(2020, 7, 4).timetuple())

class TestCDN(base.BaseCraneAPITest):
    def test_url_rewrite(self):
        self.app.config[config.SECTION_CDN][config.KEY_URL_MATCH] = 'cdn.redhat.com'
        self.app.config[config.SECTION_CDN][config.KEY_URL_REPLACE] = 'cdn.fedora.com'
        response = self.test_client.get('/v2/redhat/zoo/manifests/latest')

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers['Location'].startswith('http://cdn.fedora.com/zoo/bar'))

    @mock.patch('time.time', mock_time)
    def test_cdn_auth(self):
        self.app.config[config.SECTION_CDN][config.KEY_URL_AUTH_PARAM] = '_auth_'
        self.app.config[config.SECTION_CDN][config.KEY_URL_AUTH_TTL] = 600
        self.app.config[config.SECTION_CDN][config.KEY_URL_AUTH_SECRET] = 'abc123'
        response = self.test_client.get('/v2/redhat/zoo/manifests/latest')

        expected_time= int(time.time()) + 600
        self.assertEqual(response.status_code, 302)
        self.assertIn('?_auth_=', response.headers['Location'])
        self.assertIn('exp=%s~' % expected_time, response.headers['Location'])
