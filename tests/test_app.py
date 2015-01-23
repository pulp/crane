import logging

from flask import Flask
import mock
import unittest2

from crane import app, config, app_util, exceptions, search
from crane.search import GSA
from crane.views import crane, v1
from . import demo_data


@mock.patch('os.environ.get', spec_set=True, return_value=demo_data.demo_config_path)
class TestCreateApp(unittest2.TestCase):
    def setUp(self):
        super(TestCreateApp, self).setUp()
        with mock.patch('crane.app.init_logging') as mock_init_logging:
            self.app = app.create_app()
        # hold this so one of the tests can inspect it
        self.mock_init_logging = mock_init_logging

    def test_returns_app(self, mock_environ_get):
        self.assertIsInstance(self.app, Flask)

    def test_loads_config(self, mock_environ_get):
        self.assertTrue(config.KEY_DATA_DIR in self.app.config)

    def test_blueprints_loaded(self, mock_environ_get):
        self.assertTrue(v1.section.name in self.app.blueprints)
        self.assertTrue(crane.section.name in self.app.blueprints)

    def test_handlers_added(self, mock_environ_get):
        handlers = self.app.error_handler_spec[None][None]
        self.assertEquals(handlers[0], (exceptions.HTTPError,
                                        app_util.http_error_handler))

    def test_calls_init_logging(self, mock_environ_get):
        self.mock_init_logging.assert_called_once_with()

    def test_calls_search(self, mock_environ_get):
        # reset to the default state
        search.backend = search.SearchBackend()

        # run the "create_app", which because of the mock_environ_get, will load
        # our demo config. That config has GSA info.
        with mock.patch('crane.app.init_logging'):
            app.create_app()

        # this will only be true if the search config was parsed
        self.assertIsInstance(search.backend, GSA)


@mock.patch('logging.Logger.addHandler', spec_set=True)
class TestInitLogging(unittest2.TestCase):
    def test_adds_handler(self, mock_add_handler):
        app.create_app()
        # make sure it was called
        self.assertEqual(mock_add_handler.call_count, 1)
        # make sure the first argument is the right type
        self.assertIsInstance(mock_add_handler.call_args[0][0], logging.Handler)
        # make sure the first argument was the only argument
        mock_add_handler.assert_called_once_with(mock_add_handler.call_args[0][0])


@mock.patch('logging.Logger.setLevel', spec_set=True)
class TestSetLogLevel(unittest2.TestCase):
    def setUp(self):
        super(TestSetLogLevel, self).setUp()
        with mock.patch('crane.app.init_logging') as mock_init_logging:
            self.app = app.create_app()

    def test_debug(self, mock_set_level):
        self.app.config['DEBUG'] = True

        app.set_log_level(self.app)

        # make sure it set the level to debug
        mock_set_level.assert_called_once_with(logging.DEBUG)

    def test_not_debug(self, mock_set_level):
        self.app.config['DEBUG'] = False

        app.set_log_level(self.app)

        # make sure it did not change the log level
        self.assertEqual(mock_set_level.call_count, 0)
