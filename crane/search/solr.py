import httplib
import itertools
import json
import logging
import urllib

from .. import exceptions
from .base import HTTPBackend, SearchResult


_logger = logging.getLogger(__name__)


class Solr(HTTPBackend):
    def __init__(self, url_template):
        """
        :param url_template:    PEP3101 string that is a URL that will accept a
                                single argument to its .format() method, which
                                is the url-encoded search string.
        :type  url_template:    str
        """
        self.url_template = url_template

    def search(self, query):
        """
        Searches a Solr search backend based on a given query parameter.

        :param query:   a string representing the search input from a user that
                        should be passed through to the solr backend
        :type  query:   basestring

        :return:    a collection of search results as a generator of
                    SearchResult instances. These results have been filtered
                    to exclude any repositories that are not being served by
                    this deployment of this app.
        :rtype:     generator
        """
        quoted_query = urllib.quote(query)
        url = self.url_template.format(quoted_query)
        _logger.debug('searching with URL: %s' % url)

        body = self._get_data(url)

        results = self._parse(body)
        filtered_results = itertools.ifilter(self._filter_result, results)
        return itertools.imap(self._format_result, filtered_results)

    def _parse(self, body):
        """
        Processes the raw response body into search results

        :param body:    body from the web response object
        :type  body:    str

        :return:    generator of SearchResult instances
        :rtype:     generator
        """
        try:
            data = json.loads(body)
            for item in data['response']['docs']:
                yield SearchResult(item['allTitle'], item['ir_description'])
        except Exception, e:
            _logger.error('could not parse response body: %s' % e)
            _logger.exception('could not parse response')
            raise exceptions.HTTPError(httplib.BAD_GATEWAY,
                                       'error communicating with backend search service')
