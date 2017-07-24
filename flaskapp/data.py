# --- constants -----------------------------------------------------------

MAX_SEARCH_RES = 50

ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['survey_id', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

COMP_TBL_FIELDS = ['selected', 'compared']

INIT_KW = ''


class Data:
    base_df = None
    res_df = None
    bar_chart_df = None
    hm_df = None

    sim_matrix = None

    selected_result_index = None

    only_cross_survey = False

    @classmethod
    def update_res_df(cls, search_kw):
        cls.res_df = cls.base_df[cls.base_df['all_text'].str.contains(search_kw, na=False)]
        if len(cls.res_df) > MAX_SEARCH_RES:
            cls.res_df = cls.res_df.sample(MAX_SEARCH_RES)

        cls.compute_sim_matrix()

    @classmethod
    def update_selected_result_index(cls, index):
        cls.selected_result_index = index

    @classmethod
    def update_bar_chart_df(cls):
        if len(cls.res_df) == 0 or cls.selected_result_index is None:
            cls.bar_chart_df = None
            return None

        idx = cls.selected_result_index

        df = cls.res_df.copy()

        df['similarity'] = cls.sim_matrix[idx]
        df['color'] = df['survey_id'].apply(lambda si: 'green' if si == df.iloc[idx]['survey_id'] else 'red')

        df = df.drop(df.index[idx])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        cls.bar_chart_df = df.iloc[:MAX_BARS]

    @classmethod
    def update_heatmap_df(cls):
        if len(cls.res_df) == 0:
            cls.hm_df = None
            return

        df = cls.res_df.copy()

        vdf = pd.DataFrame(cls.sim_matrix.flatten(), columns=['similarity'])

        xdf = df.reset_index()
        xdf = pd.concat([xdf] * len(df))
        xdf.index = range(len(xdf))

        ydf = df.reset_index()
        ydf = ydf.loc[np.repeat(ydf.index.values, len(df))]
        ydf.index = range(len(ydf))

        df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
        df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + ['similarity']

        cls.hm_df = df

    @classmethod
    def compute_sim_matrix(cls):
        if len(cls.res_df) == 0:
            cls.sim_matrix = None
            return

        cls.sim_matrix = SimpleCosSim(cls.res_df, ANALYSED_COLS).get_similarity_matrix()

    @classmethod
    def init(cls):
        cls.base_df = load_clean_df()

        cls.update_res_df(INIT_KW)
        cls.update_selected_result_index(None)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()