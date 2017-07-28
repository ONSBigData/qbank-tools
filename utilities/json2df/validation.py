import copy
from helpers.common import *
from utilities.json2df.common import *
import utilities.json2df.traversing as traversing


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


# --- Top level segment -----------------------------------------------------------


def check_and_correct_top_level_segment(root_node, problems=[]):
    if is_top_level_segment_incorrect(root_node):
        problems.append((Problems.IncorrectTlSeg, True))
        root_node = correct_top_level_segment_if_necessary(root_node)

    return root_node


def is_top_level_segment_incorrect(root_node):
    tl_seg = root_node[JK_SEGMENT]

    # top level segment should not be a list - should be an object
    return isinstance(tl_seg, list) and len(tl_seg) > 1


def correct_top_level_segment_if_necessary(root_node):
    root_node = copy.deepcopy(root_node)

    is_survey_seg = lambda o: 'segment_type' in o and o['segment_type'] == 'survey'

    tl_seg = root_node[JK_SEGMENT]

    if is_top_level_segment_incorrect(root_node):
        # find the survey segment in the list - should be just 2 items, but one never knows!
        survey_seg_index, survey_seg_object = [(i, o) for i, o in enumerate(root_node[JK_SEGMENT]) if is_survey_seg(o)][0]

        # delete the survey segment from the top-level segment
        del tl_seg[survey_seg_index]

        # survey seg will contain the TL seg list
        survey_seg_object[JK_SEGMENT] = tl_seg

        # survey seg is the new TL seg
        root_node[JK_SEGMENT] = survey_seg_object

    return root_node


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

    return tc_nodes


def get_invalid_words(traversed_data):
    return filter_invalid_words(traversed_data, return_invalid=True)


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