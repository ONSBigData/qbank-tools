import bokeh.palettes as palettes
from bokeh.models import Div
import numpy as np
import helpers.bokeh_helper as bh
from bs4 import BeautifulSoup
from siman.sims.tfidf_cos import TfidfCosSim
import random
import siman.qsim as qsim
import pandas as pd
import re

COMP_TBL_FIELDS = ['question X', 'question Y', 'similarity']
SIM_MARKER = '___SIM___'
DEF_DISPLAYED_COLS = ['uuid', 'survey_id', 'survey_name', 'form_type', 'tr_code', 'suff_qtext', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']


# --- Question comparisons -----------------------------------------------------------


def get_sample_comp_questions(
        sample_df,
        sim_matrix,
        cs_only=False,
        min_val=0,
        max_val=1,
        count=3):

    cs_matrix = qsim.get_cross_survey_matrix(sample_df) if cs_only else np.full(sim_matrix.shape, True)
    not_itself_matrix = ~np.identity(len(sim_matrix), bool)

    candidates = np.where(
        (not_itself_matrix) &
        (cs_matrix) &
        (min_val <= sim_matrix) &
        (sim_matrix <= max_val)
    )

    candidates = list(zip(list(candidates[0]), list(candidates[1])))

    if len(candidates) > count:
        candidates = random.sample(candidates, count)

    q_pairs = []
    for candidate in candidates:
        qx = sample_df.iloc[candidate[0]]
        qy = sample_df.iloc[candidate[1]]
        qx.loc['uuid'] = qx.name
        qy.loc['uuid'] = qy.name

        q_pairs.append({
            'qx': qx,
            'qy': qy,
            'similarity': sim_matrix[candidate[0], candidate[1]]
        })

    return q_pairs


def get_sample_comp_questions_spectrum(
        df,
        sim,
        cs_only=False,
        start=0,
        end=1,
        buckets=5,
        sample=250,
        bucket_size=3):
    sdf = df.sample(sample)
    sim_matrix = sim.get_similarity_matrix(sdf)

    edges = np.linspace(start, end, buckets + 1)
    buckets = zip(edges[:-1], edges[1:])

    q_pairs = []
    for bucket in buckets:
        q_pairs.extend(get_sample_comp_questions(
            sdf, sim_matrix, cs_only, bucket[0], bucket[1], bucket_size))

    return q_pairs


def get_sample_comp_df(sim, q_pair, displayed_cols=None, sim_cols=None, inc_sim_marker=False):
    qx, qy = q_pair['qx'], q_pair['qy']

    if displayed_cols is None:
        displayed_cols = qx.index

    if sim_cols is None:
        sim_cols = displayed_cols

    col2doc_sim = [(c, sim.get_text_sim) for c in sim_cols]

    comp_df = create_comp_df(
        qx, qy,
        displayed_cols=displayed_cols,
        col2doc_sim=dict(col2doc_sim),
        inc_sim_marker=inc_sim_marker
    )

    return comp_df


def get_comp_div(comp_df, palette=bh.DEF_PALETTE, width=bh.DEF_WIDTH):
    if comp_df is None:
        return Div(text='')

    pd.set_option('display.max_colwidth', -1)

    FONT_COLOR_PALETTE = palettes.Greys256

    soup = BeautifulSoup(comp_df.to_html(), 'html5lib')
    for td in soup.find_all('td', text=re.compile('{}.*'.format(SIM_MARKER))):
        sim = float(td.text.replace(SIM_MARKER, ''))
        bg_color = palette[int(sim * (len(palette) - 1))]
        color = FONT_COLOR_PALETTE[int((1 - sim) * (len(FONT_COLOR_PALETTE) - 1))]
        td.attrs['style'] = 'background-color: {}; color: {}'.format(bg_color, color)
        td.string = '{:0.3f}'.format(sim)

    comp_div = Div(text=str(soup), width=width)

    return comp_div


def create_comp_df(qx, qy, displayed_cols=None, col2doc_sim=None, inc_sim_marker=False):
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
        sim = TfidfCosSim()
        col2doc_sim = dict((c, sim.get_text_sim) for c in displayed_cols)

    sim_col = pd.Series([''] * len(qx), index=qx.index)

    for c in col2doc_sim:
        similarity = col2doc_sim[c](str(qx.loc[c]), str(qy.loc[c]))
        if similarity is not None:
            sim_col.loc[c] = '{}{:0.3f}'.format(SIM_MARKER, similarity)

    df = pd.concat([qx, qy, sim_col], axis=1, ignore_index=True)
    df.columns = COMP_TBL_FIELDS

    return df


def get_comp_divs(df, sim, displayed_cols=DEF_DISPLAYED_COLS, sim_cols=None, **spectrum_kwargs):
    q_pairs = get_sample_comp_questions_spectrum(df, sim, **spectrum_kwargs)

    comp_divs = []

    for q_pair in q_pairs:
        comp_df = get_sample_comp_df(sim, q_pair, displayed_cols=displayed_cols, sim_cols=sim_cols, inc_sim_marker=True)
        comp_div = get_comp_div(comp_df)
        comp_divs.append(comp_div)

    return comp_divs


# --- Heatmap -----------------------------------------------------------


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


# --- Histogram -----------------------------------------------------------


def get_sim_hist(df, sim, sample_size=500, cs_only=False, bins=15, **kwargs):
    sdf = df
    if sample_size is not None:
        sdf = sdf.sample(sample_size)
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


if __name__ == '__main__':
    from helpers.common import *

    df = load_clean_df()
    COLS = ['suff_qtext', 'type']
    sim = TfidfCosSim(cols=COLS)
    q_pairs = get_sample_comp_questions_spectrum(df, sim)
    comp_df = get_sample_comp_df(sim, q_pairs[0], sim_cols=COLS)
    print(comp_df)