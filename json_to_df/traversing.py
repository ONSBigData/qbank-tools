import copy
import traceback

from support.common import *
from json_to_df.common import *


# ---------------------------------------------------------------------
# --- general traversing
# ---------------------------------------------------------------------


def get_children_iterator(node):
    if isinstance(node, dict):
        return node.items()

    if isinstance(node, list):
        return enumerate(node)

    return None


def is_leaf(node):
    """
    Returns true if node has no more children
    """
    return get_children_iterator(node) is None


# ---------------------------------------------------------------------
# --- main segment traversing
# ---------------------------------------------------------------------


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


def should_be_traversed(key):
    """
    Only arrays and nodes with segment and question keys should be traversed
    """
    return isinstance(key, int) or key in ['segment', 'question']


def traverse(node):
    return list(traverse_generator(node))


def traverse_generator(node, path_prefix=[], parent_recursive_attrs=[]):
    """
    Recursively traverses the structure under the specified node, outputing tracking code nodes.

    The output contains path to the node, value (tracking code value) and a list of all attributes for all nodes along the
    way from the root. E.g. if the path to the tracking code looks like this

    'path': ['segment', 'question', 1, 'tr_code']

    there will be a list containing all attributes for all of these nodes:
        []
        ['segment']
        ['segment', 'question']
        ['segment', 'question', 1]
    """
    node_attrs = get_node_attrs(node, path_prefix)

    for key, child_node in get_children_iterator(node):
        if key == 'notes':  #skip notes here - we traverse them separately
            continue

        if should_be_traversed(key):
            yield from traverse_generator(
                child_node,
                path_prefix=path_prefix + [key],
                parent_recursive_attrs=parent_recursive_attrs + node_attrs
            )
        elif key == 'tracking_code':
            yield {
                PATH: path_prefix + [key],
                VALUE: child_node,
                ATTRS: parent_recursive_attrs + node_attrs
            }


def get_node_attrs(node, path_prefix=[]):
    """
    Gets all attributes for specified node - i.e. all attributes that "belong" to this node, as they wouldn't otherwise
    be traversed.

    node: {                         # our node
        "question": ...,            # this will be traversed - so it's NOT part of node's attrs
        "segment": ...,             # same here
        "inclusions": [             # this, however, won't be traversed - so it's part of our node's attrs
            'xyz',
            'abc'
        ],
        "options": {                # same here - this node and its children are part of our node's attrs
            "note_ID": 'efg'
        }
    }
    """
    children_iterator = get_children_iterator(node)

    attrs = []
    for key, child_node in children_iterator:
        if key == 'notes':  #skip notes here - we traverse them separately
            continue

        if is_leaf(child_node):
            attrs.append({
                PATH: path_prefix + [key],
                VALUE: child_node
            })

        elif not should_be_traversed(key):
            child_attrs = get_node_attrs(child_node, path_prefix + [key])
            attrs.extend(child_attrs)

    return attrs


# ---------------------------------------------------------------------
# --- main segment traversing
# ---------------------------------------------------------------------


def explode_matrix(matrix_node, problems=[]):
    def check_field(kw):
        if isinstance(matrix_node[kw], dict):
            err_msg = '{} field for matrix node below is a dictionary (should be list)\n{}'.format(kw, json.dumps(matrix_node, indent=2))
            problems.append((Problems.MatrixParsing, err_msg))

            matrix_node[kw] = [matrix_node[kw]]

    root_node_attrs = copy.deepcopy(matrix_node)
    del root_node_attrs['cols']
    del root_node_attrs['rows']
    del root_node_attrs['cells']

    check_field('cols')
    check_field('rows')
    check_field('cells')

    rows = dict((row['row_index'], row) for row in matrix_node['rows'])
    cols = dict((col['col_index'], col) for col in matrix_node['cols'])

    cells = matrix_node['cells']

    for cell in cells:
        cell.update(root_node_attrs)
        row = rows[cell['row_index']]
        col = cols[cell['col_index']]

        for k, v in row.items():
            if k != 'row_index':
                cell['row_' + k] = v

        for k, v in col.items():
            if k != 'col_index':
                cell['col_' + k] = v

    return cells


def explode_all_matrices(nd, problems=[]):
    nd = copy.deepcopy(nd)

    def _explode_all_matrices(node, node_key=None, parent_node=None):
        if is_leaf(node):
            return

        if isinstance(node, dict) and 'cells' in node:  # it's a matrix node
            try:
                exploded_items = explode_matrix(node, problems=problems)
                parent_node[node_key] = exploded_items
            except Exception as e:
                parent_node[node_key] = {}
                problems.append((Problems.MatrixParsing, 'Exception occured parsing matrix node below: {}\n{}\n{}'.format(
                    e, traceback.format_exc(), json.dumps(node, indent=2))))

            return

        children_iterator = get_children_iterator(node)

        for key, child_node in children_iterator:
            _explode_all_matrices(child_node, key, node)

    _explode_all_matrices(nd)

    return nd


# ---------------------------------------------------------------------
# --- notes traversing
# ---------------------------------------------------------------------


def get_note_attrs(note_node):
    attrs = []

    def _collect_attrs(node, path_prefix):
        children_iterator = get_children_iterator(node)

        for key, child_node in children_iterator:
            if is_leaf(child_node):
                attrs.append({
                    PATH: path_prefix + [key],
                    VALUE: child_node
                })
            else:
                _collect_attrs(child_node, path_prefix + [key])


    _collect_attrs(note_node, [])

    return attrs


def traverse_notes(node):
    return list(traverse_notes_generator(node))


def traverse_notes_generator(node):
    if isinstance(node, dict):
        children = dict((key.lower(), val) for key, val in get_children_iterator(node))
        if 'id' in children or 'note_id' in children:
            note_id = children['note_id'] if 'note_id' in children else children['id']
            attrs = get_note_attrs(node)

            yield {
                NOTE_ID: note_id,
                ATTRS: attrs
            }
            return

    for key, child_node in get_children_iterator(node):
        yield from traverse_notes_generator(child_node)


def get_note_nodes(json_fpath):
    root_node = get_json_root(json_fpath)

    if 'notes' in root_node:
        return traverse_notes(root_node['notes'])

    return []


# ---------------------------------------------------------------------
# --- others
# ---------------------------------------------------------------------


def get_tc_nodes(json_fpath, problems=[]):
    """
    Convenience function, bundling together code to get Tr. code nodes
    """
    root_node = get_json_root(json_fpath, problems=problems)
    root_node = check_and_correct_top_level_segment(root_node, problems=problems)
    root_node = explode_all_matrices(root_node, problems=problems)

    tc_nodes = traverse(root_node)

    return tc_nodes


if __name__ == '__main__':
    import pprint

    fpath = get_json_fpath('ex_sel120-ft0001_JS_170510')

    # nodes = get_note_nodes(fpath)
    nodes = get_tc_nodes(fpath)

    print(fpath)
    pprint.pprint(nodes, indent=4, width=200)

