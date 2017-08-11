import support.bokeh_helper as bh
import qsim.sim_analyze as simeval
from dashboard.settings import *
from support.common import *
from support.cache import Cache
from qsim.sims.tfidf_cos_sim import TfidfCosSim
from qsim.sims.exact_sim import ExactSim


class Model:
    sim = TfidfCosSim()
    base_df = None
    cache = Cache()

    @classmethod
    def _compute_sim_matrix(cls, df, cs_only):
        return cls.sim.get_similarity_matrix(df, cs_only)

    # --- caching -----------------------------------------------------------

    @classmethod
    def _using_cache(cls, method, payload, relevant):
        key = method.__name__ + str([(k, None if k not in payload else payload[k]) for k in relevant])

        res = cls.cache.retrieve(key)
        if res is not None:
            return res

        res = method(payload)

        cls.cache.store(key, res)

        return res

    @classmethod
    def get_res_sim_matrix(cls, payload):
        return cls._using_cache(cls._get_res_sim_matrix, payload, relevant=[KW])

    @classmethod
    def get_res_df(cls, payload):
        return cls._using_cache(cls._get_res_df, payload, relevant=[KW])

    @classmethod
    def get_bar_chart_df(cls, payload):
        return cls._using_cache(cls._get_bar_chart_df, payload, relevant=[KW, SELECTED_RES_INDEX, CS_ONLY])

    @classmethod
    def get_heatmap_df(cls, payload):
        return cls._get_heatmap_df(payload)  # don't use cache here - we always want a new random chart

    @classmethod
    def get_comp_df(cls, payload):
        return cls._get_comp_df(payload)

    # --- functions -----------------------------------------------------------

    @classmethod
    def _get_res_sim_matrix(cls, payload):
        res_df = cls.get_res_df(payload)
        cs_only = payload[CS_ONLY] if CS_ONLY in payload else False
        return cls._compute_sim_matrix(res_df, cs_only)

    @classmethod
    def _get_res_df(cls, payload):
        df = cls.base_df[cls.base_df['all_text'].str.contains(payload[KW], na=False, case=False)]

        return df.iloc[:MAX_SEARCH_RES]

    @classmethod
    def _get_bar_chart_df(cls, payload):
        if SELECTED_RES_INDEX not in payload:
            return None

        df = cls.get_res_df(payload)
        selected_res_index = payload[SELECTED_RES_INDEX]
        cs_only = payload[CS_ONLY] if CS_ONLY in payload else False

        sim_matrix = cls.get_res_sim_matrix(payload)

        df['similarity'] = sim_matrix[selected_res_index]
        df['color'] = df['survey_id'].apply(lambda si: 'green' if si == df.iloc[selected_res_index]['survey_id'] else 'red')

        df = df.drop(df.index[selected_res_index])

        if cs_only:
            df = df[df['color'] == 'red']

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        df = df.iloc[:MAX_BARS]

        return df

    @classmethod
    def _get_heatmap_df(cls, payload):
        df = cls.get_res_df(payload)
        cs_only = payload[CS_ONLY] if CS_ONLY in payload else False

        if len(df) > MAX_HEATMAP_ITEMS:
            df = df.sample(MAX_HEATMAP_ITEMS)

        sim_matrix = cls._compute_sim_matrix(df, cs_only)

        hm_df = bh.get_heatmap_df(df, sim_matrix, 'similarity')

        return hm_df

    @classmethod
    def _get_comp_df(cls, payload):
        if COMPARED_BASE not in payload:
            return None

        if payload[COMPARED_BASE] == COMPARED_BASE_BAR:
            res_df = cls.get_res_df(payload)
            selected_res_index = payload[SELECTED_RES_INDEX]
            bar_chart_df = cls.get_bar_chart_df(payload)
            selected_bar_index = payload[SELECTED_BAR_INDEX]

            qx = res_df.iloc[selected_res_index]
            qy = bar_chart_df.iloc[selected_bar_index]

            return cls._create_comp_df(qx, qy)

        if payload[COMPARED_BASE] == COMPARED_BASE_HM:
            uuid_x = payload[SELECTED_HM_X]
            uuid_y = payload[SELECTED_HM_Y]

            qx = cls.base_df.loc[uuid_x]
            qy = cls.base_df.loc[uuid_y]

            return cls._create_comp_df(qx, qy)

    @classmethod
    def _create_comp_df(cls, qx, qy):
        col2doc_sim = [(c, cls.sim.get_text_sim) for c in ANALYSED_COLS + ['survey_name']]
        exact_sim = ExactSim()
        col2doc_sim.extend([(c, exact_sim.get_text_sim) for c in ['survey_id', 'form_type', 'tr_code']])

        df = simeval.create_comp_df(qx, qy, DISPLAYED_COLS, dict(col2doc_sim))

        return df

    @classmethod
    def init(cls):
        try:
            cls.base_df = load_clean_df()
        except:
            fpath = BUNDLED_DATA_DIR + '/clean-light.csv'
            cls.base_df = load_clean_df(fpath=fpath)
