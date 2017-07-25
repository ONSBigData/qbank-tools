MAX_SEARCH_RES = 500
MAX_HEATMAP_ITEMS = 50
MAX_BARS = 10
ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['uuid', 'survey_id', 'survey_name', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]
COMP_TBL_FIELDS = ['question X', 'question Y']