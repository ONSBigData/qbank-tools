import bokeh.palettes as palettes
import pandas as pd
from bokeh.models import \
    ColumnDataSource, \
    HoverTool, \
    Div, \
    Range1d, \
    FuncTickFormatter, \
    LinearColorMapper, \
    ColorBar, \
    BasicTicker, \
    PrintfTickFormatter, \
    CustomJS
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.plotting import figure
import numpy as np
import siman.qsim as qsim
from bs4 import BeautifulSoup
import re

DEF_PALETTE = palettes.Magma256
DEF_WIDTH = 600

# ---------------------------------------------------------------------
# --- General
# ---------------------------------------------------------------------

def format_tooltip_fields(tooltip_fields, css_class=None):
    style = 'style="white-space: pre-wrap; width:250px"' if css_class is None else 'class="{}"'.format(css_class)
    tooltip_fields = [(tf[0], '<div {}>{}</div>'.format(style, tf[1])) for tf in tooltip_fields]

    return tooltip_fields


def get_tooltip_fields(columns):
    tooltip_fields = []

    for col in columns:
        col_title = col.replace('_', ' ').title()
        tooltip_fields.append((col_title, '@{}'.format(col)))

    return tooltip_fields


def get_bar_chart(
        df,
        x_field,
        y_field,
        color_field=None,
        tooltip_fields=None,
        width=DEF_WIDTH,
        title=None,
        js_on_event=None):

    if tooltip_fields is None:
        tooltip_fields = get_tooltip_fields(df.columns)

    hover = HoverTool(tooltips=format_tooltip_fields(tooltip_fields))

    bc = figure(
        plot_width=width,
        toolbar_location=None,
        tools=[hover],
        title=title,
        y_range=Range1d(0, 1)
    )

    df = df.copy()
    INDEX = '__index__'
    df[INDEX] = range(len(df))
    src = ColumnDataSource(df)

    bc.vbar(
        x=INDEX,
        top=y_field,
        bottom=0,
        width=0.5,
        fill_color=color_field,
        source=src
    )

    bc.xaxis[0].ticker.desired_num_ticks = len(df)
    bc.yaxis.axis_label = y_field
    bc.xaxis.axis_label = x_field
    bc.xaxis.major_label_orientation = 1

    labels = dict([(i, df.iloc[i][x_field]) for i in range(len(df))])
    bc.xaxis.formatter = FuncTickFormatter(code="""var labels = {}; return labels[tick]; """.format(labels))

    if js_on_event is not None:
        bc.js_on_event(js_on_event[0], js_on_event[1])

    return bc


def get_heatmap_df(base_df, matrix, value_name='value'):
    vdf = pd.DataFrame(matrix.flatten(), columns=[value_name])

    xdf = base_df.reset_index()
    xdf = pd.concat([xdf] * len(base_df))
    xdf.index = range(len(xdf))

    ydf = base_df.reset_index()
    ydf = ydf.loc[np.repeat(ydf.index.values, len(base_df))]
    ydf.index = range(len(ydf))

    hm_df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
    hm_df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + [value_name]

    return hm_df


def get_heatmap(
        hm_df,
        x_field,
        y_field,
        value_field,
        palette=DEF_PALETTE,
        title=None,
        width=DEF_WIDTH,
        tooltip_fields=None,
        js_on_event=None):

    tools = "hover"
    x_range = list(hm_df[x_field].unique())
    y_range = list(hm_df[y_field].unique())

    hm = figure(
        tools=tools,
        toolbar_location=None,
        x_range=x_range,
        y_range=y_range,
        plot_width=width,
        title=title
    )

    src = ColumnDataSource(hm_df)
    mapper = LinearColorMapper(palette=palette, low=0, high=1)
    hm.rect(
        x=x_field,  # this needs to be column from hm_DF
        y=y_field,
        width=1,
        height=1,
        source=src,
        fill_color={'field': value_field, 'transform': mapper},
        line_color='white'
    )

    hm.xaxis.major_label_orientation = 3.14 / 3  # rotation is in radians

    # color bar
    color_bar = ColorBar(
        color_mapper=mapper,
        major_label_text_font_size="8pt",
        ticker=BasicTicker(desired_num_ticks=10),
        formatter=PrintfTickFormatter(format="%0.1f"),
        label_standoff=10,
        border_line_color=None,
        location=(0, 0)
    )
    hm.add_layout(color_bar, 'right')

    if tooltip_fields is None:
        cols = list(hm_df.columns)
        cols.sort(key=lambda x: ([value_field, x_field, y_field] + cols).index(x))
        tooltip_fields = get_tooltip_fields(cols)

    hm.select_one(HoverTool).tooltips = format_tooltip_fields(tooltip_fields)

    if js_on_event is not None:
        hm.js_on_event(js_on_event[0], js_on_event[1])

    return hm


# ---------------------------------------------------------------------
# --- Question bank related
# ---------------------------------------------------------------------

COMP_TBL_FIELDS = ['question X', 'question Y', 'similarity']
SIM_MARKER = '___SIM___'


def create_comp_df(qx, qy, displayed_cols, col2doc_sim=None):
    def _create_series(q):
        if q is None:
            q = pd.Series()

        q = pd.Series([q[c] if c in q else 'none' for c in displayed_cols], index=displayed_cols)

        return q

    qx = _create_series(qx)
    qy = _create_series(qy)

    if col2doc_sim is None:
        col2doc_sim = dict((c, qsim.get_cos_doc_sim) for c in displayed_cols)

    sim = pd.Series(['']*len(qx), index=qx.index)

    for c in col2doc_sim:
        sim.loc[c] = '{}{}'.format(SIM_MARKER, col2doc_sim[c](str(qx.loc[c]), str(qy.loc[c])))

    df = pd.concat([qx, qy, sim], axis=1, ignore_index=True)
    df.columns = COMP_TBL_FIELDS

    return df


def get_comp_div(comp_df, palette=DEF_PALETTE, width=DEF_WIDTH):
    if comp_df is None:
        return Div(text='')

    pd.set_option('display.max_colwidth', -1)

    FONT_COLOR_PALETTE = palettes.Greys256

    soup = BeautifulSoup(comp_df.to_html(), 'html5lib')
    for td in soup.find_all('td', text=re.compile('{}.*'.format(SIM_MARKER))):
        sim = float(td.text.replace(SIM_MARKER, ''))
        bg_color = palette[int(sim*(len(palette) - 1))]
        color = FONT_COLOR_PALETTE[int((1 - sim) * (len(FONT_COLOR_PALETTE) - 1))]
        td.attrs['style'] = 'background-color: {}; color: {}'.format(bg_color, color)
        td.string = '{:0.3f}'.format(sim)

    comp_div = Div(text=str(soup), width=width)

    return comp_div