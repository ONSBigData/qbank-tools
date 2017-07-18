
# coding: utf-8

# In[1]:


import sys
sys.path.append('/home/ons21553/wspace/dstools')
sys.path.append('/home/ons21553/wspace/qbank/code')
from dstools import *

from common import *

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import gensim as gs
import numpy as np

jnt.setup_rcparams()


import logging
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


# In[3]:


import nltk
from nltk.corpus import stopwords
import re
from six import iteritems
import pyLDAvis.gensim


df = load_clean_df()
df.shape


sdf = df.groupby('survey_id').agg({
        'all_text': lambda g: ' '.join(g),
        'survey_name': lambda g: g.iloc[0]
    })

data = sdf.all_text


# ##### pre-process

sws = set(stopwords.words('english'))
for x in ['survey', 'section', 'business', 'period', 'total', 'service', 'services']:
    sws.add(x)
stemmer = nltk.PorterStemmer()


def preprocess(item):
    # lower case
    item = item.lower()
    
    # remove undesired chars
    item = re.sub(r"[^a-zA-Z0-9]", " ", item)
    
    # tokenize
    words = nltk.word_tokenize(item)
    
    # remove stop-words
    words = [w for w in words if w not in sws]
    
    # remove one-letter words
    words = [w for w in words if len(w) > 1]
    
    # stem
#     words = [stemmer.stem(t) for t in words]
    
    return words

pdata = []
for x in data:
    proc = preprocess(x)
    pdata.append(proc)


# #### Dictionary

dictionary = gs.corpora.Dictionary(pdata)

once_ids = [tokenid for tokenid, docfreq in iteritems(dictionary.dfs) if docfreq == 1]

dictionary.filter_tokens(once_ids)
dictionary.compactify()

print(dictionary)

# #### LDA

corpus = [dictionary.doc2bow(x) for x in pdata]

tfidf = gs.models.TfidfModel(corpus)

lda = gs.models.LdaModel(corpus, id2word=dictionary, num_topics=10)


index = gs.similarities.MatrixSimilarity(lda[corpus])

for i, topics in enumerate(lda[corpus]):
    print('{} - {}\n\t{}'.format(sdf.index[i], sdf.iloc[i]['survey_name'], topics))

index.save(CHECKPT_DIR + '/survey-lda-model.index')


matrix = np.array(index)

# f, axs = plt.subplots(1, 2, figsize=(12, 7), gridspec_kw={'width_ratios':[5,2]})
#
# plt.sca(axs[0])
#
# sns.heatmap(matrix, vmax=1, square=True)
#
# axs[1].axis('off')
#
# plt.xticks(np.arange(data.size) + 0.5, data.index, rotation=90, )
# plt.yticks(np.arange(data.size) + 0.5, reversed(data.index), rotation=0)
# plt.gca().xaxis.tick_top()
#
#
# topics = lda.show_topics()
# text = None
# import textwrap
#
# def on_plot_hover(event):
#     global text
#
#     x = int(event.xdata)
#     y = len(data)-int(event.ydata) - 1
#
#     if text is not None:
#         text.remove()
#
#     def get_topics_text(assignments):
#         a_texts = []
#         for a in assignments[:5]:
#             words = '\n'.join(textwrap.wrap(topics[a[0]][1][:100], 40, subsequent_indent=' '*4))
#             a_texts.append('  {:0.2f} of topic {}\n    {}...'.format(a[1], a[0], words))
#
#         return '\n'.join(a_texts)
#
#     def get_text(i):
#         survey_name = '\n'.join(textwrap.wrap(sdf.iloc[i]['survey_name'], 40, subsequent_indent=' '*4))
#         return '{} - {}\n{}'.format(sdf.index[i], survey_name, get_topics_text(lda[corpus][i]))
#
#     similarity = matrix[x, y]
#
#     s = 'Topic similarity {:0.3f}\n\n{}\n\n{}'.format(similarity, get_text(x), get_text(y))
#
#     text = axs[1].text(0, 0, s)
#
#
# f.canvas.mpl_connect('button_press_event', on_plot_hover)
# f.subplots_adjust(bottom=0.2)


from bokeh.charts import HeatMap, show, output_file
import pandas as pd, numpy as np

# Normalize the data columns and sort.

data = {
  'x': list(sdf.index) * sdf.size,
  'y':  list(sdf.index) * sdf.size,
  'score': matrix,
}

hm = HeatMap(data, x='x', y='y', values='score', title='Fruits', stat=None)
show(hm)