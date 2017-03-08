from crane.app_util import authorize_repo_id, authorize_name, get_data, get_v2_data


@authorize_repo_id
def get_images_for_repo(repo_id):
    """
    Return the images details json structure for a repository

    :param repo_id: The identifier for the repository
    :type repo_id: basestring
    :returns: json structure of image details
    :rtype: dict
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
    :rtype: dict
    """
    # Validation that the repo exists is taken care of by the decorator
    return get_data()['repos'][repo_id].tags_json


@authorize_name
def get_path_for_repo(repo_id):
    """
    Return the URL for the repository.

    :param repo_id: The identifier/name for the repository
    :type repo_id: basestring
    :returns: URL for the repository
    :rtype: basestring
    """
    return get_v2_data()['repos'][repo_id].url


@authorize_name
def get_schema2_data_for_repo(repo_id):
    """
    Return the schema2 data for the repository.

    :param repo_id: The identifier/name for the repository
    :type repo_id: basestring
    :returns: schema2 data for the repo
    :rtype: list
    """
    repo = get_v2_data()['repos'][repo_id]
    try:
        schema2_data = repo.schema2_data
    except AttributeError:
        schema2_data = None
    return schema2_data
