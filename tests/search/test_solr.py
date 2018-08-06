import httplib
import json

import mock
import unittest2

from crane import exceptions
from crane.search import Solr
from crane.search.base import SearchResult


class BaseSolrTest(unittest2.TestCase):
    def setUp(self):
        super(BaseSolrTest, self).setUp()
        self.url = 'http://pulpproject.org/search?q={0}'
        self.solr = Solr(self.url)


class TestInit(BaseSolrTest):
    def test_stores_data(self):
        self.assertEqual(self.solr.url_template, self.url)


class TestSearch(BaseSolrTest):
    @mock.patch('crane.search.solr.Solr._get_data')
    def test_quotes_query(self, mock_parse):
        self.solr.search('hi mom')

        mock_parse.assert_called_once_with(self.url.format('hi%20mom'))

    @mock.patch('crane.search.solr.Solr._filter_result', spec_set=True, return_value=True)
    @mock.patch('crane.search.solr.Solr._get_data', spec_set=True)
    @mock.patch('crane.search.solr.Solr._parse')
    def test_workflow_filter_true(self, mock_parse, mock_get_data, mock_filter):
        mock_parse.return_value = [
            SearchResult('rhel', 'Red Hat Enterprise Linux',
                         True, True, 5, True)]

        ret = self.solr.search('foo')

        mock_get_data.assert_called_once_with('http://pulpproject.org/search?q=foo')
        self.assertDictEqual(list(ret)[0], {
            'name': 'rhel',
            'description': 'Red Hat Enterprise Linux',
            'star_count': 5,
            'is_trusted': True,
            'is_official': True,
            'should_filter': True
        })

    @mock.patch('crane.search.solr.Solr._filter_result', spec_set=True, return_value=False)
    @mock.patch('crane.search.solr.Solr._get_data', spec_set=True)
    @mock.patch('crane.search.solr.Solr._parse')
    def test_workflow_filter_true_with_defaults(self, mock_parse, mock_get_data, mock_filter):
        mock_parse.return_value = [SearchResult('rhel', 'Red Hat Enterprise Linux',
                                                **SearchResult.result_defaults)]

        ret = self.solr.search('foo')

        mock_get_data.assert_called_once_with('http://pulpproject.org/search?q=foo')
        self.assertEqual(len(list(ret)), 0)

    @mock.patch('crane.app_util.name_is_authorized', spec_set=True)
    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True, return_value=True)
    def test_workflow_filter_true_with_image_repository_document_kind(self, mock_is_authorized,
                                                                      mock_name_authorized):
        """
        When the should_filter attribute of SearchResult instance is True,
        the base implementation of the filter_results should be called and
        the return value should be the value returned by the mocked app_util.repo_is_authorized
        """
        mock_name_authorized.side_effect = exceptions.HTTPError(
            mock.Mock(status=404), 'not found')
        result = SearchResult(
            'rhel', 'Red Hat Enterprise Linux', False, False, 0, True)
        ret_val = self.solr._filter_result(result)
        self.assertEquals(ret_val, True)

    @mock.patch('crane.app_util.name_is_authorized', spec_set=True)
    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True)
    def test_workflow_filter_false_with_image_repository_document_kind(self, mock_is_authorized,
                                                                       mock_name_authorized):
        """
        When the should_filter attribute of SearchResult instance is True,
        the base implementation of the filter_results should be called and
        the return value should be based on the value returned/exception raised
        by the mocked app_util.repo_is_authorized
        """
        mock_is_authorized.side_effect = exceptions.HTTPError(
            httplib.NOT_FOUND)
        mock_name_authorized.side_effect = exceptions.HTTPError(
            httplib.NOT_FOUND)
        result = SearchResult(
            'rhel', 'Red Hat Enterprise Linux', False, False, 0, True)
        ret_val = self.solr._filter_result(result)
        self.assertEquals(ret_val, False)

    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True)
    def test_workflow_filter_false_with_should_filter_false(self, mock_is_authorized):
        """
        When the should_filter attribute of SearchResult instance is True,
        the base implementation of the filter_results should be called and
        the return value should be based on the value returned/exception raised
        by the mocked app_util.repo_is_authorized
        """
        mock_is_authorized.side_effect = exceptions.HTTPError(
            httplib.NOT_FOUND)
        result = SearchResult(
            'rhel', 'Red Hat Enterprise Linux', False, False, 0, False)
        ret_val = self.solr._filter_result(result)
        self.assertEquals(ret_val, True)

    @mock.patch('crane.app_util.name_is_authorized', spec_set=True)
    @mock.patch('crane.app_util.repo_is_authorized', spec_set=True)
    def test_workflow_filter_true_with_image_repository_with_defaults(self, mock_is_authorized,
                                                                      mock_name_is_authorised):
        """
        When the should_filter attribute of SearchResult instance is default which is False,
        the base implementation of the filter_results is not called
        """
        mock_name_is_authorised.side_effect = exceptions.HTTPError(
            mock.Mock(status=404), 'not found')
        result = SearchResult('rhel', 'Red Hat Enterprise Linux',
                              **SearchResult.result_defaults)
        ret_val = self.solr._filter_result(result)
        self.assertEquals(ret_val, True)


