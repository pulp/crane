import os

import mock
import unittest2

from crane import app, config, data


metadata_good_path = os.path.join(os.path.dirname(__file__), '../data/metadata_good/')


class BaseCraneAPITest(unittest2.TestCase):
    def setUp(self):
        with mock.patch('crane.app.init_logging'):
            self.app = app.create_app()
        self.app.config[config.KEY_DATA_DIR] = metadata_good_path
        self.app.config[config.KEY_ENDPOINT] = 'localhost:5000'
        self.app.config['DEBUG'] = True
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


published_good_path = os.path.join(os.path.dirname(__file__), '../data/published_good/')


class BaseCraneAPITestServeContent(BaseCraneAPITest):

    def setUp(self):
        super(BaseCraneAPITestServeContent, self).setUp()
        self.app.config[config.KEY_SC_ENABLE] = True
        self.app.config[config.KEY_SC_CONTENT_DIR_V1] = os.path.join(published_good_path, 'v1')
        self.app.config[config.KEY_SC_CONTENT_DIR_V2] = os.path.join(published_good_path, 'v2')

    def verify_200(self, response, rel_path, content_type, v1=False):
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], content_type)
        if v1:
            base_path = self.app.config[config.KEY_SC_CONTENT_DIR_V1]
        else:
            base_path = self.app.config[config.KEY_SC_CONTENT_DIR_V2]
            self.assertEqual(response.headers['Docker-Distribution-API-Version'], 'registry/2.0')
        self.assertEqual(response.headers['X-Sendfile'], os.path.join(base_path, rel_path))
