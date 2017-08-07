import numpy as np
import siman.qsim as qsim
from helpers.common import *
from siman.sims.base_sim import BaseSim


class BaseWvSim(BaseSim):
    def __init__(self, cols, debug=False, wv_dict_name='wv.dict', rem_stopwords=True):
        super().__init__(cols, debug)

        self._wv_dict = load_obj(wv_dict_name)
        self._rem_stopwords = rem_stopwords
        self._sws = qsim.get_stop_words()


    def _preprocess_df(self, df):
        proc_texts = []

        cols = self._cols if self._cols is not None else list(df.columns)
        for _, row in df.iterrows():
            text = ' '.join(str(x) for x in row[cols] if pd.notnull(x))
            item = self._preprocess_text(text)
            proc_texts.append(item)

        return np.array(proc_texts)

    def _get_similarity_matrix(self, df):
        proc_texts = self._preprocess_df(df)

        return qsim.exp_scale(self._get_similarity_matrix_from_texts(proc_texts))

    def _preprocess_text(self, text):
        sents = qsim.text2sents(text)
        words = [w for s in sents for w in qsim.sent2words(s)]
        words = [w.lower() for w in words]
        words = [w for w in words if w in self._wv_dict]

        if self._rem_stopwords:
            words = [w for w in words if w not in self._sws]

        return ' '.join(words)

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        if pd.isnull(x) or pd.isnull(y) or x == '' or y == '':
            return None

        sm = self._get_similarity_matrix_from_texts(np.array([x, y]))

        return sm[0, 1]

    def _get_similarity_matrix_from_texts(self, proc_texts):
        raise NotImplementedError