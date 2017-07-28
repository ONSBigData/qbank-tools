import json

import nose.tools as nstools
import tests.helpers.patch_helper as patch_helper

from utilities.json2csv import traversing

# ---------------------------------------------------------------------
# --- general traversing
# ---------------------------------------------------------------------


NODE = {
    'question': {
        'text': 'qtext1',
        'tr_code': 'tr1',
        'inclusions': [
            'i1', 'i2'
        ]
    },
    'segment': {
        'text': 'segtext',
        'question': [
            {
                'text': 'qtext2',
                'tr_code': 'tr2',
                'context': 'context1'
            },
            {
                'text': 'qtext3',
                'tr_code': 'tr3',
                'context': 'context2'
            },
        ]
    },
    'text': 'efg',
    'inclusions': ['i3', 'i4'],
    'options': {
        'opt1': {
            'subopt1': 'value'
        },
        'array': [1, 2]
    }
}


class TestTraverse:
    EXPECTED = [
        {
            'value': 'tr1',
            'attrs': ['attrs-[]', "attrs-['question']"],
            'path': ['question', 'tr_code']
        },
        {
            'value': 'tr2',
            'attrs': ['attrs-[]', "attrs-['segment']", "attrs-['segment', 'question']", "attrs-['segment', 'question', 0]"],
            'path': ['segment', 'question', 0, 'tr_code']
        },
        {
            'value': 'tr3',
            'attrs': ['attrs-[]', "attrs-['segment']", "attrs-['segment', 'question']","attrs-['segment', 'question', 1]"],
            'path': ['segment', 'question', 1, 'tr_code']
        }
    ]

    def setup(self):
        self.patches, self.mocks = patch_helper.patch(['utilities.json2csv.traversing.get_node_attrs'])

    def teardown(self):
        patch_helper.unpatch(self.patches)

    def test_traverses_correctly(self):
        def get_node_attrs(node, path_prefix):
            return ['attrs-{}'.format(path_prefix)]
        self.mocks['get_node_attrs'].side_effect = get_node_attrs

        actual = traversing.traverse(NODE)

        # order does not matter
        actual.sort(key=lambda x: str(x['value']))
        self.EXPECTED.sort(key=lambda x: str(x['value']))

        nstools.assert_list_equal(actual, self.EXPECTED)


class TestGetNodeAttrs:
    def test_gets_node_attrs_correctly(self):
        actual = traversing.get_node_attrs(NODE, ['pref'])
        expected = [
            {'value': 'efg', 'path': ['pref', 'text']},
            {'value': 'i3', 'path': ['pref', 'inclusions', 0]},
            {'value': 'i4', 'path': ['pref', 'inclusions', 1]},
            {'value': 'value', 'path': ['pref', 'options', 'opt1', 'subopt1']},
            {'value': 1, 'path': ['pref', 'options', 'array', 0]},
            {'value': 2, 'path': ['pref', 'options', 'array', 1]},
        ]

        # order does not matter
        actual.sort(key=lambda x: str(x['value']))
        expected.sort(key=lambda x: str(x['value']))

        nstools.assert_list_equal(actual, expected)


# ---------------------------------------------------------------------
# --- main segment traversing
# ---------------------------------------------------------------------


SMALL_MATRIX_Q = json.JSONDecoder().decode("""{
  "row_count": "1",
  "col_count": "1",
  "rows": [
    {
      "ID": "a",
      "text": "Banks and building societies?",
      "row_index": "1"
    }
  ],
  "cols": [
    {
      "text": "Acquisitions of assets at cost",
      "col_index": "1",
      "type": "pound_hunthousands"
    }
  ],
  "cells": [
    {
      "row_index": "1",
      "col_index": "1",
      "tracking_code": "3218"
    }
  ]
}""")

SMALL_MATRIX_Q_EXPLODED = json.JSONDecoder().decode("""[
  {
    "row_index": "1",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3218",
    "row_text": "Banks and building societies?",
    "row_count": "1",
    "col_count": "1"
  }
]""")

BIG_MATRIX_Q = json.JSONDecoder().decode("""{
  "row_count": "2",
  "col_count": "2",
  "rows": [
    {
      "ID": "a",
      "text": "Banks and building societies?",
      "row_index": "1"
    },
    {
      "ID": "b",
      "text": "Other UK corporates?",
      "row_index": "2"
    }
  ],
  "cols": [
    {
      "text": "Acquisitions of assets at cost",
      "col_index": "1",
      "context": "Millions of £",
      "type": "pound_hunthousands"
    },
    {
      "text": "Disposals of assets",
      "col_index": "2",
      "context": "Millions of £",
      "type": "pound_hunthousands"
    }
  ],
  "cells": [
    {
      "row_index": "1",
      "col_index": "1",
      "tracking_code": "3218"
    },
    {
      "row_index": "1",
      "col_index": "2",
      "tracking_code": "3219"
    },
    {
      "row_index": "2",
      "col_index": "1",
      "tracking_code": "3040"
    },
    {
      "row_index": "2",
      "col_index": "2",
      "tracking_code": "3041"
    }
  ]
}""")

BIG_MATRIX_Q_EXPLODED = json.JSONDecoder().decode("""[
  {
    "row_index": "1",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3218",
    "row_text": "Banks and building societies?",
    "row_count": "2",
    "col_count": "2"
  },
  {
    "row_index": "1",
    "col_text": "Disposals of assets",
    "col_index": "2",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3219",
    "row_text": "Banks and building societies?",
    "row_count": "2",
    "col_count": "2"
  },
  {
    "row_index": "2",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "b",
    "tracking_code": "3040",
    "row_text": "Other UK corporates?",
    "row_count": "2",
    "col_count": "2"
  },
  {
    "row_index": "2",
    "col_text": "Disposals of assets",
    "col_index": "2",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "b",
    "tracking_code": "3041",
    "row_text": "Other UK corporates?",
    "row_count": "2",
    "col_count": "2"
  }
]""")


class TestExplodeMatrix:
    def test_explode_correctly_small(self):
        exploded = traversing.explode_matrix(SMALL_MATRIX_Q)
        nstools.assert_list_equal(exploded, SMALL_MATRIX_Q_EXPLODED)

    def test_explode_correctly_big(self):
        exploded = traversing.explode_matrix(BIG_MATRIX_Q)
        nstools.assert_list_equal(exploded, BIG_MATRIX_Q_EXPLODED)


class TestExplodeAllMatrices:
    def test_explode_correctly_from_list(self):
        data = [SMALL_MATRIX_Q]
        expected = [SMALL_MATRIX_Q_EXPLODED]

        exploded = traversing.explode_all_matrices(data)
        nstools.assert_list_equal(exploded, expected)

    def test_explode_correctly_from_dict(self):
        data = {'question': SMALL_MATRIX_Q}
        expected = {'question': SMALL_MATRIX_Q_EXPLODED}

        exploded = traversing.explode_all_matrices(data)
        nstools.assert_dict_equal(exploded, expected)
