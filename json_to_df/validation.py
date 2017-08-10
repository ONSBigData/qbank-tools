import copy

import json_to_df.traversing as traversing

from support.common import *
from json_to_df.common import *

VALID_PATH_WORDS = [
    'Affiliate Company',
    'Branch',
    'col_count',
    'context',
    'destination',
    'download_date',
    'end',
    'exclusions',
    'file_name',
    'folder_name',
    'form_type',
    'question',
    'inclusions',
    'ID',
    'note',
    'note_ID',
    'note_id',
    'NULL',
    'options',
    'reporting_period',
    'row_count',
    'routing',
    'scrape_date',
    'segment',
    'segment_type',
    'start',
    'survey_number',
    'survey_scrape_info',
    'text',
    'tracking_code',
    'type',
    'validation',
    'value'
]

MATRIX_VALID_WORDS = [
    'context',
    'exclusions',
    'ID',
    'index',
    'inclusions',
    'note_ID',
    'NULL',
    'text',
    'type',
    'validation'
]

VALID_PATH_WORDS += ['row_' + w for w in MATRIX_VALID_WORDS]
VALID_PATH_WORDS += ['col_' + w for w in MATRIX_VALID_WORDS]


# --- invalid words in path -----------------------------------------------------------


def path_word_valid(path_word):
    return isinstance(path_word, int) or path_word in VALID_PATH_WORDS


def path_valid(path):
    return all(path_word_valid(p) for p in path)


def filter_invalid_words(tc_nodes, return_invalid=False, problems=[]):
    invalid_words = set()

    def _fix_path(path):
        for i, w in enumerate(path):
            if path_word_valid(w):
                continue

            invalid_words.add(w)

            if 'inclu' in w:
                w = 'inclusions'
            if 'exclu' in w:
                w = 'exclusions'

            if w == 'finish':
                w = 'end'

            if not path_word_valid(w):
                return False

            path[i] = w

        return True

    tc_nodes = copy.deepcopy(tc_nodes)
    filtered = []
    for tc_node in tc_nodes:
        if not _fix_path(tc_node[PATH]):
            continue

        tc_node[ATTRS] = [attr for attr in tc_node[ATTRS] if _fix_path(attr[PATH])]

        filtered.append(tc_node)

    problems.append((Problems.InvalidWords, invalid_words))

    if return_invalid:
        return invalid_words

    return filtered


def get_invalid_words(tc_nodes):
    return filter_invalid_words(tc_nodes, return_invalid=True)


def print_invalid_words(invalid_words):
    print('found {} invalid words'.format(len(invalid_words)))
    if len(invalid_words) != 0:
        print('\t' + '\n\t'.join(invalid_words))


def print_problems(problems):
    for p in problems:
        print('{}: {}'.format(p[0], p[1]))


if __name__ == '__main__':
    fpath = get_json_fpaths()[1]
    node = get_json_root(fpath)
    tc_nodes = traversing.traverse(node)

    problems = []
    filter_invalid_words(tc_nodes, problems=problems)
    print_problems(problems)