from collections import namedtuple
import httplib
import logging
import socket
import urllib2

from .. import app_util
from .. import exceptions


_logger = logging.getLogger(__name__)


class SearchBackend(object):
    """
    Base class that all search backends should inherit from. This defines the
    search() method signature and provides other functionality that may be
    useful across different search implementations.
    """
    def search(self, query):
        """
        Searches a backend service based on a given query parameter.

        :param query:   a string representing the search input from a user that
                        should be passed through to a search service
        :type  query:   basestring

        :return:    a collection of search results as a generator of
                    SearchResult instances
        :rtype:     generator
        """
        raise exceptions.HTTPError(httplib.NOT_FOUND)

    @staticmethod
    def _format_result(result):
        """
        Given an individual SearchResult, this will return a dictionary in the
        structure that "docker search" expects.

        :param result: one result of a search
        :type  result: SearchResult

        :return:    dictionary containing the search result data in the form that
                    docker expects to receive.
        :rtype:     dict
        """
        return dict(result._asdict())

    def _filter_result(self, result):
        """
        Determines if a given result object, which represents a repository, is
        both known by this app (aka we have it in the app data), and if the user
        is authorized to access it.

        :param result:  one search result
        :type  result:  SearchResult
        :return:    True iff the repository is known and the user is authorized,
                    else False
        :rtype:     bool
        """
        try:
            app_util.repo_is_authorized(result.name)
        except exceptions.HTTPError:
            return False
        return True


class HTTPBackend(SearchBackend):
    """
    This provides functionality that may be useful across different search
    implementations that use HTTP to communicate with a backend service.
    """
    @staticmethod
    def _get_data(url):
        """
        Gets data from a URL and handles various HTTP-related error conditions.
        Any search implementation that uses an HTTP-based backend service should
        be able to use this method for GET requests.

        :param url: a complete URL that will be used for a GET request
        :type  url: basestring

        :return:    the content of the response body
        :rtype:     basestring

        :raises exceptions.HTTPError:   if there is a problem performing the
                                        GET request.
                                        502: if the response is not 200
                                        503: if urllib2 raises an exception while
                                             performing the request
                                        504: if the backend takes too long
        """
        try:
            # one second timeout
            response = urllib2.urlopen(url, timeout=1)
        except socket.timeout:
            _logger.error('timeout communicating with backend search service')
            raise exceptions.HTTPError(httplib.GATEWAY_TIMEOUT)
        except urllib2.URLError, e:
            _logger.error('error communicating with backend search service: %s' % e.reason)
            raise exceptions.HTTPError(httplib.SERVICE_UNAVAILABLE)
        if response.getcode() != httplib.OK:
            _logger.error('received http response code %s from backend search service' %
                          response.getcode())
            raise exceptions.HTTPError(httplib.BAD_GATEWAY, url)

        return response.read()


# this data structure should be used to return search results in a uniform
# and well-defined way.
class SearchResult(namedtuple('SearchResult', ['name', 'description', 'is_trusted',
                                               'is_official', 'star_count', 'should_filter'])):
    result_defaults = {'is_trusted': False, 'is_official': False, 'star_count': 0,
                       'should_filter': True}
