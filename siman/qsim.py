from utilities.dl_nltk import dl_nltk
dl_nltk()

from nltk.corpus import stopwords

from sklearn.feature_extraction.text import TfidfVectorizer
from pyjarowinkler import distance as pyjarodist
import pandas as pd


def get_stop_words():
    sws = set(stopwords.words('english'))
    for x in ['survey', 'section', 'business', 'period', 'total', 'service', 'services']:
        sws.add(x)

    return sws


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