class TestParse(BaseSolrTest):
    def test_normal(self):
        result = list(self.solr._parse(json.dumps(fake_body)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)
        self.assertEqual(result[0].should_filter, False)

    def test_normal_with_document_kind_image_repository(self):
        result = list(
            self.solr._parse(json.dumps(fake_body_with_document_kind_image_repository)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, True)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

    def test_normal_with_document_kind_certified_software(self):
        result = list(
            self.solr._parse(json.dumps(fake_body_with_document_kind_certified_software)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

    def test_normal_with_document_kind_certified_software_multiple_pull(self):
        result = list(
            self.solr._parse(json.dumps(
                fake_body_with_document_kind_certified_software_multiple_pull)))

        self.assertEqual(len(result), 2)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

        self.assertTrue(isinstance(result[1], SearchResult))
        self.assertEqual(result[1].name, 'foo/baz')
        self.assertEqual(result[1].description, 'marketing speak yada yada')
        self.assertEqual(result[1].should_filter, False)
        self.assertTrue(result[1].is_official is True)
        self.assertTrue(result[1].is_trusted is True)
        self.assertEqual(result[1].star_count, 7)

    def test_normal_with_document_kind_certified_software_no_pull_command(self):
        result = list(self.solr._parse(
            json.dumps(fake_body_with_document_kind_certified_software_no_pull_command)))
        self.assertEqual(len(result), 0)

    def test_normal_with_abstract(self):
        result = list(self.solr._parse(json.dumps(fake_body_with_abstract)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

    def test_normal_with_abstract_and_document_kind_image_repository(self):
        result = list(self.solr._parse(
            json.dumps(fake_body_with_abstract_and_document_kind_image_repository)))

        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, True)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

    def test_normal_with_abstract_and_document_kind_certified_software(self):
        result = list(self.solr._parse(
            json.dumps(fake_body_with_abstract_and_document_kind_certified_software)))

        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(result[0].is_official is True)
        self.assertTrue(result[0].is_trusted is True)
        self.assertEqual(result[0].star_count, 7)

    def test_with_defaults(self):
        result = list(self.solr._parse(json.dumps(fake_body_with_defaults)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_with_defaults_and_document_kind_image_repository(self):
        result = list(self.solr._parse(
            json.dumps(fake_body_with_defaults_and_document_kind_image_repository)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, True)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_with_defaults_and_document_kind_certified_software(self):
        result = list(self.solr._parse(
            json.dumps(fake_body_with_defaults_and_document_kind_certified_software)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'marketing speak yada yada')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_with_defaults_and_abstract(self):
        result = list(
            self.solr._parse(json.dumps(fake_body_with_defaults_and_abstract)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_with_defaults_and_abstract_and_document_kind_image_repository(self):
        result = list(self.solr._parse(json.dumps(
            fake_body_with_defaults_and_abstract_and_document_kind_image_repository)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, True)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_with_defaults_and_abstract_and_document_kind_certified_software(self):
        result = list(self.solr._parse(json.dumps(
            fake_body_with_defaults_and_abstract_and_document_kind_certified_software)))

        self.assertEqual(len(result), 1)

        self.assertTrue(isinstance(result[0], SearchResult))
        self.assertEqual(result[0].name, 'foo/bar')
        self.assertEqual(result[0].description, 'test')
        self.assertEqual(result[0].should_filter, False)
        self.assertTrue(
            result[0].is_official is SearchResult.result_defaults['is_official'])
        self.assertTrue(
            result[0].is_trusted is SearchResult.result_defaults['is_trusted'])
        self.assertEqual(
            result[0].star_count, SearchResult.result_defaults['star_count'])

    def test_json_exception(self):
        """
        when an exception occurs, it should raise an HTTPError
        """
        with self.assertRaises(exceptions.HTTPError) as assertion:
            list(self.solr._parse('this is not valid json'))

        self.assertEqual(assertion.exception.status_code, httplib.BAD_GATEWAY)

    def test_attribute_exception(self):
        """
        when an exception occurs, it should raise an HTTPError
        """
        with self.assertRaises(exceptions.HTTPError) as assertion:
            list(self.solr._parse(json.dumps({})))

        self.assertEqual(assertion.exception.status_code, httplib.BAD_GATEWAY)


fake_body = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'ir_description': 'marketing speak yada yada',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
            }
        ]
    }
}

fake_body_with_document_kind_image_repository = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'ir_description': 'marketing speak yada yada',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'ImageRepository',
            }
        ]
    }
}

fake_body_with_document_kind_certified_software = {
    'response': {
        'docs': [
            {
                'c_pull_command': ['foo/bar'],
                'ir_description': 'marketing speak yada yada',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}

fake_body_with_document_kind_certified_software_multiple_pull = {
    'response': {
        'docs': [
            {
                'c_pull_command': ['docker pull foo/bar', 'docker pull foo/baz'],
                'ir_description': 'marketing speak yada yada',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}

fake_body_with_document_kind_certified_software_no_pull_command = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'ir_description': 'marketing speak yada yada',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}

fake_body_with_abstract = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'publishedAbstract': 'test',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
            }
        ]
    }
}

fake_body_with_abstract_and_document_kind_image_repository = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'publishedAbstract': 'test',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'ImageRepository',
            }
        ]
    }
}

fake_body_with_abstract_and_document_kind_certified_software = {
    'response': {
        'docs': [
            {
                'c_pull_command': ['foo/bar'],
                'publishedAbstract': 'test',
                'ir_automated': True,
                'ir_official': True,
                'ir_stars': 7,
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}


fake_body_with_defaults = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'ir_description': 'marketing speak yada yada',
            }
        ]
    }
}

fake_body_with_defaults_and_document_kind_image_repository = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'ir_description': 'marketing speak yada yada',
                'documentKind': 'ImageRepository',
            }
        ]
    }
}

fake_body_with_defaults_and_document_kind_certified_software = {
    'response': {
        'docs': [
            {
                'c_pull_command': ['foo/bar'],
                'ir_description': 'marketing speak yada yada',
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}

fake_body_with_defaults_and_abstract = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'publishedAbstract': 'test',
            }
        ]
    }
}

fake_body_with_defaults_and_abstract_and_document_kind_image_repository = {
    'response': {
        'docs': [
            {
                'allTitle': 'foo/bar',
                'publishedAbstract': 'test',
                'documentKind': 'ImageRepository',
            }
        ]
    }
}

fake_body_with_defaults_and_abstract_and_document_kind_certified_software = {
    'response': {
        'docs': [
            {
                'c_pull_command': ['foo/bar'],
                'publishedAbstract': 'test',
                'documentKind': 'CertifiedSoftware',
            }
        ]
    }
}
