import unittest

from flask import Flask
import mock


@mock.patch('crane.app.init_logging')
class TestWSGI(unittest.TestCase):
    def test_application_exists(self, mock_init_logging):
        from crane import wsgi
        self.assertTrue(isinstance(wsgi.application, Flask))
