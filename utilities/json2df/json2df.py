import utilities.json2df.traversing as traversing
import utilities.json2df.validation as validation
import utilities.json2df.dataframing as dataframing
from utilities.json2df.common import *
import io


import helpers.general_helper as gh
from helpers.common import *


def json2df(json_fpath, problems=[], print_debug=True, save_csv=False):
    def _print(s):
        if print_debug:
            print(s)

    _print('opening {}...'.format(json_fpath))
    root_node = get_json_root(json_fpath, problems)

    _print('checking and correcting top level segment...')
    root_node = validation.check_and_correct_top_level_segment(root_node, problems=problems)

    _print('exploding matrix questions...')
    root_node = traversing.explode_all_matrices(root_node, problems=problems)

    _print('traversing...')
    tc_nodes = traversing.traverse(root_node)

    _print('filtering invalid words...')
    tc_nodes = validation.filter_invalid_words(tc_nodes, problems=problems)

    _print('creating dataframe...')
    df = dataframing.create_df(tc_nodes, problems=problems)

    _print('dataframe with shape {} created'.format(df.shape))

    if save_csv:
        csv_fpath = json_fpath.replace('/jsons/', '/csvs/').replace('.json', '.csv')
        df.to_csv(csv_fpath, index=True)

        _print('dataframe saved to {}'.format(csv_fpath))

    return df


def create_full_df(print_debug=True):
    def _print(s=''):
        if print_debug:
            print(s)

    SEP_LEN = 100

    dfs = []

    for i, json_fpath in enumerate(get_json_fpaths()):
        _print()
        _print('{}.) {}'.format(i, '-' * SEP_LEN))

        try:
            problems = []
            df = json2df(json_fpath, problems, print_debug=print_debug)

            if len(problems) != 0:
                _print('PROBLEMS: {}'.format(', '.join([p[0] for p in problems])))
        except json.JSONDecodeError as e:
            _print('JSON decode ERROR: {}'.format(e))
            continue
        except Exception as e:
            _print('ERROR: {}'.format(e))
            continue

        dfs.append(df)

    _print('=' * SEP_LEN)
    _print('combining dataframes...')

    cdf = pd.concat(dfs)

    cdf = cdf.reset_index()
    cdf['uuid'] = gh.uniquify(cdf, 'uid')
    cdf = cdf.set_index('uuid')

    cdf = gh.reorder_cols(cdf, first_cols=FIRST_COLS)

    _print('shape of final dataframe: {}'.format(cdf.shape))

    cdf.to_csv(CLEAN_FULL_FPATH, index=True)
    cdf[FIRST_COLS].to_csv(CLEAN_LIGHT_FPATH, index=True)

    return cdf


def get_problems_report(json_fpaths=get_json_fpaths()):
    stream = io.StringIO()

    for json_fpath in json_fpaths:
        stream.write('\n')
        stream.write('-'*100 + '\n')
        stream.write(os.path.basename(json_fpath) + '\n')

        try:
            problems = []
            json2df(json_fpath, problems, print_debug=False)
        except Exception as e:
            stream.write('ERROR: {}'.format(e)+ '\n')
            continue

        for p in problems:
            stream.write('{}: {}'.format(p[0], p[1])+ '\n')

        if len(problems) == 0:
            stream.write('OK\n')

    s = stream.getvalue()

    with open(PROBLEM_REPORTS_DIR + '/problems_report.txt', 'w') as f:
        f.write(s)

    return s


if __name__ == '__main__':
    create_full_df()
    # print(get_problems_report())