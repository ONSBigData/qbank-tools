import bokeh.palettes as palettes
import pandas as pd
from bokeh.models import \
    ColumnDataSource, \
    HoverTool, \
    Range1d, \
    FuncTickFormatter, \
    LinearColorMapper, \
    ColorBar, \
    BasicTicker, \
    PrintfTickFormatter, \
    DataRange1d, \
    Quad
from bokeh.plotting import figure
from bokeh.embed import components
import numpy as np
import re

DEF_PALETTE = palettes.Magma256
DEF_WIDTH = 600
TOOLTIP_BASIC = 'basic'
TOOLTIP_ALL = 'all'

DEF_TOOLS = ['save', 'reset', 'box_zoom']
DEF_TOOL_LOC = 'right'

# ---------------------------------------------------------------------
# --- General
# ---------------------------------------------------------------------


def get_code(obj):
    js, div = components(obj)
    return js + ' ' + div


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

    if tooltip_fields is not None:
        if _is_non_empty_list_of_strings(tooltip_fields):  # columns
            tooltip_fields = get_tooltip_fields(tooltip_fields)

        if tooltip_fields is TOOLTIP_ALL:
            tooltip_fields = get_tooltip_fields(df.columns)

        if tooltip_fields is TOOLTIP_BASIC:
            tooltip_fields = get_tooltip_fields([x_field, y_field])

        hover = HoverTool(tooltips=format_tooltip_fields(tooltip_fields))

    bc = figure(
        plot_width=width,
        toolbar_location=DEF_TOOL_LOC,
        tools=DEF_TOOLS + [hover],
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


def get_hist(
        values,
        bins=15,
        width=DEF_WIDTH,
        title=None,
        js_on_event=None,
        **kwargs):

    hist_probs, edges = np.histogram(values, density=True, bins=bins)
    hist_counts, edges = np.histogram(values, density=False, bins=bins)

    source = ColumnDataSource(dict(
            left=edges[:-1],
            top=hist_probs,
            right=edges[1:],
            bottom=[0]*len(hist_probs),
            count=hist_counts
        )
    )

    hover = HoverTool(tooltips=[('Count', '@count')])

    xdr = DataRange1d()
    ydr = DataRange1d()

    hist = figure(
        plot_width=width,
        toolbar_location=DEF_TOOL_LOC,
        tools=DEF_TOOLS + [hover],
        title=title,
        x_range=xdr,
        y_range=ydr,
        **kwargs
    )

    bars = Quad(top='top', bottom='bottom', left='left', right='right', fill_color="#036564", line_color="#033649")
    hist.add_glyph(source, bars)

    if js_on_event is not None:
        hist.js_on_event(js_on_event[0], js_on_event[1])

    return hist


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


def _is_non_empty_list_of_strings(arg):
    return isinstance(arg, list) and len(arg) > 0 and type(arg[0]) == type('')


def get_heatmap(
        hm_df,
        x_field,
        y_field,
        value_field='value',
        palette=DEF_PALETTE,
        title=None,
        width=DEF_WIDTH,
        tooltip_fields=None,
        js_on_event=None):

    x_range = list(str(v) for v in hm_df[x_field].unique())
    y_range = list(str(v) for v in hm_df[y_field].unique())

    hm = figure(
        tools=DEF_TOOLS + ['hover'],
        toolbar_location='above',
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

    if tooltip_fields is not None:
        if _is_non_empty_list_of_strings(tooltip_fields):  # columns
            cols = [c for c in hm_df.columns if any(re.match('{}_(x|y)'.format(x), c) is not None for x in tooltip_fields)]
            cols = [value_field] + cols
            tooltip_fields = get_tooltip_fields(cols)

        if tooltip_fields == TOOLTIP_BASIC:
            tooltip_fields = get_tooltip_fields([value_field, x_field, y_field])

        if tooltip_fields == TOOLTIP_ALL:
            cols = list(hm_df.columns)
            cols_cp = list(cols)
            cols.sort(key=lambda x: ([value_field, x_field, y_field] + cols_cp).index(x))
            tooltip_fields = get_tooltip_fields(cols)

        hm.select_one(HoverTool).tooltips = format_tooltip_fields(tooltip_fields)

    if js_on_event is not None:
        hm.js_on_event(js_on_event[0], js_on_event[1])

    return hm

