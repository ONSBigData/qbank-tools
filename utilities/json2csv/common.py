import json

PATH = 'path'
VALUE = 'value'
ATTRS = 'attrs'

# JSON keys
JK_SEGMENT = 'segment'
JK_QUESTION = 'question'
JK_SCRAPE_INFO = 'survey_scrape_info'
JK_TR_CODE = 'tracking_code'

FIRST_COLS = [
    'uid',
    'survey_id',
    'survey_name',
    'form_type',
    'tr_code',
    'type',
    'period_days',
    'period_start',
    'period_end',
    'qtext',
    'sufficient_qtext',
    'first_text',
    'close_seg_text',
    'all_seg_text',
    'all_text',
    'all_context',
    'all_inclusions',
    'all_exclusions'
]


class Problems:
    IncorrectTlSeg = 'INCORRECT_TOP_LEVEL_SEGMENT'
    InvalidWords = 'INVALID_KEYWORDS'
    ReportingPeriod = 'PROBLEM_WITH_REPORTING_PERIOD'
    MatrixParsing = 'MATRIX_PARSING_PROBLEM'
    NoData = 'NO_DATA'
    Encoding = 'ENCODING_NOT_UTF8'


def get_json_root(fpath, problems=[]):
    try:
        with open(fpath, encoding='utf8') as f:
            root_node = json.load(f)
    except:
        problems.append((Problems.Encoding, 'encoding is UTF-8-sig'))
        with open(fpath, encoding='utf-8-sig') as f:
            root_node = json.load(f)

    return root_node