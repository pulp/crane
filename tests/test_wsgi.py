import unittest

from flask import Flask

from crane import wsgi


class TestWSGI(unittest.TestCase):
    def test_application_exists(self):
        self.assertTrue(isinstance(wsgi.application, Flask))
