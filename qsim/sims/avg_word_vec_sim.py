import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from helpers.common import *
from qsim.sims.embeddings_based_sim import EmbeddingsBasedSim


class AvgWordVecSim(EmbeddingsBasedSim):
    DEF_COLS = ['suff_qtext', 'type']

    def __init__(self, cols=DEF_COLS, debug=False, wv_dict_name='wv.dict', rem_stopwords=True):
        super().__init__(cols, debug, wv_dict_name, rem_stopwords)

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
    sm = AvgWordVecSim(debug=True).get_similarity_matrix(df)
    print(sm)
