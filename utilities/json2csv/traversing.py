import copy
import traceback
from utilities.json2csv.common import *
from helpers.common import *


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

if __name__ == '__main__':
    import pprint

    fpath = get_json_fpaths()[0]
    node = get_json_root(fpath)
    tc_nodes = traverse(node)

    print(fpath)
    pprint.pprint(tc_nodes, indent=4, width=200)

