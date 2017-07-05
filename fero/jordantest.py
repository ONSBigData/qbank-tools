from functools import reduce
import operator
import os
import copy
from sys import argv
import csv
import json
import re
from datetime import date
from datetime import datetime
import numpy as np
import pandas as pd
from glob import glob


import nltk

# nltk.download()


fullInfo = pd.read_csv('../data/cleanInfoJune23.csv')

from nltk.corpus import stopwords

cachedStopWords = stopwords.words("english")

text = fullInfo['TEXT'][3]

text = ' '.join([word for word in text.split() if word not in cachedStopWords])


def removeStopWords(tempText):
    text = ' '.join([word for word in tempText.split() if word not in cachedStopWords])
    return text


strippedText = []

for x in fullInfo['TEXT']:
    strippedText.append(removeStopWords(x))

fullInfo['stoppedText'] = strippedText


# trying to create jaccard similarity
# Jaccard similarity coefficient is a similarity measure that compares the similarity
# between two feature sets. When applying to sentence similarity task, it is defined as
# the size of the intersection of the words in the two sentences compared to the size of
# the union of the words in the two sentences.

def jaccard(a, b):
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


import numpy

fullMatrix = numpy.zeros((len(strippedText), len(strippedText)))

for x in range(0, len(strippedText) - 0):
    for y in range(0, len(strippedText) - 0):
        first = strippedText[x]
        second = strippedText[y]
        firstWordSet = set(first.split())
        secondWordSet = set(second.split())
        fullMatrix[x, y] = jaccard(firstWordSet, secondWordSet)

import networkx as nx
from matplotlib import pyplot, patches


def draw_adjacency_matrix(G, node_order=None, partitions=[], colors=[]):
    """
    - G is a networkx graph
    - node_order (optional) is a list of nodes, where each node in G
          appears exactly once
    - partitions is a list of node lists, where each node in G appears
          in exactly one node list
    - colors is a list of strings indicating what color each
          partition should be
    If partitions is specified, the same number of colors needs to be
    specified.
    """
    adjacency_matrix = nx.to_numpy_matrix(G, dtype=np.bool, nodelist=node_order)

    # Plot adjacency matrix in toned-down black and white
    fig = pyplot.figure(figsize=(5, 5))  # in inches
    pyplot.imshow(adjacency_matrix,
                  cmap="Greys",
                  interpolation="none")

    # The rest is just if you have sorted nodes by a partition and want to
    # highlight the module boundaries
    assert len(partitions) == len(colors)
    ax = pyplot.gca()
    for partition, color in zip(partitions, colors):
        current_idx = 0
        for module in partition:
            ax.add_patch(patches.Rectangle((current_idx, current_idx),
                                           len(module),  # Width
                                           len(module),  # Height
                                           facecolor="none",
                                           edgecolor=color,
                                           linewidth="1"))
            current_idx += len(module)


from scipy import io

A = numpy.matrix(fullMatrix)
G = nx.from_numpy_matrix(A)

draw_adjacency_matrix(G)