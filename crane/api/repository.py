from crane.app_util import authorize_repo_id, get_data


@authorize_repo_id
def get_images_for_repo(repo_id):
    """
    Return the images details json structure for a repository

    :param repo_id: The identifier for the repository
    :type repo_id: basestring
    :returns: json structure of image details
    """
    # Validation that the repo exists is taken care of by the decorator
    return get_data()['repos'][repo_id].images_json


@authorize_repo_id
def get_tags_for_repo(repo_id):
    """
    Return the tag details for a repository

    :param repo_id: The identifier for the repository
    :type repo_id: basestring
    :returns: json structure of repo tags
    """
    # Validation that the repo exists is taken care of by the decorator
    return get_data()['repos'][repo_id].tags_json
