import logging
import re

import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import helpers.log_helper as lg
import siman.qsim as qsim
from helpers.common import *

import utilities.json2df.dataframing as dataframing
import nltk
import re
from nltk.corpus import stopwords
from gensim.models import word2vec
from gensim.models import Phrases


# COLS = ['all_text', 'all_context', 'all_inclusions', 'all_exclusions', 'notes']
COLS = ['suff_qtext', 'type']


class AvgWvSim:
    def __init__(self, df, wv_dict_name='wv.dict', cols=COLS, debug=False):
        self._debug = debug
        self._lg = lg.get_logger(str(self.__class__.__name__))
        if not debug:
            self._lg.setLevel(logging.WARNING)

        self._df = df
        self._cols = cols
        self._wv_dict = load_obj(wv_dict_name)


    def preprocess(self):
        items = []

        sws = qsim.get_stop_words()

        cols = self._cols if self._cols is not None else list(self._df.columns)
        for _, row in self._df.iterrows():
            text = ' '.join(str(x) for x in row[cols] if pd.notnull(x))
            sents = qsim.text2sents(text)
            words = [w for s in sents for w in qsim.sent2words(s)]

            words = [w.lower() for w in words]
            words = [w for w in words if w not in sws and w in self._wv_dict]

            item = ' '.join(words)
            items.append(item)

        return np.array(items)


    def get_similarity_matrix(self):
        items = self.preprocess()

        # N = # of items
        # V = # of vocab words
        # M = dimensionality of vector space

        # create TF-IDF matrix - one row per question (N x V)
        tfidf_vectorizer = TfidfVectorizer(lowercase=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(items).toarray()

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
    sm = AvgWvSim(df, debug=True).get_similarity_matrix()
    print(sm)
