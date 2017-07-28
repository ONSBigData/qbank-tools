import collections
import copy
import io
import json
import re
import traceback
import helpers.general_helper as gh

import helpers.helper as helper
from helpers.common import *

FIRST_COLS = [
    'uid',
    'survey_id',
    'survey_name',
    'form_type',
    'tr_code',
    'type',
    'period_days',
    'period_start',
    'period_end',
    'text',
    'qtext',
    'closest_text',
    'close_seg_text',
    'all_seg_text',
    'all_text',
    'all_context',
    'all_inclusions',
    'all_exclusions'
]


def is_top_level_segment_incorrect(root_node):
    tl_seg = root_node['segment']

    # top level segment should not be a list - should be an object
    return isinstance(tl_seg, list) and len(tl_seg) > 1


def correct_top_level_segment_if_necessary(root_node):
    root_node = copy.deepcopy(root_node)

    is_survey_seg = lambda o: 'segment_type' in o and o['segment_type'] == 'survey'

    tl_seg = root_node['segment']

    if is_top_level_segment_incorrect(root_node):
        # find the survey segment in the list - should be just 2 items, but one never knows!
        survey_seg_index, survey_seg_object = [(i, o) for i, o in enumerate(root_node['segment']) if is_survey_seg(o)][0]

        # delete the survey segment from the top-level segment
        del tl_seg[survey_seg_index]

        # survey seg will contain the TL seg list
        survey_seg_object['segment'] = tl_seg

        # survey seg is the new TL seg
        root_node['segment'] = survey_seg_object

    return root_node





def path2str(path):
    return '__'.join(str(p) for p in path)


def create_df(traversed_data):
    MINOR_SEP = ' | '
    MAJOR_SEP = ' ||| '
    SEG = 'segment__'

    traversed_data = [tr for tr in traversed_data if 'tracking_code' in tr['path']]

    rows = []
    for tr in traversed_data:
        row = {
            'tr_code': tr['value'],
            'path': path2str(tr['path'])
        }

        # some attributes will be combined - thus the "list" value
        attrs = collections.defaultdict(list)

        # depth of segment nesting
        question_depth = max([path2str(attr['path']).count(SEG) for attr in tr['attrs']])

        # process attributes
        for attr in tr['attrs']:
            path = attr['path']

            if 'survey_scrape_info' in path:  # skip these kind of attributes
                continue

            if 'tracking_code' in path:  # we have that already
                continue

            path = [p for p in path if not isinstance(p, int)]  # remove indices from path, they're not relevant
            key = path2str(path)
            key = key.lower()

            def _append(_key):
                attrs[_key].append(attr['value'])

            if path[-2] == 'question':  # question attributes
                key = 'q_' + path[-1]
                _append(key)
                continue

            if key.startswith(SEG):  # segment attribute
                seg_depth = key.count(SEG)
                key = key.replace(SEG, '')
                _append('s{}_{}'.format(seg_depth - 1, key))
                _append('i{}_{}'.format(question_depth - seg_depth, key))  #i0 will be closest segment to the question
                continue

            _append(key)

        # flatten lists and assign to row
        for key in attrs:
            row[key] = MINOR_SEP.join(attrs[key])

        # now create new attributes --------------------------------------------------------------------------
        def get_all_values_where_keys_like(pattern):
            keys = [key for key in row if re.search(pattern, key)]
            keys.sort()
            return [row[key] for key in keys]

        def get_all_value(field):
            return MAJOR_SEP.join(get_all_values_where_keys_like(r's\d+.*_' + field) + get_all_values_where_keys_like(r'q.*_' + field))

        def_row = collections.defaultdict(lambda: None)
        def_row.update(row)

        row['period_start'] = def_row['s0_reporting_period__start']
        row['period_end'] = def_row['s0_reporting_period__end']
        row['survey_id'] = def_row['s0_survey_number']
        row['form_type'] = def_row['s0_form_type']

        def get_first_nonempty(keys):
            for key in keys:
                if key in row:
                    return row[key]

            return None

        row['type'] = get_first_nonempty(['q_type', 'q_col_type', 'q_row_type'] + ['i{}_type'.format(i) for i in range(9)])

        row['text'] = MINOR_SEP.join(get_all_values_where_keys_like(r'(q|q_row|q_col)_text'))

        closest = row['text']
        if closest == '':
            closest = get_first_nonempty(['i{}_text'.format(i) for i in range(9)])
        row['closest_text'] = closest

        qtext = row['text']
        last = qtext
        for key in ['i{}_text'.format(i) for i in range(9)]:
            last_words = list(filter(None, re.sub('[^0-9a-zA-Z]+', ' ', last).split(' ')))
            if key not in def_row or len(last_words) > 5:
                break
            last = def_row[key]
            if qtext == '':
                qtext = last
                continue
            qtext = '{} ||| {}'.format(last, qtext)
        row['qtext'] = qtext

        # period days
        try:
            row['period_days'] = (pd.to_datetime(row['period_end'], format='%d/%m/%Y') - pd.to_datetime(row['period_start'], format='%d/%m/%Y')).days
        except:
            row['period_days'] = None

        # text for 3 closest segments
        close_segment_texts = reversed(get_all_values_where_keys_like(r'i[0-2].*_text'))
        row['close_seg_text'] = MAJOR_SEP.join(close_segment_texts)

        # all text for segments
        segment_texts = get_all_values_where_keys_like(r's\d+.*_text')
        row['all_seg_text'] = MAJOR_SEP.join(segment_texts)

        # all text
        row['all_text'] = get_all_value('text')
        row['all_context'] = get_all_value('context')
        row['all_inclusions'] = get_all_value('inclusions')
        row['all_exclusions'] = get_all_value('exclusions')

        # unique_id
        row['uid'] = '{}_{}_{}'.format(row['survey_id'], row['form_type'], row['tr_code'])

        rows.append(row)

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]

    if len(df) == 0:
        return df

    df = helper.reorder_cols(df, first_cols=FIRST_COLS)

    df = df.set_index('uid')

    return df


