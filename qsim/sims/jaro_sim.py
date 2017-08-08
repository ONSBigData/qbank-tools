from helpers.common import *
from qsim.sims.exact_sim import ExactSim
from pyjarowinkler import distance as pyjarodist
import pathos.multiprocessing as mp
import time
import numpy as np


class JaroSim(ExactSim):
    def __init__(self, cols=None, debug=False, lower=True, stem=True, rem_stopwords=True, only_alphanum=True, parallel=False):
        super().__init__(cols, debug, lower, stem, rem_stopwords, only_alphanum)

        self._parallel=parallel

    def _get_text_sim(self, x, y):
        x = self._preprocess_text(x)
        y = self._preprocess_text(y)

        return self._compute(x, y)

    def _compute(self, x, y):
        return pyjarodist.get_jaro_distance(x, y, winkler=True, scaling=0.1)

    def _get_similarity_matrix(self, df):
        proc_array = self._preprocess_df(df)

        n = len(proc_array)
        relevant_pairs = [(x, y) for x in range(n) for y in range(x)]

        t = time.time()
        results = self._get_similarity_matrix_parallel(proc_array, relevant_pairs) if self._parallel \
            else self._get_similarity_matrix_serial(proc_array, relevant_pairs)
        self._lg.debug('Took {} sec'.format(time.time() - t))

        # now reconstruct matrix
        rows = []
        offset = 0
        for i in range(n):
            row = results[offset:offset + i] + [1] + [0] * (n - i - 1)
            rows.append(row)
            offset += i

        sm = np.array(rows)
        for i in range(n):
            sm[i, i + 1:] = sm[i + 1:, i]

        return sm

    def _get_similarity_matrix_serial(self, proc_array, relevant_pairs):
        CHUNK_COUNT = 5000
        results = []

        for i, p in enumerate(relevant_pairs):
            if i % CHUNK_COUNT == 0:
                self._lg.debug('{}/{}'.format(i, len(relevant_pairs)))
            results.append(self._compute(proc_array[p[0]], proc_array[p[1]]))

        return results

    def _get_similarity_matrix_parallel(self, proc_array, relevant_pairs):
        CHUNK_COUNT = 5000

        with mp.Pool(32) as pool:
            results = []

            for i in range(0, len(relevant_pairs), CHUNK_COUNT):
                self._lg.debug('{}/{}'.format(i, len(relevant_pairs)))
                chunk = relevant_pairs[i:i + CHUNK_COUNT]
                chunk_results = list(pool.map(lambda p: self._compute(proc_array[p[0]], proc_array[p[1]]), chunk))

                results.extend(chunk_results)

        return results

if __name__ == '__main__':
    df = load_clean_df().iloc[:100]
    sm = JaroSim(debug=True, parallel=False).get_similarity_matrix(df)
    print(sm)
