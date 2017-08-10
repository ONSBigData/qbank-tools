import json

PATH = 'path'
VALUE = 'value'
ATTRS = 'attrs'
NOTE_ID = 'note_id'

# JSON keys
JK_SEGMENT = 'segment'
JK_QUESTION = 'question'
JK_SCRAPE_INFO = 'survey_scrape_info'
JK_TR_CODE = 'tracking_code'
JK_NOTE_ID = 'note_id'

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
    'suff_qtext',
    'first_text',
    'close_seg_text',
    'all_seg_text',
    'all_text',
    'all_context',
    'all_inclusions',
    'all_exclusions',
    'sci_download_date',
    'sci_scrape_date',
    'sci_file_name',
    'sci_folder_name',
    'notes'
]


class Problems:
    IncorrectTlSeg = 'INCORRECT_TOP_LEVEL_SEGMENT'
    InvalidWords = 'INVALID_KEYWORDS'
    ReportingPeriod = 'PROBLEM_WITH_REPORTING_PERIOD'
    FormType = 'MISSING_FORM_TYPE'
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