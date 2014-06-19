import unittest

from flask import Flask
import mock

from crane import app, config, app_util, exceptions
from crane.views import v1
from . import demo_data


@mock.patch('os.environ.get', spec_set=True, return_value=demo_data.demo_config_path)
class TestCreateApp(unittest.TestCase):
    def test_returns_app(self, mock_environ_get):
        ret = app.create_app()

        self.assertTrue(isinstance(ret, Flask))

    def test_loads_config(self, mock_environ_get):
        ret = app.create_app()

        self.assertTrue(config.KEY_DATA_DIR in ret.config)

    def test_blueprints_loaded(self, mock_environ_get):
        ret = app.create_app()

        self.assertTrue(v1.section.name in ret.blueprints)

    def test_handlers_added(self, mock_environ_get):
        ret = app.create_app()
        handlers = ret.error_handler_spec[None][None]
        self.assertEquals(handlers[0], (exceptions.AuthorizationFailed,
                                        app_util.error_handler_auth_error))
        self.assertEquals(handlers[1], (exceptions.NotFoundException,
                                        app_util.error_handler_not_found))
