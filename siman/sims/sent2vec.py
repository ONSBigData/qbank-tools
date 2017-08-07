import numpy as np
import siman.qsim as qsim
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from helpers.common import *
from siman.sims.base_wv import BaseWvSim


class Sent2VecSim(BaseWvSim):
    """Based on paper https://openreview.net/pdf?id=SyK00v5xx"""

    DEF_COLS = ['suff_qtext', 'type']

    def __init__(self,
                 cols=DEF_COLS,
                 debug=False,
                 wv_dict_name='wv.dict',
                 wf_dict_name='wf.dict',
                 alpha=0.001,
                 rem_stopwords=True):
        super().__init__(cols, debug, wv_dict_name, rem_stopwords)

        self._wf_dict = load_obj(wf_dict_name)
        if rem_stopwords:
            sws = qsim.get_stop_words()
            self._wf_dict = dict((w, f) for w, f in self._wf_dict.items() if w not in sws)
        self._total_words = sum(self._wf_dict.values())
        self._alpha = alpha

    def _get_question_vec(self, question_proc_text):
        if len(question_proc_text) == 0:
            return

        word_vectors = []

        for w in question_proc_text.split():
            word_prob = self._wf_dict[w] / self._total_words
            weight = self._alpha/(self._alpha + word_prob)
            v = self._wv_dict[w] * weight

            word_vectors.append(v)

        sent_vec = np.sum(word_vectors, axis=0) / len(question_proc_text)

        return sent_vec

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        if pd.isnull(x) or pd.isnull(y) or x == '' or y == '':
            return None

        # here we don't subtract the principal component projection, as there's not enough data
        sent_vectors = np.array([self._get_question_vec(text) for text in [x, y]])
        csm = cosine_similarity(sent_vectors, sent_vectors)

        return csm[0, 1]

    def _get_similarity_matrix_from_texts(self, proc_texts):
        # N = # of items
        # V = # of vocab words
        # M = dimensionality of vector space
        # SV = sentence vector
        # PC = principal component

        # matrix of SVs - NxM
        sent_vectors = np.array([self._get_question_vec(text) for text in proc_texts])

        # get first PC of PCA - a vector of M items (matrix 1xM)
        pca = PCA(n_components=1)
        pca.fit(sent_vectors)
        first_pc = pca.components_

        # from each SV, subtract its projection onto onto the first PC
        # - the first dot product basically converts each sentence vector to its "strength" in direction of the first PC (result is matrix Nx1)
        # - the second dot product basically scales the first PC by each these "strengths" (result is matrix NxM)
        sent_vectors = sent_vectors - sent_vectors.dot(first_pc.T).dot(first_pc)

        # finally, cosine similarity on these sentence vectors
        csm = cosine_similarity(sent_vectors, sent_vectors)
        return csm



if __name__ == '__main__':
    df = load_clean_df().iloc[:100]
    # print(df)
    sim = Sent2VecSim(debug=True)

    value = sim.get_text_sim(df['all_text'][0], df['all_text'][20])
    print(value)

    # sm = sim._get_similarity_matrix(df)
    # proc_texts = [
    #     'reporting stated above, what was the value of the business turnover excluding VAT',
    #     'dates found above, how much turnover did the business have VAT excluding',
    # ]
    # sm = Sent2VecSim(debug=True)._get_similarity_matrix_from_texts(proc_texts)
    # print(sm)
