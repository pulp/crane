import mock
import unittest2

from crane.views import v2


class UtilTest(unittest2.TestCase):
    def test_get_accept_headers(self):
        tests = [
            (dict(), set()),
            (dict(Accept="a"), set(["a"])),
            (dict(Accept="a, b"), set(["a", "b"])),
            (dict(Accept="a,b"), set(["a", "b"])),
            (dict(Accept=" a ,  b  "), set(["a", "b"])),
            (dict(Accept="a; q=1, b"), set(["a", "b"])),
        ]
        req = mock.MagicMock()
        for headers, expected in tests:
            req.headers = headers
            self.assertEquals(expected, v2.get_accept_headers(req))
