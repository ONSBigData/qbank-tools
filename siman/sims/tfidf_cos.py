import nltk
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import siman.qsim as qsim
from helpers.common import *
from siman.sims.base_sim import BaseSim


class TfidfCosSim(BaseSim):
    def __init__(self, cols=None, debug=False):
        super().__init__(cols, debug)

    def preprocess(self, df):
        self._lg.debug('Processing...')

        items = []
        cols = self._cols if self._cols is not None else list(df.columns)
        for _, row in df.iterrows():
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

            words = [stemmer.stem(t) for t in words]

            proc_item = ' '.join(words)
            proc_items.append(proc_item)

            self._lg.debug('Item:           {}'.format(item))
            self._lg.debug('Processed item: {}'.format(proc_item))

        return np.array(proc_items)

    def _get_similarity_matrix(self, df):
        proc_array = self.preprocess(df)

        tfidf_vectorizer = TfidfVectorizer(lowercase=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(proc_array)
        csm = cosine_similarity(tfidf_matrix, tfidf_matrix)
        return csm


if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = TfidfCosSim(debug=True)._get_similarity_matrix(df)
    print(sm)
