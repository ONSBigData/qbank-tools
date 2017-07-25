import json

import nose.tools as nstools

from utilities import json2clean

SMALL_MQ = json.JSONDecoder().decode("""{
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

SMALL_MQ_EXPLODED = json.JSONDecoder().decode("""[
  {
    "row_index": "1",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3218",
    "row_text": "Banks and building societies?"
  }
]""")

BIG_MQ = json.JSONDecoder().decode("""{
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

BIG_MQ_EXPLODED = json.JSONDecoder().decode("""[
  {
    "row_index": "1",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3218",
    "row_text": "Banks and building societies?"
  },
  {
    "row_index": "1",
    "col_text": "Disposals of assets",
    "col_index": "2",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "a",
    "tracking_code": "3219",
    "row_text": "Banks and building societies?"
  },
  {
    "row_index": "2",
    "col_text": "Acquisitions of assets at cost",
    "col_index": "1",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "b",
    "tracking_code": "3040",
    "row_text": "Other UK corporates?"
  },
  {
    "row_index": "2",
    "col_text": "Disposals of assets",
    "col_index": "2",
    "col_context": "Millions of £",
    "col_type": "pound_hunthousands",
    "row_ID": "b",
    "tracking_code": "3041",
    "row_text": "Other UK corporates?"
  }
]""")


class TestExplodeMatrix:
    def test_explode_correctly_small(self):
        exploded = json2clean.explode_matrix(SMALL_MQ)
        nstools.assert_list_equal(exploded, SMALL_MQ_EXPLODED)

    def test_explode_correctly_big(self):
        exploded = json2clean.explode_matrix(BIG_MQ)
        nstools.assert_list_equal(exploded, BIG_MQ_EXPLODED)


class TestExplodeAllMatrices:
    def test_explode_correctly_from_list(self):
        data = [SMALL_MQ]
        expected = [SMALL_MQ_EXPLODED]

        exploded = json2clean.explode_all_matrices(data)
        nstools.assert_list_equal(exploded, expected)

    def test_explode_correctly_from_dict(self):
        data = {'question': SMALL_MQ}
        expected = {'question': SMALL_MQ_EXPLODED}

        exploded = json2clean.explode_all_matrices(data)
        nstools.assert_dict_equal(exploded, expected)
