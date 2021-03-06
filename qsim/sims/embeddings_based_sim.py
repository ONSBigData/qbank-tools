import numpy as np
import qsim.qsim_common as qsim
from support.common import *
from qsim.sims.base_sim import BaseSim


class EmbeddingsBasedSim(BaseSim):
    def __init__(self, cols, debug, wv_dict_model_name, rem_stopwords):
        super().__init__(cols, debug)

        self._wv_dict = qsim.load_word_vectors(wv_dict_model_name)
        self._rem_stopwords = rem_stopwords
        self._sws = qsim.get_stop_words()


    def _preprocess_df(self, df):
        proc_texts = []

        cols = self._cols if self._cols is not None else list(df.columns)
        for _, row in df.iterrows():
            proc_texts.append(self._preprocess_question(row, cols))

        return np.array(proc_texts)

    def _get_similarity_matrix(self, df):
        proc_texts = self._preprocess_df(df)

        return qsim.exp_scale(self._get_similarity_matrix_from_texts(proc_texts))

    def _preprocess_question(self, question_series, cols):
        text = ' '.join(str(x) for x in question_series[cols] if pd.notnull(x))
        item = self._preprocess_text(text)
        return item

    def preprocess_question(self, question_series):
        cols = self._cols if self._cols is not None else list(question_series.index)

        return self._preprocess_question(question_series, cols)

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