import httplib
import inspect
import os
import urlparse
import unittest2
import mock

from crane import exceptions
from crane.search.base import SearchResult
from crane.search.gsa import GSA


basepath = os.path.dirname(__file__)

rhel70_xml_path = os.path.join(basepath, '../data/gsa/rhel70.xml')
with open(rhel70_xml_path) as f:
    rhel70_xml = f.read()

rhel70_no_desc_xml_path = os.path.join(basepath, '../data/gsa/rhel70_no_desc.xml')
with open(rhel70_no_desc_xml_path) as f:
    rhel70_no_desc_xml = f.read()


class BaseGSATest(unittest2.TestCase):
    def setUp(self):
        super(BaseGSATest, self).setUp()
        self.url = 'http://pulpproject.org/search'
        self.gsa = GSA(self.url)


class TestInit(BaseGSATest):
    def test_stores_data(self):
        self.assertEqual(self.gsa.url_parts.hostname, 'pulpproject.org')
        self.assertEqual(self.gsa.url_parts.path, '/search')
        self.assertEqual(self.gsa.url_parts.scheme, 'http')
        self.assertDictEqual(self.gsa.params, {})


class TestSearch(BaseGSATest):
    @mock.patch('crane.search.gsa.GSA._filter_result', spec_set=True, return_value=True)
    @mock.patch('crane.search.gsa.GSA._get_data', spec_set=True)
    @mock.patch('crane.search.gsa.GSA._parse_xml')
    def test_workflow_filter_true(self, mock_parse_xml, mock_get_data, mock_filter):
        mock_parse_xml.return_value = [SearchResult('rhel', 'Red Hat Enterprise Linux',
                                                    **SearchResult.result_defaults)]

        ret = self.gsa.search('foo')

        mock_get_data.assert_called_once_with('http://pulpproject.org/search?q=foo')
        self.assertDictEqual(list(ret)[0], {
            'name': 'rhel',
            'description': 'Red Hat Enterprise Linux',
            'star_count': 0,
            'is_trusted': False,
            'is_official': False,
        })

    @mock.patch('crane.search.gsa.GSA._filter_result', spec_set=True, return_value=False)
    @mock.patch('crane.search.gsa.GSA._get_data', spec_set=True)
    @mock.patch('crane.search.gsa.GSA._parse_xml')
    def test_workflow_filter_false(self, mock_parse_xml, mock_get_data, mock_filter):
        mock_parse_xml.return_value = [SearchResult('rhel', 'Red Hat Enterprise Linux',
                                                    **SearchResult.result_defaults)]

        ret = self.gsa.search('foo')

        mock_get_data.assert_called_once_with('http://pulpproject.org/search?q=foo')
        self.assertEqual(len(list(ret)), 0)


class TestFormURL(unittest2.TestCase):
    def test_adds_query_param(self):
        gsa = GSA('http://pulpproject.org/search')

        url = gsa._form_url('foo')

        self.assertEqual(url, 'http://pulpproject.org/search?q=foo')

    def test_appends_query_param(self):
        gsa = GSA('https://pulpproject.org/search?x=1&y=2')

        url = gsa._form_url('foo')

        # verify that all of the pieces are correct.
        parts = urlparse.urlparse(url)
        self.assertEqual(parts.hostname, 'pulpproject.org')
        self.assertEqual(parts.scheme, 'https')
        self.assertEqual(parts.path, '/search')
        params = urlparse.parse_qs(parts.query)
        self.assertDictEqual(params, {'q': ['foo'], 'x': ['1'], 'y': ['2']})


class TestParseXML(BaseGSATest):
    def test_success(self):
        generator = self.gsa._parse_xml(rhel70_xml)

        self.assertTrue(inspect.isgenerator(generator))

        items = list(generator)

        self.assertListEqual(items, [
            SearchResult('rhel7.0', 'Red Hat Enterprise Linux 7 base image',
                         **SearchResult.result_defaults),
            SearchResult('redhat/rhel7.0', 'Red Hat Enterprise Linux 7 base image',
                         **SearchResult.result_defaults),
        ])

    def test_no_description(self):
        """test when the description is missing from the XML"""
        generator = self.gsa._parse_xml(rhel70_no_desc_xml)
        items = list(generator)

        self.assertListEqual(items, [
            SearchResult('rhel7.0', '', **SearchResult.result_defaults),
        ])

    def test_handle_exception(self):
        with self.assertRaises(exceptions.HTTPError) as assertion:
            list(self.gsa._parse_xml('this is not xml'))

        self.assertEqual(assertion.exception.status_code, httplib.BAD_GATEWAY)
