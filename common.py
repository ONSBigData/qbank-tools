import os
import pandas as pd

DATA_DIR = os.path.realpath(os.path.dirname(__file__)) + '/../data'

JSON_DIR = DATA_DIR + '/jsons'

SCRAPE_STATUS_CSV_FNAME = 'scrape-status.csv'


def get_validated_jsons(scrape_status_csv_fname=SCRAPE_STATUS_CSV_FNAME):
    df = pd.read_csv(DATA_DIR + '/' + scrape_status_csv_fname)
    vdf = df[df['Validated?'].notnull()]
    validated = list(vdf['Filename (includes formtype)'])

    jsons = [f for f in os.listdir(JSON_DIR) if any(f.startswith(v) for v in validated)]
    jsons.sort()

    return [JSON_DIR + '/' + j for j in jsons]

if __name__ == '__main__':
    print('\n'.join(get_validated_jsons()))

