import numpy as np
from siman.simple_cos_sim import SimpleCosSim
from common import *
from dashboard.settings import *
from pyjarowinkler import distance as pyjarodist

class Model:
    base_df = None
    res_df = None
    bar_chart_df = None
    hm_base_df = None
    hm_df = None
    comp_df = None

    selected_result_index = None

    only_cross_survey = False

    sim_matrix = None

    @staticmethod
    def compute_sim_matrix(df):
        return SimpleCosSim(df, ANALYSED_COLS).get_similarity_matrix()

    @classmethod
    def update_res_df(cls, search_kw):
        search_kw = search_kw if search_kw is not None else ''

        cls.res_df = cls.base_df[cls.base_df['all_text'].str.contains(search_kw, na=False, case=False)]
        if len(cls.res_df) > MAX_SEARCH_RES:
            cls.res_df = cls.res_df.sample(MAX_SEARCH_RES)

        cls.sim_matrix = cls.compute_sim_matrix(cls.res_df)

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
        if cls.only_cross_survey:
            df = df[df['color'] == 'red']

        df = df.drop(df.index[idx])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        cls.bar_chart_df = df.iloc[:MAX_BARS]

    @classmethod
    def update_selected_bar_index(cls, index):
        cls.selected_bar_index = index

    @classmethod
    def update_heatmap_df(cls):
        if len(cls.res_df) == 0:
            cls.hm_df = None
            return

        df = cls.res_df.copy()
        if len(df) > MAX_HEATMAP_ITEMS:
            df = df.sample(MAX_HEATMAP_ITEMS)
        cls.hm_base_df = df

        sim_matrix = cls.compute_sim_matrix(df)

        vdf = pd.DataFrame(sim_matrix.flatten(), columns=['similarity'])

        xdf = df.reset_index()
        xdf = pd.concat([xdf] * len(df))
        xdf.index = range(len(xdf))

        ydf = df.reset_index()
        ydf = ydf.loc[np.repeat(ydf.index.values, len(df))]
        ydf.index = range(len(ydf))

        df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
        df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + ['similarity']

        if cls.only_cross_survey:
            df['similarity'] = df.apply(lambda row: row['similarity'] if row['survey_id_x'] != row['survey_id_y'] else 0, axis=1)

        cls.hm_df = df

    @classmethod
    def update_comp_df(cls, qx, qy):
        def _create_series(q):
            if q is None:
                q = pd.Series()

            q['uuid'] = q.name

            q = pd.Series([q[c] if c in q else 'none' for c in DISPLAYED_COLS], index=DISPLAYED_COLS)


            return q

        qx = _create_series(qx)
        qy = _create_series(qy)

        sim = pd.Series(['']*len(qx), index=qx.index)
        for i in ANALYSED_COLS:
            sim.loc[i] = pyjarodist.get_jaro_distance(str(qx[i]), str(qy[i]), winkler=True, scaling=0.1)

        df = pd.concat([qx, qy, sim], axis=1, ignore_index=True)
        df.columns = COMP_TBL_FIELDS

        cls.comp_df = df

    @classmethod
    def init(cls):
        try:
            cls.base_df = load_clean_df()
        except:
            cls.base_df = load_clean_df(fpath='./clean-light.csv')

    # --- actions -----------------------------------------------------------

    @classmethod
    def search_for_kw(cls, search_kw=None):
        cls.update_res_df(search_kw)
        cls.update_selected_result_index(None)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()

    @classmethod
    def select_search_res(cls, selected_result_index=None):
        cls.update_selected_result_index(selected_result_index)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()

    @classmethod
    def select_bar(cls, bar_index=None):
        if cls.selected_result_index is None or bar_index is None:
            cls.comp_df = None
            return

        qx = Model.res_df.iloc[cls.selected_result_index]
        qy = Model.bar_chart_df.iloc[bar_index]

        cls.update_comp_df(qx, qy)

    @classmethod
    def select_hm_cell(cls, uuid_x, uuid_y):
        if uuid_x is None or uuid_y is None:
            cls.comp_df = None
            return

        qx = Model.res_df.loc[uuid_x]
        qy = Model.res_df.loc[uuid_y]

        cls.update_comp_df(qx, qy)