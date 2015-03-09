import httplib
import itertools
import logging
import urllib
import urlparse
import xml.etree.cElementTree as ET

from .. import exceptions
from .base import HTTPBackend, SearchResult


_logger = logging.getLogger(__name__)


class GSA(HTTPBackend):
    """
    This backend works with a Google Search Appliance. It was developed against
    version 3.2 of the Google Search Protocol.

    This expects to find two meta tag (MT) elements for each result element in
    the returned XML: one with the name "portal_name", and one with the name
    "portal_short_description".
    """
    def __init__(self, url):
        """
        :param url: full URL to a Google Search Appliance that will allow a
                    search operation. The query parameter "q" will be added to
                    the URL, and the result will be used in a GET request to
                    retrieve search results.
        :type  url: basestring
        """
        self.url = url
        # expand the url into its components once, and then we can re-assemble
        # the pieces (with the added query parameter) for each request.
        self.url_parts = urlparse.urlparse(url)
        self.params = urlparse.parse_qs(self.url_parts.query)

    def search(self, query):
        """
        Searches a Google Search Appliance based on a given query parameter.

        :param query:   a string representing the search input from a user that
                        should be passed through to the GSA
        :type  query:   basestring

        :return:    a collection of search results as a generator of
                    SearchResult instances. These results have been filtered
                    to exclude any repositories that are not being served by
                    this deployment of this app.
        :rtype:     generator
        """
        url = self._form_url(query)
        data = self._get_data(url)
        result_generator = self._parse_xml(data)
        filtered_results = itertools.ifilter(self._filter_result, result_generator)
        return itertools.imap(self._format_result, filtered_results)

    def _form_url(self, query):
        """
        Creates a full URL that can be used in a GET request to retrieve results
        from the GSA. This takes the url specified in a config file and adds
        the 'q' parameter with the query as its value.

        :param query:   a string representing the search input from a user that
                        should be passed through to the GSA
        :type  query:   basestring

        :return:    a full URL that can be used in a GET request
        :rtype:     basestring
        """
        params = self.params.copy()
        params['q'] = [query]
        parts = list(self.url_parts)
        parts[4] = urllib.urlencode(params, doseq=True)
        return urlparse.urlunparse(parts)

    @staticmethod
    def _parse_xml(data):
        """
        Parses the XML returned by a GSA and turns it into a generator of result
        instances.

        :param data:    XML data returned by a GET request to a Google Search
                        Appliance
        :type  data:    basestring

        :return:    a collection of search results as a generator of
                    SearchResult instances
        :rtype:     generator

        :raises exceptions.HTTPError: if there is an error parsing the XML
        """
        try:
            tree = ET.fromstring(data)
            # each result is in an element of type "R"
            for repo in tree.findall('./RES/R'):
                name = None
                description = ''
                # each attribute of the repo is returned in an element of type MT
                # that looks like: <MT N="portal_name" V="rhel7.0"/>
                for mt in repo.findall('./MT'):
                    if mt.attrib.get('N') == 'portal_name':
                        name = mt.attrib['V']
                    elif mt.attrib.get('N') == 'portal_short_description':
                        description = mt.attrib['V']

                if name is not None:
                    yield SearchResult(name, description, **SearchResult.result_defaults)

        except Exception:
            _logger.exception('could not parse xml')
            raise exceptions.HTTPError(httplib.BAD_GATEWAY,
                                       'error communicating with backend search service')
