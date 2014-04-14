import unittest

from flask import Flask
import mock

from crane import app
from crane.views import v1


@mock.patch('crane.config.load', spec_set=True)
class TestCreateApp(unittest.TestCase):
    def test_returns_app(self, mock_load_config):
        ret = app.create_app()

        self.assertTrue(isinstance(ret, Flask))

    def test_loads_config(self, mock_load_config):
        ret = app.create_app()

        mock_load_config.assert_called_once_with(ret)

    def test_blueprints_loaded(self, mock_load_config):
        ret = app.create_app()

        self.assertTrue(v1.section.name in ret.blueprints)
