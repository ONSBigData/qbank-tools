import os
import pandas as pd
import collections
import support.general_helper as gh
import re
import pickle

ROOT_DIR = os.path.realpath(os.path.dirname(__file__)) + '/..'
DATA_DIR = ROOT_DIR + '/../data'

BUNDLED_DATA_DIR = ROOT_DIR + '/dashboard/bundled_data'

CHECKPT_DIR = DATA_DIR + '/checkpoints'
JSON_DIR = DATA_DIR + '/jsons'

SCRAPE_STATUS_CSV_FPATH = DATA_DIR + '/scraped-status.csv'

CLEAN_FULL_FPATH = DATA_DIR + '/clean-full.csv'
CLEAN_LIGHT_FPATH = DATA_DIR + '/clean-light.csv'
PROBLEM_REPORTS_DIR = DATA_DIR + '/problem-reports'


# --- pickling -----------------------------------------------------------


def _get_standard_pickle_fpath(name):
    return '{}/{}.pkl'.format(CHECKPT_DIR, name)


def _get_bundled_pickle_fpath(name):
    return '{}/{}.pkl'.format(BUNDLED_DATA_DIR, name)


def save_pickled_obj(obj, name):
    def _save(fpath):
        with open(fpath, 'wb') as f:
            pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

    _save(_get_standard_pickle_fpath(name))
    _save(_get_bundled_pickle_fpath(name))


def load_pickled_obj(name):
    fpath = _get_standard_pickle_fpath(name)
    if not os.path.exists(fpath):
        fpath = _get_bundled_pickle_fpath(name)

    with open(fpath, 'rb') as f:
        return pickle.load(f)


# ---  -----------------------------------------------------------


def get_survey_name_map():
    sdf = pd.read_excel(DATA_DIR + '/survey-names.xlsx', index_col=0)
    d = sdf['Survey Name'].to_dict()
    return collections.defaultdict(lambda: None, d)


def get_json_fpaths(only_validated=False):
    jsons = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    jsons.sort()

    jsons = [JSON_DIR + '/' + j for j in jsons]

    if only_validated:
        df = pd.read_csv(SCRAPE_STATUS_CSV_FPATH)
        vdf = df[df['Validated?'].notnull()]
        validated = list(vdf['Filename (includes formtype)'])
        print(validated)

        jsons = [f for f in jsons if any(v in f for v in validated)]

    return jsons


def get_json_fpath(pattern=''):
    jsons = [f for f in os.listdir(JSON_DIR) if re.search(pattern, f) is not None and f.endswith('.json')]

    return JSON_DIR + '/' + jsons[0]


def load_clean_df(full=False, fpath=None):
    if fpath is None:
        fpath = CLEAN_LIGHT_FPATH
        if full:
            fpath = CLEAN_FULL_FPATH

    df = pd.read_csv(fpath, index_col=0)

    return df


if __name__ == '__main__':
    print('\n'.join(get_json_fpaths(True)))
