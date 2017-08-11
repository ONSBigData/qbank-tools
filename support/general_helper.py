import datetime
import collections
import os
import sys


def print_and_flush(s):
    print(s)
    sys.stdout.flush()


def get_date():
    return datetime.datetime.now().strftime("%y-%m-%d")


def get_time():
    return datetime.datetime.now().strftime("%H-%M-%S")


def uniquify(df, col):
    sr = df[col]
    val_counts = sr.value_counts().to_dict()

    new_sr = []

    counts = collections.defaultdict(int)
    for x in sr:
        if val_counts[x] == 1:
            new_sr.append(x)
            continue

        counts[x] += 1
        new_sr.append('{}_({})'.format(x, counts[x] - 1))

    return new_sr


def reorder_cols(df, first_cols):
    def sort_function(c):
        if c in first_cols:
            return first_cols.index(c)
        return len(first_cols) + 1

    cols = list(df.columns)
    cols.sort(key=sort_function)
    return df[cols]
