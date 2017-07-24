import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

import numpy as np

from bokeh.plotting import figure
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
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter, CheckboxGroup
import bokeh.palettes as palettes

from siman.simple_cos_sim import SimpleCosSim

from common import *

import helpers.log_helper as lg

# --- constants -----------------------------------------------------------

MAX_SEARCH_RES = 100
MAX_HEATMAP_ITEMS = 50
MAX_BARS = 10
ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['uuid', 'survey_id', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

COMP_TBL_FIELDS = ['question X', 'question Y']

PAGE_WIDTH = 1800

NARROW_COL_W = 100
WIDE_COL_W = 600
COL_WIDTHS = collections.defaultdict(lambda: NARROW_COL_W)
for c in ['text', 'close_seg_text', 'all_inclusions', 'all_exclusions']:
    COL_WIDTHS[c] = WIDE_COL_W
COL_WIDTHS['type'] = 200
COL_WIDTHS['uuid'] = 200

LOG = lg.get_logger('dashboard')

# --- data -----------------------------------------------------------

class Data:
    base_df = None
    res_df = None
    bar_chart_df = None
    hm_base_df = None
    hm_df = None
    comp_df = None

    selected_result_index = None

    only_cross_survey = False

    @staticmethod
    def compute_sim_matrix(df):
        return SimpleCosSim(df, ANALYSED_COLS).get_similarity_matrix()

    @classmethod
    def update_res_df(cls, search_kw):
        search_kw = search_kw if search_kw is not None else ''

        cls.res_df = cls.base_df[cls.base_df['all_text'].str.contains(search_kw, na=False)]
        if len(cls.res_df) > MAX_SEARCH_RES:
            cls.res_df = cls.res_df.sample(MAX_SEARCH_RES)

    @classmethod
    def update_selected_result_index(cls, index):
        cls.selected_result_index = index

    @classmethod
    def update_bar_chart_df(cls):
        if len(cls.res_df) == 0 or cls.selected_result_index is None:
            cls.bar_chart_df = None
            return None

        idx = cls.selected_result_index

        df = cls.res_df.copy()

        sim_matrix = cls.compute_sim_matrix(df)
        df['similarity'] = sim_matrix[idx]
        df['color'] = df['survey_id'].apply(lambda si: 'green' if si == df.iloc[idx]['survey_id'] else 'red')
        if cls.only_cross_survey:
            df = df[df['color'] == 'red']

        df = df.drop(df.index[idx])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        cls.bar_chart_df = df.iloc[:MAX_BARS]

    @classmethod
    def update_selected_bar_index(cls, index):
        cls.selected_bar_index = index

    @classmethod
    def update_heatmap_df(cls):
        if len(cls.res_df) == 0:
            cls.hm_df = None
            return

        df = cls.res_df.copy()
        if len(df) > MAX_HEATMAP_ITEMS:
            df = df.sample(MAX_HEATMAP_ITEMS)
        cls.hm_base_df = df

        sim_matrix = cls.compute_sim_matrix(df)

        vdf = pd.DataFrame(sim_matrix.flatten(), columns=['similarity'])

        xdf = df.reset_index()
        xdf = pd.concat([xdf] * len(df))
        xdf.index = range(len(xdf))

        ydf = df.reset_index()
        ydf = ydf.loc[np.repeat(ydf.index.values, len(df))]
        ydf.index = range(len(ydf))

        df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
        df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + ['similarity']

        if cls.only_cross_survey:
            df['similarity'] = df.apply(lambda row: row['similarity'] if row['survey_id_x'] != row['survey_id_y'] else 0, axis=1)

        cls.hm_df = df

    @classmethod
    def update_comp_df(cls, qx, qy):
        def _create_series(q):
            if q is None:
                q = pd.Series()

            q['uuid'] = q.name

            q = pd.Series([q[c] if c in q else 'none' for c in DISPLAYED_COLS], index=DISPLAYED_COLS)
            return q

        qx = _create_series(qx)
        qy = _create_series(qy)
        df = pd.concat([qx, qy], axis=1)
        df.columns = COMP_TBL_FIELDS

        cls.comp_df = df

    @classmethod
    def init(cls):
        cls.base_df = load_clean_df()

    # --- actions -----------------------------------------------------------

    @classmethod
    def search_for_kw(cls, search_kw=None):
        cls.update_res_df(search_kw)
        cls.update_selected_result_index(None)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()

    @classmethod
    def select_search_res(cls, selected_result_index=None):
        cls.update_selected_result_index(selected_result_index)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()

    @classmethod
    def select_bar(cls, bar_index=None):
        if cls.selected_result_index is None or bar_index is None:
            cls.comp_df = None
            return

        qx = Data.res_df.iloc[cls.selected_result_index]
        qy = Data.bar_chart_df.iloc[bar_index]

        cls.update_comp_df(qx, qy)

    @classmethod
    def select_hm_cell(cls, uuid_x, uuid_y):
        if uuid_x is None or uuid_y is None:
            cls.comp_df = None
            return

        qx = Data.res_df.loc[uuid_x]
        qy = Data.res_df.loc[uuid_y]

        cls.update_comp_df(qx, qy)


class App:
    @staticmethod
    def format_tooltip_fields(tooltip_fields):
        tooltip_fields = [(tf[0], '<div class="tooltip-field">{}</div>'.format(tf[1])) for tf in tooltip_fields]

        return tooltip_fields

    @classmethod
    def get_nresults_div(cls):
        nresults = len(Data.res_df)
        top_all = 'top' if nresults == MAX_SEARCH_RES else 'all'

        nresults = Div(text='Showing {} {} results'.format(top_all, nresults))

        return nresults

    @classmethod
    def get_res_table(cls):
        if Data.res_df is None:
            return Div(text='')

        template = """<div class="tooltip-parent"><div class="tooltipped"><%= value %></div><div class="tooltip-text"><%= value %></div></div>"""
        columns = [TableColumn(
            field=c,
            title=c,
            width=COL_WIDTHS[c],
            formatter=HTMLTemplateFormatter(template=template)
        ) for c in DISPLAYED_COLS]

        source = ColumnDataSource(Data.res_df)

        callback = CustomJS(args=dict(source=source), code="""select_res(source.attributes.selected['1d']['indices'][0])""")
        source.js_on_change('selected', callback)

        res_table = DataTable(
            source=source,
            columns=columns,
            width=PAGE_WIDTH,
            height=320,
            editable=True
        )

        return res_table

    @classmethod
    def get_bar_chart(cls):
        if Data.bar_chart_df is None:
            return Div(text='')

        tooltip_fields = [
            ('Tr. code', '@tr_code'),
            ('Survey', '@survey_id (@survey_name)'),
            ('Form Type', '@form_type'),
        ]

        for col in ANALYSED_COLS:
            bar_char_title = col.replace('_', ' ').title()
            tooltip_fields.append((bar_char_title, '@{}'.format(col)))

        hover = HoverTool(tooltips=App.format_tooltip_fields(tooltip_fields))

        bc = figure(
            plot_width=int(PAGE_WIDTH // 2 - 20),
            toolbar_location=None,
            tools=[hover],
            title="Select question",
            y_range=Range1d(0, 1)
        )

        src = ColumnDataSource(Data.bar_chart_df)
        bc.vbar(
            x="index",
            top="similarity",
            bottom=0,
            width=0.5,
            fill_color="color",
            source=src
        )

        bc.xaxis[0].ticker.desired_num_ticks = MAX_BARS
        bc.yaxis.axis_label = 'similarity'
        bc.xaxis.axis_label = 'question'
        bc.xaxis.major_label_orientation = 1

        tr_code = Data.res_df.iloc[Data.selected_result_index].name
        bc.title.text = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)

        labels = dict([(i, Data.bar_chart_df.iloc[i]['tr_code']) for i in range(len(Data.bar_chart_df))])
        bc.xaxis.formatter = FuncTickFormatter(code="""var labels = {}; return labels[tick]; """.format(labels))

        callback = CustomJS(code="""
            select_bar(Math.round(cb_obj['x']))
        """)
        bc.js_on_event('tap', callback)

        return bc

    @classmethod
    def get_comp_div(cls):
        if Data.comp_df is None:
            return Div(text='')

        pd.set_option('display.max_colwidth', -1)
        comp_div = Div(text=Data.comp_df.to_html(), width=PAGE_WIDTH)

        return comp_div

    @classmethod
    def get_heatmap(cls):
        if Data.hm_df is None:
            return Div(text='')

        palette = palettes.Magma256
        mapper = LinearColorMapper(palette=palette, low=0, high=1)
        tools = "hover"
        xy_range = list(Data.hm_base_df.index)

        # plot
        hm = figure(
            tools=tools,
            toolbar_location=None,
            x_range=xy_range,
            y_range=xy_range,
            plot_width=int(PAGE_WIDTH // 2)
        )

        title = "Similarity heatmap"
        if len(Data.res_df) > MAX_HEATMAP_ITEMS:
            title += ' (showing only random {} entries from results)'.format(MAX_HEATMAP_ITEMS)
        hm.title.text = title

        src = ColumnDataSource(Data.hm_df)
        hm.rect(
            x="uuid_x",  # this needs to be column from DF
            y="uuid_y",
            width=1,
            height=1,
            source=src,
            fill_color={'field': 'similarity', 'transform': mapper},  # mapper gives the coloring
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

        hm.select_one(HoverTool).tooltips = App.format_tooltip_fields([
            ('Similarity', '@similarity'),
            ('X', '@uuid_x (@survey_name_x)'),
            ('Y', '@uuid_y (@survey_name_y)'),
            ('Text X', '@text_x'),
            ('Text Y', '@text_y'),
        ])

        callback = CustomJS(code="""
            select_hm_cell(cb_obj['x'], cb_obj['y'])
        """)
        hm.js_on_event('tap', callback)

        return hm
