"""
In this module we can train word vector models, open pre-trained models to extract relevant word vectors, and save
all relevant info in pickled objects
"""

from helpers.common import *

import logging
import gensim as gs
import qsim.qsim_common as qsim
from qsim.qsim_common import W2vModelName
from qsim.sims.sent_vec_sim import SentVecSim

import nltk
from gensim.models import word2vec


PROCESSED_COLS = ['all_text', 'all_context', 'all_inclusions', 'all_exclusions', 'notes']
QBANK_TRAINED_MODEL_FPATH = CHECKPT_DIR + '/w2v.model'


def get_sentences():
    df = load_clean_df()
    sentences = qsim.create_sentences(df, PROCESSED_COLS)

    return sentences


def train_w2v():
    sentences = get_sentences()

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    num_features = 300    # Word vector dimensionality
    min_word_count = 30   # Minimum word count
    num_workers = 4       # Number of threads to run in parallel
    context = 7           # Context window size
    downsampling = 1e-3   # Downsample setting for frequent words

    model = word2vec.Word2Vec(
        sentences,
        workers=num_workers,
        size=num_features,
        min_count = min_word_count,
        window = context,
        sample = downsampling
    )

    # If you don't plan to train the model any further, calling
    # init_sims will make the model much more memory-efficient.
    model.init_sims(replace=True)
    model.save(QBANK_TRAINED_MODEL_FPATH)


def _load_w2v_keyed_vectors(model_name):
    if model_name == W2vModelName.PretrainedGoogleNews:
        return gs.models.KeyedVectors.load_word2vec_format(DATA_DIR + '/pretrained-w2v/GoogleNews-vectors-negative300.bin', binary=True)

    if model_name == W2vModelName.QbankTrained:
        return gs.models.Word2Vec.load(QBANK_TRAINED_MODEL_FPATH).wv


def create_and_pickle_word_frequencies():
    print('creating word frequencies...')
    sentences = get_sentences()

    fd = nltk.FreqDist([w for s in sentences for w in s])

    word_freq_dict = dict(fd.items())
    qsim.pickle_word_frequencies(word_freq_dict)


def get_and_pickle_word_vectors(model_name):
    print('getting word vectors for {}...'.format(model_name))
    model = _load_w2v_keyed_vectors(model_name)

    sentences = get_sentences()

    vocab = set(w for s in sentences for w in s)

    wv_dict = {}
    for v in vocab:
        if v not in model:
            continue
        wv_dict[v] = model[v]

    qsim.pickle_word_vectors(wv_dict, model_name)


def get_and_pickle_1st_pc(sent_vec_sim, model_name, rem_stopwords):
    print('getting 1st PC - {}/{}...'.format(model_name, rem_stopwords))
    df = load_clean_df()

    first_pc = sent_vec_sim.get_first_pc(df)
    qsim.pickle_1st_pc(first_pc, model_name, rem_stopwords)


if __name__ == '__main__':
    # train_w2v()
    #
    # create_and_pickle_word_frequencies()

    # get_and_pickle_word_vectors(W2vModelName.PretrainedGoogleNews)
    # get_and_pickle_word_vectors(W2vModelName.QbankTrained)

    for model_name in W2vModelName:
        for rem_stopwords in [True, False]:
            sim = SentVecSim(wv_dict_model_name=model_name, rem_stopwords=rem_stopwords, first_pc_model_name=None)
            get_and_pickle_1st_pc(sim, model_name, rem_stopwords)
