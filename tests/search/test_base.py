import httplib
import socket
import urllib2
import unittest2

import mock

from crane import exceptions
from crane.search import base


class TestSearchBackend(unittest2.TestCase):
    def setUp(self):
        super(TestSearchBackend, self).setUp()
        self.backend = base.SearchBackend()

    def test_search(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            self.backend.search('foo')

        # by default, the base backend does not implement search, and will
        # cause a 404 to be returned for every call.
        self.assertEqual(assertion.exception.status_code, httplib.NOT_FOUND)

    def test_format_result(self):
        result = base.SearchResult('rhel', 'Red Hat Enterprise Linux',
                                   **base.SearchResult.result_defaults)

        ret = self.backend._format_result(result)

        self.assertDictEqual(ret, {
            'name': 'rhel',
            'description': 'Red Hat Enterprise Linux',
            'is_trusted': False,
            'is_official': False,
            'star_count': 0,
            'should_filter': True,
        })

    def test_non_defaults(self):
        result = base.SearchResult('rhel', 'Red Hat Enterprise Linux',
                                   True, True, 8, False)

        ret = self.backend._format_result(result)

        self.assertDictEqual(ret, {
            'name': 'rhel',
            'description': 'Red Hat Enterprise Linux',
            'is_trusted': True,
            'is_official': True,
            'star_count': 8,
            'should_filter': False,
        })

    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True)
    def test_filter_authorized_result(self, mock_is_authorized):
        result = base.SearchResult('rhel', 'Red Hat Enterprise Linux',
                                   **base.SearchResult.result_defaults)

        ret = self.backend._filter_result(result)

        self.assertIs(ret, True)
        mock_is_authorized.assert_called_once_with(result.name)

    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True)
    def test_filter_nonauthorized_result(self, mock_is_authorized):
        result = base.SearchResult('rhel', 'Red Hat Enterprise Linux',
                                   **base.SearchResult.result_defaults)
        mock_is_authorized.side_effect = exceptions.HTTPError(httplib.NOT_FOUND)

        ret = self.backend._filter_result(result)

        self.assertIs(ret, False)
        mock_is_authorized.assert_called_once_with(result.name)


@mock.patch('urllib2.urlopen', spec_set=True)
class TestHTTPBackend(unittest2.TestCase):
    def setUp(self):
        super(TestHTTPBackend, self).setUp()
        self.backend = base.HTTPBackend()
        self.url = 'http://pulpproject.org/search'

    def test_returns_urlopen_response(self, mock_urlopen):
        response = mock.MagicMock()
        response.getcode.return_value = httplib.OK
        mock_urlopen.return_value = response

        ret = self.backend._get_data(self.url)

        # make sure the correct args were passed through
        mock_urlopen.assert_called_once_with(self.url, timeout=1)
        # make sure the response body is returned
        self.assertIs(ret, mock_urlopen.return_value.read.return_value)

    def test_non_200(self, mock_urlopen):
        response = mock.MagicMock()
        response.getcode.return_value = httplib.NOT_FOUND
        mock_urlopen.return_value = response

        with self.assertRaises(exceptions.HTTPError) as assertion:
            self.backend._get_data(self.url)

        # bad gateway is the correct response if the backend service returns a
        # non-200 response code.
        self.assertEqual(assertion.exception.status_code, httplib.BAD_GATEWAY)

    def test_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = socket.timeout

        with self.assertRaises(exceptions.HTTPError) as assertion:
            self.backend._get_data(self.url)

        # make sure that a timeout talking to the backend results in the
        # timeout error code
        self.assertEqual(assertion.exception.status_code, httplib.GATEWAY_TIMEOUT)

    def test_urlerror(self, mock_urlopen):
        mock_urlopen.side_effect = urllib2.URLError(reason='?')

        with self.assertRaises(exceptions.HTTPError) as assertion:
            self.backend._get_data(self.url)

        # make sure that a failure to connect results in the service unavailable
        # error code
        self.assertEqual(assertion.exception.status_code, httplib.SERVICE_UNAVAILABLE)
