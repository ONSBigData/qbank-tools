import os
import pandas as pd

DATA_DIR = os.path.realpath(os.path.dirname(__file__)) + '/../data'

JSON_DIR = DATA_DIR + '/jsons'

SCRAPE_STATUS_CSV_FNAME = 'scraped-status.csv'

CLEAN_FULL_FPATH = DATA_DIR + '/clean-full.csv'
CLEAN_LIGHT_FPATH = DATA_DIR + '/clean-light.csv'
PROBLEM_REPORTS_DIR = DATA_DIR + '/problem-reports'


def get_all_jsons():
    jsons = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
    jsons.sort()

    return [JSON_DIR + '/' + j for j in jsons]


def get_validated_jsons(scrape_status_csv_fname=SCRAPE_STATUS_CSV_FNAME):
    df = pd.read_csv(DATA_DIR + '/' + scrape_status_csv_fname)
    vdf = df[df['Validated?'].notnull()]
    validated = list(vdf['Filename (includes formtype)'])

    jsons = [f for f in get_all_jsons() if any(v in f for v in validated)]

    return jsons


def load_clean_df(full=False):
    fpath = CLEAN_LIGHT_FPATH
    if full:
        fpath = CLEAN_FULL_FPATH

    return pd.read_csv(fpath, index_col=0)


if __name__ == '__main__':
    print('\n'.join(get_validated_jsons()))

