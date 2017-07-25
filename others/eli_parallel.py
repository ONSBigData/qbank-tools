import sys
sys.path.append('/home/ons21553/wspace/dstools')

from helpers.common import *
import pandas as pd
import multiprocessing as mp
from pyjarowinkler import distance as ds
import time
import numpy as np

df = pd.read_csv(DATA_DIR + '/../data/cleanInfoJune23.csv')
df.columns = [c.lower() for c in df.columns]

text = df['text'][:100]
n = len(text)
print('n = {}'.format(n))

all_pos = [(x, y) for x in range(n) for y in range(n)]

def similarity(p):
    x, y = p

    if x < y:
        return 0

    return ds.get_jaro_distance(text[x], text[y], winkler=True, scaling=0.1)





print('computing...')
t = time.time()
with mp.Pool(32) as pool:
    res = []

    CHUNK_COUNT = 5000

    for i in range(0, len(all_pos), CHUNK_COUNT):
        print('{}/{}'.format(i, len(all_pos)))
        chunk_pos = all_pos[i:i + CHUNK_COUNT]

        chunk_res = list(pool.map(similarity, chunk_pos))
        # chunk_res = list(map(similarity, chunk_pos))

        res.extend(chunk_res)

print('took {} sec'.format(time.time() - t))

matrix = np.array(res).reshape(n, n)

print(matrix)





t = time.time()
print('computing vectorized...')

def sim(t1, t2):
    return ds.get_jaro_distance(t1, t2, winkler=True, scaling=0.1)

vsim = np.vectorize(sim)

A = np.tile(text, n).reshape(n, n)
G = vsim(A, A.T)

print('took {} sec'.format(time.time() - t))
print(G)


print(G == matrix)
#
# sns.set(context="paper", font="monospace")
#
# # Set up the matplotlib figure
# f, ax = plt.subplots(figsize=(12, 9))
#
# # Draw the heatmap using seaborn
# sns.heatmap(matrix, vmax=1, square=True)
#
# plt.xticks()
# vst.sparsify_tick_labels(plt.gca(), rough_limit=10)
#
# plt.show()
