import os

def create_directories_if_necessary(path):
    """
    Given a path, creates all the directories necessary till the last '/' encountered. E.g.

    if '/path/to/ exists' and path is '/path/to/file/is/this' calling this would create '/path/to/file/is/'
    """

    if '/' not in path:
        return

    dir_path = path[0:path.rfind('/') + 1]

    if os.path.exists(dir_path):
        return

    os.makedirs(dir_path)


def from_root(path, create_if_needed=False):
    """
    Returns path with project root prepended
    """
    proj_root = os.path.realpath(os.path.dirname(__file__)) + '/../'
    result_path = proj_root + path

    if create_if_needed:
        create_directories_if_necessary(result_path)

    return result_path