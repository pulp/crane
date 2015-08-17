import httplib
import json

import mock

from crane.search.base import SearchResult, SearchBackend
import base


class TestSearch(base.BaseCraneAPITest):
    def test_no_query(self):
        response = self.test_client.get('/v1/search')

        self.assertEqual(response.status_code, httplib.BAD_REQUEST)

    def test_empty_query(self):
        response = self.test_client.get('/v1/search?q=')

        self.assertEqual(response.status_code, httplib.BAD_REQUEST)

    @mock.patch('crane.search.backend.search', spec_set=True)
    def test_with_results(self, mock_search):
        mock_search.return_value = [
            SearchBackend._format_result(SearchResult('rhel', 'Red Hat Enterprise Linux',
                                                      **SearchResult.result_defaults)),
        ]

        response = self.test_client.get('/v1/search?q=rhel')
        data = json.loads(response.data)

        self.assertDictEqual(data, {
            'query': 'rhel',
            'num_results': 1,
            'results': mock_search.return_value
        })

    @mock.patch('crane.search.backend.search', spec_set=True)
    def test_num_results(self, mock_search):
        mock_search.return_value = [
            SearchBackend._format_result(SearchResult('rhel', 'Red Hat Enterprise Linux',
                                                      **SearchResult.result_defaults)),
            SearchBackend._format_result(SearchResult('foo', 'Foo',
                                                      **SearchResult.result_defaults)),
            SearchBackend._format_result(SearchResult('bar', 'Bar',
                                                      **SearchResult.result_defaults)),
        ]

        response = self.test_client.get('/v1/search?q=rhel')
        data = json.loads(response.data)

        self.assertEqual(data['num_results'], 3)
