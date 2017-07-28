import re
from utilities.json2df.common import *
from helpers.common import *

MINOR_SEP = ' | '
MAJOR_SEP = ' ||| '


def path2str(path):
    return '__'.join(str(p) for p in path)


def extract_useful_attrs(tc_node):
    question_seg_depth = tc_node['path'].count(JK_SEGMENT)

    useful_attrs = collections.defaultdict(list)

    for attr in tc_node[ATTRS]:
        def _append(_key):
            useful_attrs[_key].append(attr[VALUE])

        path = attr[PATH]
        path = [p for p in path if not isinstance(p, int)]  # filter out array indices from path - they're not relevant
        path = [p.lower() for p in path]  # make everything lower case

        if JK_TR_CODE in path:  # we have that already
            continue

        if JK_SCRAPE_INFO in path:
            rest_of_path = path[path.index(JK_SCRAPE_INFO) + 1:]
            _append('sci_' + path2str(rest_of_path))

        if JK_QUESTION in path:
            rest_of_path = path[path.index(JK_QUESTION) + 1:]
            _append('q_' + path2str(rest_of_path))
            continue

        if JK_SEGMENT in path:
            seg_depth = path.count(JK_SEGMENT)

            last_seg = len(path) - path[::-1].index(JK_SEGMENT) - 1
            rest_of_path = path[last_seg + 1:]
            key = path2str(rest_of_path)

            _append('s{}_{}'.format(seg_depth - 1, key))  # s0 will be the root segment
            _append('i{}_{}'.format(question_seg_depth - seg_depth, key))  # i0 will be closest segment to the question
            continue

    # combine values for the same key
    result = dict((key, MINOR_SEP.join(useful_attrs[key])) for key in useful_attrs)

    return result


def create_new_attrs(row):
    def_row = collections.defaultdict(lambda: None)  # we will use this to avoid "if key not in row..."
    def_row.update(row)

    new_attrs = {}

    def _get_all_values_where_keys_like(pattern):
        keys = [key for key in row if re.search(pattern, key)]
        keys.sort()
        return [row[key] for key in keys]

    def _get_all_value(field):
        return MAJOR_SEP.join(
            _get_all_values_where_keys_like(r's\d+.*_' + field) +
            _get_all_values_where_keys_like(r'q.*_' + field)
        )

    def _get_first_nonempty(keys):
        for key in keys:
            if key in row:
                return row[key]

        return None

    # these are basically just renames for convenience
    new_attrs['period_start'] = def_row['s0_reporting_period__start']
    new_attrs['period_end'] = def_row['s0_reporting_period__end']
    new_attrs['survey_id'] = def_row['s0_survey_number']
    new_attrs['form_type'] = def_row['s0_form_type']

    # the question type might be further up the json
    new_attrs['type'] = _get_first_nonempty(['q_type', 'q_col_type', 'q_row_type'] + ['i{}_type'.format(i) for i in range(9)])

    # text associated right with the question node
    new_attrs['qtext'] = MINOR_SEP.join(_get_all_values_where_keys_like(r'(q|q_row|q_col)_text'))

    # first non empty text (going from leaf to root)
    first_text = new_attrs['qtext']
    if first_text == '':
        first_text = _get_first_nonempty(['i{}_text'.format(i) for i in range(9)])
    new_attrs['first_text'] = first_text

    # long enough/sufficient question text
    texts = list(filter(None, [new_attrs['qtext']] + _get_all_values_where_keys_like(r'i\d+.*_text')))
    sufficient_qtext = []
    for text in texts:
        sufficient_qtext.append(text)

        text_words = list(filter(None, re.sub('[^0-9a-zA-Z]+', ' ', text).split(' ')))
        if len(text_words) > 5:  # break when the last text contained sufficient amount of words
            break
    new_attrs['suff_qtext'] = MAJOR_SEP.join(reversed(sufficient_qtext))

    # construct period days
    try:
        new_attrs['period_days'] = (
            pd.to_datetime(new_attrs['period_end'], format='%d/%m/%Y') -
            pd.to_datetime(new_attrs['period_start'], format='%d/%m/%Y')
        ).days
    except:
        new_attrs['period_days'] = None

    # text for 3 closest segments
    close_segment_texts = reversed(_get_all_values_where_keys_like(r'i\d+.*_text')[:3])
    new_attrs['close_seg_text'] = MAJOR_SEP.join(close_segment_texts)

    # all text for segments
    segment_texts = _get_all_values_where_keys_like(r's\d+.*_text')
    new_attrs['all_seg_text'] = MAJOR_SEP.join(segment_texts)

    # values for all text, all context ...
    new_attrs['all_text'] = _get_all_value('text')
    new_attrs['all_context'] = _get_all_value('context')
    new_attrs['all_inclusions'] = _get_all_value('inclusions')
    new_attrs['all_exclusions'] = _get_all_value('exclusions')

    # unique id (this is actually not unique, due to scraping errors, but should be)
    new_attrs['uid'] = '{}_{}_{}'.format(new_attrs['survey_id'], new_attrs['form_type'], row['tr_code'])

    return new_attrs


def create_row(tc_node):
    if tc_node[VALUE] =='5901':
        x = 1

    row = {
        'tr_code': tc_node[VALUE],
        'path': path2str(tc_node[PATH])
    }

    useful_attrs = extract_useful_attrs(tc_node)
    row.update(useful_attrs)

    new_attrs = create_new_attrs(row)
    row.update(new_attrs)

    return row


def create_df(tc_nodes, problems=[]):
    rows = [create_row(tc_node) for tc_node in tc_nodes]

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]

    if len(df) == 0:
        problems.append((Problems.NoData, True))
        return df

    if df['period_days'].count() == 0:
        problems.append((Problems.ReportingPeriod, True))

    if df['form_type'].count() == 0:
        problems.append((Problems.FormType, True))

    df = gh.reorder_cols(df, FIRST_COLS)

    mp = get_survey_name_map()
    df['survey_name'] = df['survey_id'].apply(lambda x: mp[int(x)])

    df = df.set_index('uid')

    return df


if __name__ == '__main__':
    import utilities.json2df.traversing as traversing
    import pandas as pd

    pd.set_option('max_colwidth', 1800)

    fpath = get_json_fpath('ex_sel108-ft0002')
    tc_nodes = traversing.get_tc_nodes(fpath)
    df = create_df(tc_nodes)

    print(df)
    print(df.columns)
