
class NotFoundException(Exception):
    """
    Generic exception to be used whenever a resource can not be found.  Mostly
    for proper communication with Flask
    """
    pass


class AuthorizationFailed(Exception):
    """
    Generic exception to be used whenever authorization fails.  Mostly
    for proper communication with Flask
    """
    pass
