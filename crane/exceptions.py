class HTTPError(Exception):
    def __init__(self, status_code, message=''):
        """
        Raise this exception to return an http response indicating an error.

        :param status_code: HTTP status code. It's a good idea to get this straight
                            from httplib, such as httplib.NOT_FOUND
        :type  status_code: int
        :param message:     optional error message to be put in the response
                            body. If not supplied, the default message for the
                            status code will be used.
        """
        super(HTTPError, self).__init__()
        self.message = message
        self.status_code = status_code
