from os.path import dirname, join

import numpy as np

from dashboard.settings import *
from helpers.common import *
from siman.simple_cos_sim import SimpleCosSim
import siman.qsim as qsim

import hashlib
import queue


class Cache:
    MAX_ITEMS = 1000

    def __init__(self):
        self.cache = {}
        self.keys = queue.Queue()

    def _hash_key(self, key):
        return hashlib.md5(key.encode()).hexdigest()

    def store(self, key, item):
        key = self._hash_key(key)

        self.keys.put(key)
        if self.keys.qsize() > self.MAX_ITEMS:
            key_to_rem = self.keys.get()
            del self.cache[key_to_rem]

        self.cache[key] = item

    def retrieve(self, key):
        key = self._hash_key(key)

        if key in self.cache:
            return self.cache[key]

        return None


class Model:
    base_df = None
    cache = Cache()

    @classmethod
    def _compute_sim_matrix(cls, df):
        return SimpleCosSim(df, ANALYSED_COLS).get_similarity_matrix()

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
        return cls._compute_sim_matrix(res_df)

    @classmethod
    def _get_res_df(cls, payload):
        df = cls.base_df[cls.base_df['all_text'].str.contains(payload[KW], na=False, case=False)]

        return df.iloc[:MAX_SEARCH_RES]

    @classmethod
    def _get_bar_chart_df(cls, payload):
        if SELECTED_RES_INDEX not in payload:
            return None

        df = cls.get_res_df(payload)
        selected_res_index = int(payload[SELECTED_RES_INDEX])
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

        sim_matrix = cls._compute_sim_matrix(df)

        vdf = pd.DataFrame(sim_matrix.flatten(), columns=['similarity'])

        xdf = df.reset_index()
        xdf = pd.concat([xdf] * len(df))
        xdf.index = range(len(xdf))

        ydf = df.reset_index()
        ydf = ydf.loc[np.repeat(ydf.index.values, len(df))]
        ydf.index = range(len(ydf))

        df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
        df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + ['similarity']

        if cs_only:
            df['similarity'] = df.apply(lambda row: row['similarity'] if row['survey_id_x'] != row['survey_id_y'] else 0, axis=1)

        return df

    @classmethod
    def _get_comp_df(cls, payload):
        if COMPARED_BASE not in payload:
            return None

        if payload[COMPARED_BASE] == COMPARED_BASE_BAR:
            res_df = cls.get_res_df(payload)
            selected_res_index = int(payload[SELECTED_RES_INDEX])
            bar_chart_df = cls.get_bar_chart_df(payload)
            selected_bar_index = int(payload[SELECTED_BAR_INDEX])

            qx = res_df.iloc[selected_res_index]
            qy = bar_chart_df.iloc[selected_bar_index]

            return cls._create_comp_df(qx, qy)

        if payload[COMPARED_BASE] == COMPARED_BASE_HM:
            res_df = cls.get_res_df(payload)

            uuid_x = payload[SELECTED_HM_X]
            uuid_y = payload[SELECTED_HM_Y]

            qx = res_df.loc[uuid_x]
            qy = res_df.loc[uuid_y]

            return cls._create_comp_df(qx, qy)

    @classmethod
    def _create_comp_df(cls, qx, qy):
        def _create_series(q):
            if q is None:
                q = pd.Series()

            q['uuid'] = q.name

            q = pd.Series([q[c] if c in q else 'none' for c in DISPLAYED_COLS], index=DISPLAYED_COLS)

            return q

        qx = _create_series(qx)
        qy = _create_series(qy)

        sim = pd.Series(['']*len(qx), index=qx.index)
        for i in ANALYSED_COLS + ['survey_name']:
            sim.loc[i] = qsim.get_cos_doc_sim(str(qx.loc[i]), str(qy.loc[i]))
        for i in ['survey_id', 'form_type', 'tr_code']:
            sim.loc[i] = qsim.get_exact_doc_sim(str(qx.loc[i]), str(qy.loc[i]))

        df = pd.concat([qx, qy, sim], axis=1, ignore_index=True)
        df.columns = COMP_TBL_FIELDS

        return df

    @classmethod
    def init(cls):
        try:
            cls.base_df = load_clean_df()
        except:
            fpath = join(dirname(__file__), 'clean-light.csv')
            cls.base_df = load_clean_df(fpath=fpath)
