import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import siman.qsim as qsim
from helpers.common import *
from siman.sims.base_sim import BaseSim


class AvgWvSim(BaseSim):
    DEF_COLS = ['suff_qtext', 'type']

    def __init__(self, cols=DEF_COLS, debug=False, wv_dict_name='wv.dict', rem_stopwords=True):
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

        sm = self._get_similarity_matrix_from_texts(np.array([x, y]))

        return sm[0, 1]


    def _get_similarity_matrix(self, df):
        proc_texts = self._preprocess_df(df)

        return self._get_similarity_matrix_from_texts(proc_texts)

    def _get_similarity_matrix_from_texts(self, proc_texts):
        # N = # of items
        # V = # of vocab words
        # M = dimensionality of vector space

        # create TF-IDF matrix - one row per question (N x V)
        tfidf_vectorizer = TfidfVectorizer()
        tfidf_matrix = tfidf_vectorizer.fit_transform(proc_texts).toarray()

        # get features (words)
        features = tfidf_vectorizer.get_feature_names()

        # now make word vector for each feature -> a V x M matrix - one row (word vec) per feature
        wvs_matrix = np.array([self._wv_dict[f] for f in features])

        # multiply the two matrices to get a matrix N x M
        # - each row is a (tf-idf) scaled sum of the word vectors for words of the question
        sumwv_matrix = np.matrix.dot(tfidf_matrix, wvs_matrix)

        # now normalize using the sum oprf tf-idfs for the question's words
        sumtfidf_vec = tfidf_matrix.sum(axis=1)
        avgwv_matrix = sumwv_matrix / sumtfidf_vec[:, np.newaxis]

        # finally, cosine similarity on this
        csm = cosine_similarity(avgwv_matrix, avgwv_matrix)
        return csm



if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = AvgWvSim(debug=True).get_similarity_matrix(df)
    print(sm)
