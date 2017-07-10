import multiprocessing as mp

import numpy as np


S = np.random.rand(3, 3)
print(S)

def calc(pair):
    x, y = pair

    return S[x, y]  #similarity(x, y)

all_positions = [(x, y) for x in range(3) for y in range(0, x + 1)]

with mp.Pool(4) as pool:
    res = pool.map(calc, all_positions)

    print(np.array(res).reshape(3, 3))