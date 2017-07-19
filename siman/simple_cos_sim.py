from common import *
import helpers.log_helper as lg
import siman.qsim as qsim
import logging


import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import gensim as gs
import numpy as np

import nltk
from nltk.corpus import stopwords
import re
from six import iteritems
import pyLDAvis.gensim

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class SimpleCosSim:
    def __init__(self, df, cols=None, debug=False):
        self._debug = debug
        self._lg = lg.get_logger(str(self.__class__.__name__))
        if not debug:
            self._lg.setLevel(logging.WARNING)

        self._df = df
        self._cols = cols

    def preprocess(self):
        self._lg.debug('Processing...')

        items = []
        cols = self._cols if self._cols is not None else list(self._df.columns)
        for _, row in self._df.iterrows():
            item = ' ||||| '.join(str(x) for x in row[cols])
            items.append(item)
        array = np.array(items)

        stemmer = nltk.stem.PorterStemmer()
        sws = qsim.get_stop_words()

        proc_items = []

        for item in array:
            item = item.lower()

            item = re.sub(r"[^a-zA-Z0-9]", " ", item)

            words = nltk.word_tokenize(item)

            words = [w for w in words if w not in sws]

            # one letter words
            # words = [w for w in words if len(w) > 1]

            words = [stemmer.stem(t) for t in words]

            proc_item = ' '.join(words)
            proc_items.append(proc_item)

            self._lg.debug('Item:           {}'.format(item))
            self._lg.debug('Processed item: {}'.format(proc_item))

        return np.array(proc_items)

    def get_similarity_matrix(self):
        proc_array = self.preprocess()

        tfidf_vectorizer = TfidfVectorizer(lowercase=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(proc_array)
        csm = cosine_similarity(tfidf_matrix, tfidf_matrix)
        return csm


if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = SimpleCosSim(debug=True).get_similarity_matrix(df['text'])
    print(sm)
