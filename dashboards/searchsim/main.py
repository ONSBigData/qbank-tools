import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

import traceback
import collections
import numpy as np

from bokeh.embed import components
from bokeh.io import curdoc, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Div, Range1d, FuncTickFormatter, LinearColorMapper, ColorBar, BasicTicker, PrintfTickFormatter
from bokeh.models.widgets import TextInput, DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.layouts import layout
from bokeh.events import Tap
import bokeh.palettes as palettes

from tornado.ioloop import IOLoop
from bokeh.server.server import Server
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application

from os.path import dirname, join

from siman.simple_cos_sim import SimpleCosSim

from common import *

import helpers.log_helper as lg

# --- constants -----------------------------------------------------------

MAX_SEARCH_RES = 50
MAX_BARS = 10
ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['survey_id', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

COMP_TBL_FIELDS = ['selected', 'compared']

PAGE_WIDTH = 1300

NARROW_COL_W = 100
WIDE_COL_W = 600
COL_WIDTHS = collections.defaultdict(lambda: NARROW_COL_W)
for c in ['text', 'close_seg_text', 'all_inclusions', 'all_exclusions']:
    COL_WIDTHS[c] = WIDE_COL_W
COL_WIDTHS['type'] = 200

LOG = lg.get_logger('dashboard')

INIT_KW = ''

# --- data -----------------------------------------------------------

class Data:
    base_df = None
    res_df = None
    bar_chart_df = None
    hm_df = None

    sim_matrix = None

    selected_result_index = None

    @classmethod
    def update_res_df(cls, search_kw):
        cls.res_df = cls.base_df[cls.base_df['all_text'].str.contains(search_kw, na=False)]
        if len(cls.res_df) > MAX_SEARCH_RES:
            cls.res_df = cls.res_df.sample(MAX_SEARCH_RES)

        cls.compute_sim_matrix()

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

        df['similarity'] = cls.sim_matrix[idx]
        df['color'] = df['survey_id'].apply(lambda si: 'green' if si == df.iloc[idx]['survey_id'] else 'red')

        df = df.drop(df.index[idx])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        cls.bar_chart_df = df.iloc[:MAX_BARS]

    @classmethod
    def update_heatmap_df(cls):
        if len(cls.res_df) == 0:
            cls.hm_df = None
            return

        df = cls.res_df.copy()

        vdf = pd.DataFrame(cls.sim_matrix.flatten(), columns=['similarity'])

        xdf = df.reset_index()
        xdf = pd.concat([xdf] * len(df))
        xdf.index = range(len(xdf))

        ydf = df.reset_index()
        ydf = ydf.loc[np.repeat(ydf.index.values, len(df))]
        ydf.index = range(len(ydf))

        df = pd.concat([xdf, ydf, vdf], axis=1, ignore_index=True)
        df.columns = [c + '_x' for c in xdf.columns] + [c + '_y' for c in xdf.columns] + ['similarity']

        cls.hm_df = df

    @classmethod
    def compute_sim_matrix(cls):
        if len(cls.res_df) == 0:
            cls.sim_matrix = None
            return

        cls.sim_matrix = SimpleCosSim(cls.res_df, ANALYSED_COLS).get_similarity_matrix()

    @classmethod
    def init(cls):
        cls.base_df = load_clean_df()

        cls.update_res_df(INIT_KW)
        cls.update_selected_result_index(None)
        cls.update_bar_chart_df()
        cls.update_heatmap_df()


class App:
    qtext = None
    nresults = None
    res_table = None
    bar_chart = None
    comp_div = None
    hm = None

    # --- static -----------------------------------------------------------

    @staticmethod
    def format_tooltip_fields(tooltip_fields):
        tooltip_fields = [(tf[0], '<div class="tooltip-field">{}</div>'.format(tf[1])) for tf in tooltip_fields]

        return tooltip_fields

    # --- actions -----------------------------------------------------------

    @classmethod
    def search_for_kw_handler(cls, search_kw):
        Data.update_res_df(search_kw)
        Data.update_selected_result_index(None)
        Data.update_bar_chart_df()
        Data.update_heatmap_df()

        cls.update_nresults()
        cls.update_res_table()
        cls.update_bar_chart()
        cls.update_hm()
        cls.update_comp_div(None)

    @classmethod
    def select_result_handler(cls, index):
        Data.update_selected_result_index(index)
        Data.update_bar_chart_df()

        cls.update_bar_chart()
        cls.update_comp_div(None)

    @classmethod
    def select_bar_handler(cls, bar_index):
        cls.update_comp_div(bar_index)

    # --- updates -----------------------------------------------------------

    @classmethod
    def update_nresults(cls):
        nresults = len(Data.res_df)
        top_all = 'top' if nresults == MAX_SEARCH_RES else 'all'
        cls.nresults.text = 'Showing {} {} results'.format(top_all, nresults)

    @classmethod
    def update_res_table(cls):
        cls.res_table.source.data = ColumnDataSource(Data.res_df).data

    @classmethod
    def update_bar_chart(cls):
        df = Data.bar_chart_df

        if df is None:
            cls.bar_chart.text = ''
            return

        script, div = cls.get_bar_chart()
        cls.bar_chart.text = script + div

    @classmethod
    def update_comp_div(cls, selected_bar_index):
        if selected_bar_index is None:
            return

        selected_res_index = Data.selected_result_index

        selected_q = Data.res_df.iloc[selected_res_index]
        compared_q = Data.bar_chart_df.iloc[selected_bar_index]

        def _create_series(q):
            if q is None:
                q = pd.Series()

            q = pd.Series([q[c] if c in q else 'none' for c in DISPLAYED_COLS], index=DISPLAYED_COLS)
            return q

        selected_q = _create_series(selected_q)
        compared_q = _create_series(compared_q)
        df = pd.concat([selected_q, compared_q], axis=1)
        df.columns = COMP_TBL_FIELDS

        pd.set_option('display.max_colwidth', -1)

        cls.comp_div.text = df.to_html()

    @classmethod
    def update_hm(cls):
        df = Data.hm_df

        if df is None:
            cls.hm.text = ''
            return

        script, div = cls.get_heatmap()
        cls.hm.text = script + div


    # --- create -----------------------------------------------------------

    @classmethod
    def create_qtext_box(cls):
        cls.qtext = TextInput(title="Search question text")
        cls.qtext.on_change('value', lambda attr, old, new: cls.search_for_kw_handler(cls.qtext.value))

    @classmethod
    def create_nresults_div(cls):
        cls.nresults = Div(text=str(MAX_SEARCH_RES))

    @classmethod
    def create_res_table(cls):
        template = """<div class="tooltip-parent"><div class="tooltipped"><%= value %></div><div class="tooltip-text"><%= value %></div></div>"""
        columns = [TableColumn(
            field=c,
            title=c,
            width=COL_WIDTHS[c],
            formatter=HTMLTemplateFormatter(template=template)
        ) for c in DISPLAYED_COLS]

        def _selected_handler(attr, old, new):
            cls.select_result_handler(new['1d']['indices'][0])

        source = ColumnDataSource(pd.DataFrame())
        source.on_change('selected', _selected_handler)

        cls.res_table = DataTable(
            source=source,
            columns=columns,
            width=PAGE_WIDTH,
            height=320,
            editable=True
        )

    @classmethod
    def get_bar_chart(cls):
        tooltip_fields = [
            ('Tr. code', '@tr_code'),
            ('Survey', '@survey_id (@survey_name)'),
            ('Form Type', '@form_type'),
            ('Text', '@text')
        ]

        for col in ANALYSED_COLS:
            bar_char_title = col.replace('_', ' ').title()
            tooltip_fields.append((bar_char_title, '@{}'.format(col)))

        hover = HoverTool(tooltips=App.format_tooltip_fields(tooltip_fields))

        bc = figure(
            plot_height=400,
            plot_width=PAGE_WIDTH // 2 - 50,
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

        def on_tap(event):
            index = round(event.x)
            cls.select_bar_handler(index)

        bc.on_event(Tap, on_tap)

        return components(bc)

    @classmethod
    def create_bar_chart(cls):
        cls.bar_chart = Div(text='', height=400, width=PAGE_WIDTH // 2 - 50)

    @classmethod
    def create_comp_div(cls):
        cls.comp_div = Div(text='')

    @classmethod
    def get_heatmap(cls):
        palette = palettes.Magma256
        mapper = LinearColorMapper(palette=palette, low=0, high=1)
        tools = "hover"
        xy_range = list(Data.res_df.index)

        # plot
        hm = figure(
            title="Heatmap",
            tools=tools,
            toolbar_location=None,
            x_range=xy_range,
            y_range=xy_range,
            plot_width=PAGE_WIDTH // 2 - 50
        )

        src = ColumnDataSource(Data.hm_df)
        hm.rect(
            x="uid_x",  # this needs to be column from DF
            y="uid_y",
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
            ('X', '@uid_x'),
            ('Y', '@uid_y'),

            ('Survey X', '@survey_id_x (@survey_name_x)'),
            ('Form type X', '@form_type_x'),
            ('Tr. code X', '@tr_code_x'),

            ('Survey Y', '@survey_id_y (@survey_name_y)'),
            ('Form type Y', '@form_type_y'),
            ('Tr. code Y', '@tr_code_y'),
        ])

        return components(hm)

    @classmethod
    def create_heatmap(cls):
        cls.hm = Div(text='', width=PAGE_WIDTH // 2 - 50)

    @classmethod
    def get_layout(cls):
        sizing_mode = 'fixed'

        desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=700)

        search = layout([[cls.qtext], [cls.nresults]])

        l = layout([
            [desc, search],
            [cls.res_table],
            [cls.bar_chart, cls.hm],
            [cls.comp_div],
            [Div(height=200)]  # some empty space
        ], sizing_mode=sizing_mode)

        return l

    @classmethod
    def init(cls):
        Data.init()

        cls.create_qtext_box()
        cls.create_nresults_div()
        cls.create_res_table()
        cls.create_bar_chart()
        cls.create_heatmap()
        cls.create_comp_div()

        cls.search_for_kw_handler(INIT_KW)

def modify_doc(doc):
    App.init()
    l = App.get_layout()

    doc.add_root(l)


io_loop = IOLoop.current()

bokeh_app = Application(FunctionHandler(modify_doc))

server = Server({'/': bokeh_app}, io_loop=io_loop)
server.start()

if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')
    io_loop.add_callback(server.show, "/")
    io_loop.start()