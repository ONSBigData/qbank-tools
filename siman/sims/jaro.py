from helpers.common import *
from siman.sims.exact import ExactSim
from pyjarowinkler import distance as pyjarodist
import pathos.multiprocessing as mp
import time
import numpy as np


class JaroSim(ExactSim):
    def __init__(self, cols=None, debug=False, lower=True, stem=True, rem_stopwords=True, only_alphanum=True):
        super().__init__(cols, debug, lower, stem, rem_stopwords, only_alphanum)

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        return self._compute(x, y)

    def _compute(self, x, y):
        return pyjarodist.get_jaro_distance(x, y, winkler=True, scaling=0.1)

    def _get_similarity_matrix(self, df):
        CHUNK_COUNT = 5000

        proc_array = self._preprocess_df(df)
        n = len(proc_array)
        relevant_pairs = [(x, y) for x in range(n) for y in range(x)]

        t = time.time()
        with mp.Pool(32) as pool:
            results = []

            for i in range(0, len(relevant_pairs), CHUNK_COUNT):
                self._lg.debug('{}/{}'.format(i, len(relevant_pairs)))
                chunk = relevant_pairs[i:i + CHUNK_COUNT]
                chunk_results = list(pool.map(lambda p: self._compute(proc_array[p[0]], proc_array[p[1]]), chunk))

                results.extend(chunk_results)

        self._lg.debug('Took {} sec'.format(time.time() - t))

        # now reconstruct matrix
        rows = []
        offset = 0
        for i in range(n):
            row = results[offset:offset + i] + [1] + [0]*(n - i - 1)
            rows.append(row)
            offset += i

        sm = np.array(rows)
        for i in range(n):
            sm[i, i + 1:] = sm[i + 1:, i]

        return sm

if __name__ == '__main__':
    df = load_clean_df().iloc[:5]
    sm = JaroSim(debug=True).get_similarity_matrix(df)
    print(sm)
