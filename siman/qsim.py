from nltk.corpus import stopwords
import bokeh.palettes as palettes
from sklearn.feature_extraction.text import TfidfVectorizer
from pyjarowinkler import distance as pyjarodist
import pandas as pd
import re
import utilities.json2df.dataframing as dataframing
import nltk
from gensim.models import Phrases
import numpy as np
import helpers.bokeh_helper as bh
from bs4 import BeautifulSoup


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


# ---------------------------------------------------------------------
# --- Eval similarities
# ---------------------------------------------------------------------


COMP_TBL_FIELDS = ['question X', 'question Y', 'similarity']
SIM_MARKER = '___SIM___'


def get_comp_div(comp_df, palette=bh.DEF_PALETTE, width=bh.DEF_WIDTH):
    if comp_df is None:
        return bh.Div(text='')

    pd.set_option('display.max_colwidth', -1)

    FONT_COLOR_PALETTE = palettes.Greys256

    soup = BeautifulSoup(comp_df.to_html(), 'html5lib')
    for td in soup.find_all('td', text=re.compile('{}.*'.format(SIM_MARKER))):
        sim = float(td.text.replace(SIM_MARKER, ''))
        bg_color = palette[int(sim*(len(palette) - 1))]
        color = FONT_COLOR_PALETTE[int((1 - sim) * (len(FONT_COLOR_PALETTE) - 1))]
        td.attrs['style'] = 'background-color: {}; color: {}'.format(bg_color, color)
        td.string = '{:0.3f}'.format(sim)

    comp_div = bh.Div(text=str(soup), width=width)

    return comp_div


def create_comp_df(qx, qy, displayed_cols=None, col2doc_sim=None):
    def _create_series(q):
        if q is None:
            q = pd.Series()

        q = pd.Series([q[c] if c in q else 'none' for c in displayed_cols], index=displayed_cols)

        return q

    if displayed_cols is None:
        displayed_cols = qx.index

    qx = _create_series(qx)
    qy = _create_series(qy)

    if col2doc_sim is None:
        col2doc_sim = dict((c, get_cos_doc_sim) for c in displayed_cols)

    sim_col = pd.Series(['']*len(qx), index=qx.index)

    for c in col2doc_sim:
        similarity = col2doc_sim[c](str(qx.loc[c]), str(qy.loc[c]))
        if similarity is not None:
            sim_col.loc[c] = '{}{:0.3f}'.format(SIM_MARKER, similarity)

    df = pd.concat([qx, qy, sim_col], axis=1, ignore_index=True)
    df.columns = COMP_TBL_FIELDS

    return df


def get_cross_survey_matrix(df):
    sur_ids = np.array(df['survey_id'])
    n = len(df)

    S = np.repeat(sur_ids, n).reshape(n, n)
    cross_survey_matrix = ~(S == S.T)

    return cross_survey_matrix


def get_sim_heatmap(df, sim, sample_size=30, cs_only=False, **kwargs):
    sdf = df.sample(sample_size)
    sim_matrix = sim.get_similarity_matrix(sdf, cs_only=cs_only)

    hm_df = bh.get_heatmap_df(sdf, sim_matrix)

    title = 'Similarity scores heatmap'
    if cs_only:
        title += ' (CS only)'

    hm = bh.get_heatmap(
        hm_df,
        'uuid_x',
        'uuid_y',
        title=title,
        **kwargs
    )

    return hm


def get_sim_hist(df, sim, sample_size=500, cs_only=False, bins=15, **kwargs):
    if sample_size is not None:
        sdf = df.sample(sample_size)
    sim_matrix = sim.get_similarity_matrix(sdf, cs_only=cs_only)

    title = 'Similarity scores prob. density'
    if cs_only:
        title += ' (CS only)'

    return bh.get_hist(
        sim_matrix.flatten(),
        bins=bins,
        title=title,
        plot_height=300,
        **kwargs
    )