import os
import unittest2

from crane import app, config, data

import mock


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
