from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from pyjarowinkler import distance as pyjarodist
import pandas as pd
import re
import utilities.json2df.dataframing as dataframing
import nltk
from gensim.models import Phrases


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


def get_cos_doc_sim(x, y):
    if pd.isnull(x) or pd.isnull(y):
        return 0

    vect = TfidfVectorizer()
    tfidf = vect.fit_transform([x, y])
    return (tfidf * tfidf.T).A[0, 1]


def get_exact_doc_sim(x, y):
    if pd.isnull(x) or pd.isnull(y):
        return 0

    return 1 if x == y else 0


def get_jaro_doc_sim(x, y):
    if pd.isnull(x) or pd.isnull(y):
        return 0

    return pyjarodist.get_jaro_distance(x, y, winkler=True, scaling=0.1)
