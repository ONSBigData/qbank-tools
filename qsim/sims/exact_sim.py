import nltk
import numpy as np
import qsim.qsim_common as qsim
from support.common import *
from qsim.sims.base_sim import BaseSim


class ExactSim(BaseSim):
    def __init__(self, cols=None, debug=False, lower=True, stem=True, rem_stopwords=True, only_alphanum=True):
        super().__init__(cols, debug)

        self._lower = lower
        self._stem = stem
        self._rem_stopwords = rem_stopwords
        self._only_alphanum = only_alphanum

        self._stemmer = nltk.stem.PorterStemmer()
        self._sws = qsim.get_stop_words()

    def _preprocess_text(self, text):
        if self._lower:
            text = text.lower()

        if self._only_alphanum:
            text = re.sub(r"[^a-zA-Z0-9]", " ", text)

        words = nltk.word_tokenize(text)

        if self._rem_stopwords:
            words = [w for w in words if w not in self._sws]

        if self._stem:
            words = [self._stemmer.stem(t) for t in words]

        return ' '.join(words)

    def _preprocess_question(self, question_series, cols):
        return ' ||||| '.join(str(x) for x in question_series[cols])

    def preprocess_question(self, question_series):
        cols = self._cols if self._cols is not None else list(question_series.index)

        return self._preprocess_question(question_series, cols)

    def _preprocess_df(self, df):
        texts = []
        cols = self._cols if self._cols is not None else list(df.columns)
        for _, row in df.iterrows():
            text = self._preprocess_question(row, cols)
            texts.append(text)

        proc_texts = [self._preprocess_text(text) for text in texts]

        return np.array(proc_texts)

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        return 1 if x == y else 0

    def _get_similarity_matrix(self, df):
        proc_array = self._preprocess_df(df)

        n = len(proc_array)
        M = np.repeat(proc_array, n).reshape(n, n)
        sm = np.zeros((n, n))
        sm[M == M.T] = 1
        return sm


if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = ExactSim(debug=True).get_similarity_matrix(df)
    print(sm)

