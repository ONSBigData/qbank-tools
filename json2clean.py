from functools import reduce
import operator
import os
import copy
from sys import argv
import csv
import json
from os.path import basename
import sys
import copy
from common import *


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


def get_node_info(node, path_prefix=[]):
    children_iterator = get_children_iterator(node)

    info = []
    for key, child_node in children_iterator:
        if is_leaf(child_node):
            info.append({
                'path': path_prefix + [key],
                'value': child_node
            })

        elif not is_traversable(key):
            child_info = get_node_info(child_node, path_prefix + [key])
            info.extend(child_info)

    return info


def path2str(path):
    return '__'.join(str(p) for p in path)


def traverse(node):
    return list(traverse_generator(node))


def traverse_generator(node, path_prefix=[], parent_recursive_info=[]):
    if is_leaf(node):
        yield {
            'path': path_prefix,
            'value': node,
            'info': parent_recursive_info
        }
        return

    if path_prefix != [] and not is_traversable(path_prefix[-1]):
        return

    node_info = get_node_info(node, path_prefix)

    children_iterator = get_children_iterator(node)

    for key, child_node in children_iterator:
        yield from traverse_generator(
            child_node,
            path_prefix=list(path_prefix) + [key],
            parent_recursive_info=parent_recursive_info + node_info
        )


def create_df(traversed_data):
    traversed_data = [tr for tr in traversed_data if 'tracking_code' in tr['path']]

    rows = []
    for tr in traversed_data:
        row = {
            'tracking_code': tr['value'],
            'path': tr['path']
        }

        for info in tr['info']:
            row[path2str(info['path'])] = info['value']

        rows.append(row)

    return pd.DataFrame(rows)


def f():
    return 7

if __name__ == '__main__':
    pass