def load_json(json_fpath, problems=[], print_debug=True):
    def _print(s):
        if print_debug:
            print(s)

    _print('opening {}...'.format(json_fpath))
    try:
        with open(json_fpath, encoding='utf8') as f:
            root_node = json.load(f)
    except:
        problems.append((Problems.Encoding, 'encoding is UTF-8-sig'))
        with open(json_fpath, encoding='utf-8-sig') as f:
            root_node = json.load(f)

    if is_top_level_segment_incorrect(root_node):
        _print('correcting top level segment...')
        problems.append((Problems.IncorrectTlSeg, True))
        root_node = correct_top_level_segment_if_necessary(root_node)

    _print('exploding matrix questions...')
    root_node = explode_all_matrices(root_node, problems=problems)
    json.dump(root_node, open(DATA_DIR + '/jsons-exploded/' + os.path.basename(json_fpath), 'w'))

    _print('traversing...')
    traversed = traverse(root_node)

    _print('validating...')
    invalid = get_invalid_words(traversed)
    if len(invalid) > 0:
        if print_debug:
            print_invalid_words(invalid)
        problems.append((Problems.InvalidWords, invalid))
    traversed = filter_invalid(traversed)

    _print('creating dataframe...')
    df = create_df(traversed)
    if len(df) == 0:
        problems.append((Problems.NoData, True))
    elif df['period_days'].count() == 0:
        _print('missing reporting period...')
        problems.append((Problems.ReportingPeriod, True))

    _print('adding survey names')
    mp = get_survey_name_map()
    df['survey_name'] = df['survey_id'].apply(lambda x: mp[int(x)])

    _print('dataframe with shape {} created'.format(df.shape))

    return df




def create_full_df(print_debug=True):
    def _print(s=''):
        if print_debug:
            print(s)

    SEP_LEN = 100

    all_invalid_words = set()
    dfs = []

    for i, json_fpath in enumerate(get_all_jsons()):
        _print()
        _print('{}.) {}'.format(i, '-' * SEP_LEN))

        try:
            problems = []
            df = load_json(json_fpath, problems, print_debug=print_debug)
        except json.JSONDecodeError as e:
            _print('ERROR: {}'.format(e))
            continue
        except Exception as e:
            _print('ERROR: {}'.format(e))
            continue

        invalid_words = next((p[1] for p in problems if p[0] == Problems.InvalidWords), [])
        all_invalid_words = all_invalid_words.union(invalid_words)

        csv_fpath = json_fpath.replace('/jsons/', '/csvs/').replace('.json', '.csv')
        _print('dataframe saved to: {}'.format(csv_fpath))
        df.to_csv(csv_fpath, index=True)

        if len(problems) != 0:
            _print('PROBLEMS: {}'.format(', '.join([p[0] for p in problems])))

        dfs.append(df)

    _print('=' * SEP_LEN)
    _print('combining dataframes...')
    cdf = pd.concat(dfs)
    if print_debug:
        print_invalid_words(all_invalid_words)

    cdf = cdf.reset_index()
    cdf['uuid'] = gh.uniquify(cdf, 'uid')
    cdf = cdf.set_index('uuid')

    _print('shape of final dataframe: {}'.format(cdf.shape))

    cdf = helper.reorder_cols(cdf, first_cols=FIRST_COLS)

    cdf.to_csv(CLEAN_FULL_FPATH, index=True)
    cdf[FIRST_COLS].to_csv(CLEAN_LIGHT_FPATH, index=True)

    return cdf


if __name__ == '__main__':
    create_full_df()

