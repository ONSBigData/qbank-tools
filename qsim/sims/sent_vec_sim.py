import numpy as np
import qsim.qsim_common as qsim
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
from helpers.common import *
from qsim.sims.embeddings_based_sim import EmbeddingsBasedSim
from qsim.qsim_common import W2vModelName


class SentVecSim(EmbeddingsBasedSim):
    """Based on paper https://openreview.net/pdf?id=SyK00v5xx"""

    DEF_COLS = ['suff_qtext', 'type']

    def __init__(self,
                 cols=DEF_COLS,
                 debug=False,
                 wv_dict_model_name=W2vModelName.PretrainedGoogleNews,
                 wf_dict_name=qsim.DEF_WF_DICT_NAME,
                 first_pc_name=qsim.FIRST_PC_EXC_STOP_NAME,
                 alpha=0.001,
                 rem_stopwords=True):
        super().__init__(cols, debug, wv_dict_model_name, rem_stopwords)

        self._wf_dict = qsim.load_word_frequencies_dict(wf_dict_name)
        if rem_stopwords:
            sws = qsim.get_stop_words()
            self._wf_dict = dict((w, f) for w, f in self._wf_dict.items() if w not in sws)
        self._total_words = sum(self._wf_dict.values())
        self._alpha = alpha
        self._first_pc = None if first_pc_name is None else qsim.load_1st_pc(first_pc_name)

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

        sent_vectors = np.array([self._get_question_vec(text) for text in [x, y]])
        if self._first_pc is not None:
            sent_vectors = sent_vectors - sent_vectors.dot(self._first_pc.T).dot(self._first_pc)

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
        first_pc = self._get_first_pc(sent_vectors)

        # from each SV, subtract its projection onto onto the first PC
        # - the first dot product basically converts each sentence vector to its "strength" in direction of the first
        #   PC (result is matrix Nx1)
        # - the second dot product basically scales the first PC by each these "strengths" (result is matrix NxM)
        sent_vectors = sent_vectors - sent_vectors.dot(first_pc.T).dot(first_pc)

        # finally, cosine similarity on these sentence vectors
        csm = cosine_similarity(sent_vectors, sent_vectors)
        return csm

    def _get_first_pc(self, sent_vectors):
        if self._first_pc is not None:
            return self._first_pc

        pca = PCA(n_components=1)
        pca.fit(sent_vectors)
        first_pc = pca.components_

        return first_pc

    def get_first_pc(self, df):
        proc_texts = self._preprocess_df(df)
        sent_vectors = np.array([self._get_question_vec(text) for text in proc_texts])
        first_pc = self._get_first_pc(sent_vectors)

        return first_pc


if __name__ == '__main__':
    df = load_clean_df().iloc[:100]
    # print(df)
    sim = SentVecSim(debug=True)

    value = sim.get_text_sim(df['all_text'][0], df['all_text'][20])
    print(value)

    # sm = sim._get_similarity_matrix(df)
    # proc_texts = [
    #     'reporting stated above, what was the value of the business turnover excluding VAT',
    #     'dates found above, how much turnover did the business have VAT excluding',
    # ]
    # sm = Sent2VecSim(debug=True)._get_similarity_matrix_from_texts(proc_texts)
    # print(sm)
