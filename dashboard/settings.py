MAX_SEARCH_RES = 500
MAX_HEATMAP_ITEMS = 50
MAX_BARS = 10
ANALYSED_COLS = ['suff_qtext', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['uuid', 'survey_id', 'survey_name', 'form_type', 'tr_code', 'suff_qtext']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

KW = 'kw'
SELECTED_RES_INDEX = 'selected_res_index'
COMPARED_BASE = 'compared_base'
COMPARED_BASE_BAR = 'bar'
COMPARED_BASE_HM = 'hm'
SELECTED_BAR_INDEX = 'selected_bar_index'
SELECTED_HM_X = 'selected_hm_x'
SELECTED_HM_Y = 'selected_hm_y'
CS_ONLY = 'cs_only'
SIM = 'sim'
