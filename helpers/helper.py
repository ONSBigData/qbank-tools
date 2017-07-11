import os


def reorder_cols(df, first_cols):
    def sort_function(c):
        if c in first_cols:
            return first_cols.index(c)
        return len(first_cols) + 1

    cols = list(df.columns)
    cols.sort(key=sort_function)
    return df[cols]


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