from nltk.corpus import stopwords
import pandas as pd
import re
import utilities.json2df.dataframing as dataframing
import nltk
from gensim.models import Phrases
import numpy as np


def get_stop_words():
    sws = set(stopwords.words('english'))
    for x in ['survey', 'section', 'business', 'period', 'total', 'service', 'services']:
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
