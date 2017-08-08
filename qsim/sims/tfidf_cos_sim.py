from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from helpers.common import *
from qsim.sims.exact_sim import ExactSim


class TfidfCosSim(ExactSim):
    def __init__(self, cols=None, debug=False, lower=True, stem=True, rem_stopwords=True, only_alphanum=True):
        super().__init__(cols, debug, lower, stem, rem_stopwords, only_alphanum)

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        vect = TfidfVectorizer(lowercase=self._lower)
        tfidf = vect.fit_transform([x, y])
        return (tfidf * tfidf.T).A[0, 1]

    def _get_similarity_matrix(self, df):
        proc_array = self._preprocess_df(df)

        tfidf_vectorizer = TfidfVectorizer(lowercase=self._lower)
        tfidf_matrix = tfidf_vectorizer.fit_transform(proc_array)
        csm = cosine_similarity(tfidf_matrix, tfidf_matrix)
        return csm


if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = TfidfCosSim(debug=True).get_similarity_matrix(df)
    print(sm)
