import os
import pandas as pd
import collections
import support.general_helper as gh
import re
import pickle

ROOT_DIR = os.path.realpath(os.path.dirname(__file__)) + '/..'
BUNDLED_DATA_DIR = ROOT_DIR + '/dashboard/bundled_data'

# --- DATA -----------------------------------------------------------

# point the following constants to folders where you want to have data

# root folder for your data
DATA_DIR = ROOT_DIR + '/../data'

# folder where trained models or pickled files are to be stored
CHECKPT_DIR = DATA_DIR + '/checkpoints'

# folder where scraped JSONs are located
JSON_DIR = DATA_DIR + '/jsons'

# folder where JSON validation problems should be reported
PROBLEM_REPORTS_DIR = DATA_DIR + '/problem-reports'

# pretrained word vectors from Google news articles.
# can be downloaded from e.g. https://github.com/mmihaltz/word2vec-GoogleNews-vectors
GOOGLE_NEWS_WORD_VECS = DATA_DIR + '/pretrained-w2v/GoogleNews-vectors-negative300.bin'

# path to a CSV containing the table from confluence of scrape statuses for scraping surveys
SCRAPE_STATUS_CSV_FPATH = DATA_DIR + '/scraped-status.csv'

# path where full CSV should be output by json2df
CLEAN_FULL_FPATH = DATA_DIR + '/clean-full.csv'

# path where light (only main columns) CSV should be output by json2df
CLEAN_LIGHT_FPATH = DATA_DIR + '/clean-light.csv'

# NOTE! update also the paths in deploy-common.sh


# --- pickling -----------------------------------------------------------

# quick helpers to persist and load back objects. Used to store e.g. word vector dictionaries or first principal component
# of sentence vectors, so that they don't have to be re-computed every time

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


# --- others -----------------------------------------------------------


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
