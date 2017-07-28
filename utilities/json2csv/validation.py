import copy
from helpers.common import *
from utilities.json2csv.common import *
import io


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


def path_word_valid(path_word):
    return isinstance(path_word, int) or path_word in VALID_PATH_WORDS


def path_valid(path):
    return all(path_word_valid(p) for p in path)


def filter_invalid(tc_nodes, return_invalid=False, problems=[]):
    invalid = set()

    def fix_path(path):
        for i, w in enumerate(path):
            if path_word_valid(w):
                continue

            invalid.add(w)

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
    for tr in tc_nodes:
        if not fix_path(tr['path']):
            continue

        tr['attrs'] = [a for a in tr['attrs'] if fix_path(a['path'])]

        filtered.append(tr)

    if return_invalid:
        return invalid

    return tc_nodes


def get_invalid_words(traversed_data):
    return filter_invalid(traversed_data, return_invalid=True)


def print_invalid_words(invalid_words):
    print('found {} invalid words'.format(len(invalid_words)))
    if len(invalid_words) != 0:
        print('\t' + '\n\t'.join(invalid_words))


def get_invalid_words_report(json_fpaths=get_json_fpaths()):
    stream = io.StringIO()

    for json_fpath in json_fpaths:
        try:
            problems = []
            load_json(json_fpath, problems, print_debug=False)
        except:
            continue

        invalid_words = next((p[1] for p in problems if p[0] == Problems.InvalidWords), [])
        if invalid_words == []:
            continue

        stream.write(os.path.basename(json_fpath) + '\n')
        stream.write('\t' + '\n\t'.join(invalid_words) + '\n')
        stream.write('\n')

    s = stream.getvalue()

    with open(PROBLEM_REPORTS_DIR + '/invalid_words_report.txt', 'w') as f:
        f.write(s)

    return s


def get_problems_report(json_fpaths=get_json_fpaths()):
    stream = io.StringIO()

    for json_fpath in json_fpaths:
        stream.write('\n')
        stream.write('-'*100 + '\n')
        stream.write(os.path.basename(json_fpath) + '\n')

        try:
            problems = []
            load_json(json_fpath, problems, print_debug=False)
        except Exception as e:
            stream.write('ERROR: {}'.format(e)+ '\n')
            continue

        for p in problems:
            stream.write('{}: {}'.format(p[0], p[1])+ '\n')

        if len(problems) == 0:
            stream.write('OK\n')

    s = stream.getvalue()

    with open(PROBLEM_REPORTS_DIR + '/problems_report.txt', 'w') as f:
        f.write(s)

    return s


def print_problems(problems):
    for p in problems:
        print('{}: {}'.format(p[0], p[1]))


if __name__ == '__main__':
    get_problems_report()
    get_invalid_words_report()