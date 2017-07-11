import helpers.helper as helper
from common import *

import copy
import collections
import re


VALID_PATH_WORDS = [
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


def get_children_iterator(node):
    if isinstance(node, dict):
        return node.items()

    if isinstance(node, list):
        return enumerate(node)

    return None


def is_leaf(node):
    return get_children_iterator(node) is None


def explode_matrix(matrix_node):
    rows = dict((row['row_index'], row) for row in matrix_node['rows'])
    cols = dict((col['col_index'], col) for col in matrix_node['cols'])

    cells = matrix_node['cells']

    for cell in cells:
        row = rows[cell['row_index']]
        col = cols[cell['col_index']]

        for k, v in row.items():
            if k != 'row_index':
                cell['row_' + k] = v

        for k, v in col.items():
            if k != 'col_index':
                cell['col_' + k] = v

    return cells


def explode_all_matrices(nd):
    nd = copy.deepcopy(nd)

    def _explode_all_matrices(node, node_key=None, parent_node=None):
        if is_leaf(node):
            return

        if isinstance(node, dict) and 'cells' in node:  # it's a matrix node
            exploded_items = explode_matrix(node)
            parent_node[node_key] = exploded_items
            return

        children_iterator = get_children_iterator(node)

        for key, child_node in children_iterator:
            _explode_all_matrices(child_node, key, node)

    _explode_all_matrices(nd)
    return nd


def is_traversable(key):
    return isinstance(key, int) or key in ['segment', 'question']


def get_node_attrs(node, path_prefix=[]):
    children_iterator = get_children_iterator(node)

    attrs = []
    for key, child_node in children_iterator:
        if is_leaf(child_node):
            attrs.append({
                'path': path_prefix + [key],
                'value': child_node
            })

        elif not is_traversable(key):
            child_attrs = get_node_attrs(child_node, path_prefix + [key])
            attrs.extend(child_attrs)

    return attrs


def path2str(path):
    return '__'.join(str(p) for p in path)


def traverse(node):
    return list(traverse_generator(node))


def traverse_generator(node, path_prefix=[], parent_recursive_attrs=[]):
    if is_leaf(node):
        yield {
            'path': path_prefix,
            'value': node,
            'attrs': parent_recursive_attrs
        }
        return

    if path_prefix != [] and not is_traversable(path_prefix[-1]):
        return

    node_attrs = get_node_attrs(node, path_prefix)

    children_iterator = get_children_iterator(node)

    for key, child_node in children_iterator:
        yield from traverse_generator(
            child_node,
            path_prefix=list(path_prefix) + [key],
            parent_recursive_attrs=parent_recursive_attrs + node_attrs
        )


def path_word_valid(path_word):
    return isinstance(path_word, int) or path_word in VALID_PATH_WORDS


def path_valid(path):
    return all(path_word_valid(p) for p in path)


def filter_invalid(traversed_data, return_invalid=False):
    invalid = set()

    def fix_path(path):
        for i, w in enumerate(path):
            if path_word_valid(w):
                continue

            invalid.add(w)

            if 'includ' in w:
                w = 'inclusions'
            if 'exclud' in w:
                w = 'exclusions'

            if w == 'finish':
                w = 'end'

            if not path_word_valid(w):
                return False

            path[i] = w

        return True

    traversed_data = copy.deepcopy(traversed_data)
    filtered = []
    for tr in traversed_data:
        if not fix_path(tr['path']):
            continue

        tr['attrs'] = [a for a in tr['attrs'] if fix_path(a['path'])]

        filtered.append(tr)

    if return_invalid:
        return invalid

    return traversed_data


def get_invalid_words(traversed_data):
    return filter_invalid(traversed_data, return_invalid=True)


def print_invalid_words(invalid_words):
    print('found {} invalid words'.format(len(invalid_words)))
    if len(invalid_words) != 0:
        print('\t' + '\n\t'.join(invalid_words))


def create_df(traversed_data):
    MINOR_SEP = ' | '
    MAJOR_SEP = ' ||| '

    traversed_data = [tr for tr in traversed_data if 'tracking_code' in tr['path']]

    rows = []
    for tr in traversed_data:
        row = {
            'tr_code': tr['value'],
            'path': path2str(tr['path'])
        }

        # some attributes will be combined - thus the "list" value
        attrs = collections.defaultdict(list)

        # process attributes
        for attr in tr['attrs']:
            path = attr['path']

            if 'survey_scrape_info' in path:  # skip these kind of attributes
                continue

            if 'tracking_code' in path:  # we have that already
                continue

            path = [p for p in path if not isinstance(p, int)]  # remove indices from path, they're not relevant
            key = path2str(path)

            if path[-2] == 'question':  # question attributes
                key = 'q_' + path[-1]

            SEG = 'segment__'
            if key.startswith(SEG):
                counter = 0
                while key.startswith(SEG):
                    counter += 1
                    key = key.replace(SEG, '', 1)
                key = 's{}_{}'.format(counter, key)

            key = key.replace('s1_reporting_period', 'period') \
                .replace('s1_survey_number', 'survey_id') \
                .replace('s1_form_type', 'form_type') \
                .replace('period__', 'period_')

            attrs[key].append(attr['value'])

        # flatten lists
        for key in attrs:
            attrs[key] = MINOR_SEP.join(attrs[key])

        def get_all_seg_values_where_keys_like(pattern):
            seg_keys = [key for key in attrs if re.search(pattern, key)]
            seg_keys.sort()
            return [attrs[key] for key in seg_keys]

        # create new attributes

        # period days
        try:
            row['period_days'] = (pd.to_datetime(attrs['period_end'], format='%d/%m/%Y') - pd.to_datetime(attrs['period_start'], format='%d/%m/%Y')).days
        except:
            row['period_days'] = None

        # all text for segments
        segment_texts = get_all_seg_values_where_keys_like(r's\d+.*_text')
        row['all_seg_text'] = MAJOR_SEP.join(segment_texts)

        # all text
        all_texts = list(segment_texts)
        if 'q_text' in attrs:
            all_texts.append(attrs['q_text'])
        row['all_text'] = MAJOR_SEP.join(all_texts)

        # all context
        all_contexts = get_all_seg_values_where_keys_like(r's\d+.*_context')
        if 'q_context' in attrs:
            all_contexts.append(attrs['q_context'])
        row['all_context'] = MAJOR_SEP.join(all_contexts)

        # unique_id
        row['uid'] = '{}_{}_{}'.format(attrs['survey_id'], attrs['form_type'], row['tr_code'])

        row.update(attrs)
        rows.append(row)

    df = pd.DataFrame(rows)
    df.columns = [c.lower() for c in df.columns]

    df = helper.reorder_cols(df, first_cols=['survey_id', 'form_type', 'tr_code'])

    df = df.set_index('uid')

    return df


if __name__ == '__main__':
    pass