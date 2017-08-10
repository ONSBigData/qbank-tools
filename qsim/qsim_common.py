from support.dl_nltk import dl_nltk
dl_nltk()


from nltk.corpus import stopwords
from support.common import *
import pandas as pd
import re
import json2df.dataframing as dataframing
import nltk
from gensim.models import Phrases
import numpy as np
from enum import Enum


class W2vModelName(Enum):
    PretrainedGoogleNews = 1
    QbankTrained = 2


DEF_WF_DICT_NAME = 'wf.dict'


# --- pickling -----------------------------------------------------------


def _get_wf_dict_pickle_name(name):
    return 'wf.{}.dict'.format(name)


def pickle_word_frequencies(wf_dict, name=DEF_WF_DICT_NAME):
    save_pickled_obj(wf_dict, _get_wf_dict_pickle_name(name))


def load_word_frequencies_dict(name=DEF_WF_DICT_NAME):
    return load_pickled_obj(_get_wf_dict_pickle_name(name))


def _get_wv_dict_pickle_name(model_name):
    return 'wv.{}.dict'.format(model_name.name)


def pickle_word_vectors(wv_dict, model_name):
    save_pickled_obj(wv_dict, _get_wv_dict_pickle_name(model_name))


def load_word_vectors(model_name):
    return load_pickled_obj(_get_wv_dict_pickle_name(model_name))


def _get_1st_pc_pickle_name(model_name, rem_stopwords):
    return '1pc.{}.{}'.format(model_name.name, 'exc-stop' if rem_stopwords else 'inc-stop')


def pickle_1st_pc(first_pc, model_name, rem_stopwords):
    save_pickled_obj(first_pc, _get_1st_pc_pickle_name(model_name, rem_stopwords))


def load_1st_pc(model_name, rem_stopwords):
    return load_pickled_obj(_get_1st_pc_pickle_name(model_name, rem_stopwords))


# --- other helper functions -----------------------------------------------------------

def get_stop_words():
    sws = set(stopwords.words('english'))
    for x in [
        'segment',
        'inclusions',
        'exclusions',
        'text',
        'id',
        'context',
        'survey',
        'section',
        'business',
        'period',
        'total',
        'service',
        'services'
    ]:
        sws.add(x)

    return sws


def text2sents(text):
    SEPS = [dataframing.MINOR_SEP, dataframing.MAJOR_SEP, dataframing.NOTES_SEP]

    pattern = '|'.join([re.escape(sep) for sep in SEPS])
    split = re.split(pattern, text)

    sents = []
    for part in split:
        sents.extend(nltk.tokenize.sent_tokenize(part))

    return sents


def sent2words(sent):
    sent = sent.lower()

    sent = re.sub(' v?i{1,2}\)| i?v\)| i?x\)', ' ', sent)

    sent = re.sub('[^a-zA-Z]', ' ', sent)
    words = sent.lower().split()

    return words


def exp_scale(X, base=10):
    """Scales the values in X (0-1) to a new scale 0-1. If base > 1, values < 1 are reduced as their distance from 1 increases

    X = np.linspace(0, 1, 20)
    base = 10
    plt.plot(X, (base**X - 1)/(base - 1), show)
    plt.grid()
    """

    return (base**X - 1) / (base - 1)


def create_sentences(df, cols):
    sentences = []

    for _, row in df.iterrows():
        for col in cols:
            if pd.isnull(row[col]):
                continue
            sents = text2sents(row[col])
            for sent in sents:
                words = sent2words(sent)
                sentences.append(words)

    return sentences


def detect_phrases(sents, max_length=5, **kwargs):
    if max_length <= 1:
        return list(sents)

    phrases = Phrases(sents, **kwargs)
    return detect_phrases(list(phrases[sents]), max_length - 1, **kwargs)


def get_cross_survey_matrix(df):
    sur_ids = np.array(df['survey_id'])
    n = len(df)

    S = np.repeat(sur_ids, n).reshape(n, n)
    cross_survey_matrix = ~(S == S.T)

    return cross_survey_matrix


