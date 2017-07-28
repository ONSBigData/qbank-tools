import unittest.mock as mock


def patch(targets):
    """
    Given a list of targets to be patched produces a patch and mock object for each.

    For more info on patches, see http://www.voidspace.org.uk/python/mock/patch.html

    :param targets: e.g. ['functions.get_urls', 'functions.requests.get', 'functions.get']
    :return: 2 dictionaries, one with patches, the other with mocks. Keys are the method_names of the targets, except
    if there are collisions, in which case full target paths are used (in the above example, keys are:
    'get_urls', 'functions.requests.get', 'functions.get')
    """
    patches = {}
    mocks = {}

    method_names = [t.split('.')[-1] for t in targets]

    for target_path in targets:
        key = target_path.split('.')[-1]  # e.g. 'some_module.functions.xpath_searcher' -> 'xpath_searcher' is the key
        if method_names.count(key) > 1:  # if there's a collision, use full path to target
            key = target_path

        patch_object = mock.patch(target_path)
        mock_object = patch_object.start()

        patches[key] = patch_object
        mocks[key] = mock_object

    return patches, mocks


def unpatch(patches):
    """
    Unpatches (stops the mocks) of the given list of patch objects

    For more info on patches, see http://www.voidspace.org.uk/python/mock/patch.html
    """
    for patch_object in patches.values():
        patch_object.stop()

