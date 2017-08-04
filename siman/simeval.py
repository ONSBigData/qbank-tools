import bokeh.palettes as palettes
from bokeh.models import Div, LinearColorMapper
import numpy as np
import helpers.bokeh_helper as bh
from bs4 import BeautifulSoup
import random
import siman.qsim as qsim
import pandas as pd
import re
from siman.sims.tfidf_cos import TfidfCosSim


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
        qx = sample_df.iloc[candidate[0]].copy()
        qy = sample_df.iloc[candidate[1]].copy()
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
    sdf = df.copy()
    if sample < len(sdf):
        sdf = df.sample(sample)
    sim_matrix = sim.get_similarity_matrix(sdf)

    edges = np.linspace(start, end, buckets + 1)
    buckets = zip(edges[:-1], edges[1:])

    q_pairs = []
    for bucket in buckets:
        q_pairs.extend(get_sample_comp_questions(
            sdf, sim_matrix, cs_only, bucket[0], bucket[1], bucket_size))

    return q_pairs


def get_sample_comp_df(sim, q_pair, displayed_cols=None, sim_cols=None):
    qx, qy = q_pair['qx'], q_pair['qy']

    if displayed_cols is None:
        displayed_cols = qx.index

    if sim_cols is None:
        sim_cols = displayed_cols

    col2doc_sim = [(c, sim.get_text_sim) for c in sim_cols]

    comp_df = create_comp_df(
        qx, qy,
        displayed_cols=displayed_cols,
        col2doc_sim=dict(col2doc_sim)
    )

    comp_df.meta = q_pair

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

    html = str(soup)

    if hasattr(comp_df, 'meta'):
        similarity = comp_df.meta['similarity']
        html = '<h3>Similarity: {:0.3f}</h3>'.format(similarity) + html

    comp_div = Div(text=html, width=width)

    return comp_div


def create_comp_df(qx, qy, displayed_cols=None, col2doc_sim=None, def_sim=TfidfCosSim()):
    def _create_series(q):
        q['uuid'] = q.name

        q = pd.Series([q[c] if c in q else 'none' for c in displayed_cols], index=displayed_cols)

        return q

    if displayed_cols is None:
        displayed_cols = ['uuid'] + list(qx.index)

    qx = _create_series(qx)
    qy = _create_series(qy)

    if col2doc_sim is None:
        col2doc_sim = dict((c, def_sim.get_text_sim) for c in displayed_cols)

    sim_col = pd.Series([''] * len(qx), index=qx.index)

    for c in col2doc_sim:
        similarity = col2doc_sim[c](str(qx.loc[c]), str(qy.loc[c]))
        if similarity is not None:
            sim_col.loc[c] = '{}{:0.3f}'.format(SIM_MARKER, similarity)

    df = pd.concat([qx, qy, sim_col], axis=1, ignore_index=True)
    df.columns = COMP_TBL_FIELDS

    return df


def get_comp_divs(df, sim, displayed_cols=DEF_DISPLAYED_COLS, sim_cols=None, width=bh.DEF_WIDTH, **spectrum_kwargs):
    q_pairs = get_sample_comp_questions_spectrum(df, sim, **spectrum_kwargs)

    comp_divs = []

    for q_pair in q_pairs:
        comp_df = get_sample_comp_df(sim, q_pair, displayed_cols=displayed_cols, sim_cols=sim_cols)
        comp_div = get_comp_div(comp_df, width=width)
        comp_divs.append(comp_div)

    return comp_divs


# --- Heatmap of similarities -----------------------------------------------------------


def get_sim_heatmap(df, sim, sample_size=30, cs_only=False, **kwargs):
    sdf = df.copy()
    if sample_size < len(sdf):
        sdf = df.sample(sample_size)
    sim_matrix = sim.get_similarity_matrix(sdf, cs_only=cs_only)

    hm_df = bh.get_heatmap_df(sdf, sim_matrix)

    title = '{} scores heatmap'.format(sim.__class__.__name__)
    if cs_only:
        title += ' (0 for non-CS pairs)'

    hm = bh.get_heatmap(
        hm_df,
        'uuid_x',
        'uuid_y',
        title=title,
        **kwargs
    )

    return hm


# --- Bar chart of most similar -----------------------------------------------------------


def get_sim_bar_chart_df(df, sim, bars=10, sample_size=50, cs_only=False):
    sdf = df.copy()
    if sample_size < len(sdf):
        sdf = df.sample(sample_size)

    sim_matrix = sim.get_similarity_matrix(sdf, cs_only=cs_only)
    n = sim_matrix.shape[0]

    top_indices = [(i // n, i % n) for i in sim_matrix.argsort(axis=None)][::-1]

    sdf = sdf.reset_index()

    rows = []
    for ti in top_indices[:bars]:
        row = pd.Series()

        def _get_q(index, xy):
            q = sdf.iloc[index]
            q.index = ['{}_{}'.format(i, xy) for i in q.index]
            return q

        row = row.append(_get_q(ti[0], 'x'))
        row = row.append(_get_q(ti[1], 'y'))
        row['similarity'] = sim_matrix[ti[0], ti[1]]
        rows.append(row)

    bc_df = pd.DataFrame(rows)
    if cs_only:
        bc_df = bc_df[bc_df.apply(lambda row: row['survey_id_x'] != row['survey_id_y'], axis=1)]

    return bc_df


def get_sim_bar_chart(df, sim, bars=10, sample_size=50, cs_only=False, palette=bh.DEF_PALETTE, **kwargs):
    mapper = LinearColorMapper(palette=palette, low=0, high=1)

    bc_df = get_sim_bar_chart_df(df, sim, bars, sample_size, cs_only)
    if len(bc_df) > 0:
        bc_df['q_pair'] = bc_df.apply(lambda row: '{} - {}'.format(row['uuid_x'], row['uuid_y']), axis=1)

    title = 'Top question pairs by {} scores on sample '.format(sim.__class__.__name__)
    if cs_only:
        title += ' (CS only)'

    bc = bh.get_bar_chart(
        bc_df,
        'q_pair',
        'similarity',
        title=title,
        color={'field': 'similarity', 'transform': mapper},
        **kwargs
    )

    return bc


# --- Histogram of similarities -----------------------------------------------------------


def get_sim_hist(df, sim, sample_size=500, cs_only=False, bins=15, **kwargs):
    sdf = df
    if sample_size is not None:
        if sample_size < len(sdf):
            sdf = df.sample(sample_size)
    sim_matrix = sim.get_similarity_matrix(sdf, cs_only=cs_only)

    title = '{} scores prob. density'.format(sim.__class__.__name__)
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
    bc_df = get_sim_bar_chart_df(df, sim)
    print(bc_df.columns)

    # q_pairs = get_sample_comp_questions_spectrum(df, sim)
    # comp_df = get_sample_comp_df(sim, q_pairs[0], sim_cols=COLS)
    # print(comp_df)