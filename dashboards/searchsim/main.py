import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

import collections

from bokeh.io import curdoc, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Div, Range1d, Text
from bokeh.models.widgets import TextInput, DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.layouts import widgetbox, layout

from os.path import dirname, join

from siman.simple_cos_sim import SimpleCosSim

from common import *

# --- constants -----------------------------------------------------------

MAX_SEARCH_RES = 200
MAX_BARS = 15
ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['survey_id', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

PAGE_WIDTH = 1300

NARROW_COL_W = 100
WIDE_COL_W = 600
COL_WIDTHS = collections.defaultdict(lambda: NARROW_COL_W)
for c in ['text', 'close_seg_text', 'all_inclusions', 'all_exclusions']:
    COL_WIDTHS[c] = WIDE_COL_W
COL_WIDTHS['type'] = 200

# --- data -----------------------------------------------------------

class App:
    qtext = None
    nresults = None
    res_table = None
    bar_chart = None

    search_res_df = None
    base_df = None

    results_src = None
    similarity_src = None

    @classmethod
    def compute_sims_df(cls, selected_index):
        df = cls.search_res_df.copy()
        df['text'] = df['text'].fillna('')

        csm = SimpleCosSim(df, ANALYSED_COLS).get_similarity_matrix()

        df['similarity'] = csm[selected_index]
        df['color'] = df['survey_id'].apply(lambda si: 'green' if si == df.iloc[selected_index]['survey_id'] else 'red')

        df = df.drop(df.index[selected_index])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        return df.iloc[:MAX_BARS]

    @classmethod
    def search_for_kw(cls, search_kw):
        cls.update_results_src(search_kw)
        cls.nresults.text = '{} results'.format(len(cls.search_res_df))

    @classmethod
    def update_results_src(cls, search_kw):
        cls.search_res_df = cls.base_df[cls.base_df['text'].str.contains(search_kw, na=False)]
        if len(cls.search_res_df) > MAX_SEARCH_RES:
            cls.search_res_df = cls.search_res_df.sample(MAX_SEARCH_RES)

        if cls.results_src == None:  # creating
            cls.results_src = ColumnDataSource(cls.search_res_df)
            cls.results_src.on_change('selected', cls.selected_search_result_handler)
        else:
            cls.results_src.data = ColumnDataSource(cls.search_res_df).data

    @classmethod
    def update_similarity_src(cls, selected_index):
        cls.sims_df = cls.compute_sims_df(selected_index)
        
        if cls.similarity_src == None:  # creating
            cls.similarity_src = ColumnDataSource(cls.sims_df)
        else:
            cls.similarity_src.data = ColumnDataSource(cls.sims_df).data

    @classmethod
    def create_table(cls):
        template = """<div class="tooltip-parent"><div class="tooltipped"><%= value %></div><div class="tooltip-text"><%= value %></div></div>"""

        columns = [TableColumn(
            field=c,
            title=c,
            width=COL_WIDTHS[c],
            formatter=HTMLTemplateFormatter(template=template)
        ) for c in DISPLAYED_COLS]

        cls.res_table = DataTable(
            source=cls.results_src,
            columns=columns,
            width=PAGE_WIDTH,
            height=320,
            editable=True
        )
        
    @classmethod
    def create_bar_chart(cls):
        tooltip_fields = [
            ("Survey", "@survey_id (@survey_name)"),
            ("Form Type/Tr. code", "@form_type / @tr_code"),
            ("Text", "@text")
        ]

        for col in ANALYSED_COLS:
            bar_char_title = col.replace('_', ' ').title()
            tooltip_fields.append((bar_char_title, '@{}'.format(col)))

        hover = HoverTool(tooltips=tooltip_fields)

        cls.bar_chart = figure(
            plot_height=600,
            plot_width=PAGE_WIDTH,
            toolbar_location=None,
            tools=[hover],
            title="Select question",
            y_range=Range1d(0, 1)
        )
        cls.bar_chart.vbar(
            x="index",
            top="similarity",
            bottom=0,
            width=0.5,
            fill_color="color",
            source=cls.similarity_src
        )
        cls.bar_chart.min_border_bottom = 200
        cls.bar_chart.yaxis.axis_label = 'similarity'
        cls.bar_chart.xaxis.axis_label = 'question'

    @classmethod
    def selected_search_result_handler(cls, attr, old, new):
        cls.select_index(new['1d']['indices'][0])

    @classmethod
    def select_index(cls, selected_index):
        cls.update_similarity_src(selected_index)

        tr_code = cls.search_res_df.iloc[selected_index].name
        cls.bar_chart.title.text = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)

    @classmethod
    def create_qtext_box(cls):
        cls.qtext = TextInput(title="Search question text")
        cls.qtext.on_change('value', lambda attr, old, new: cls.search_for_kw(cls.qtext.value))

    @classmethod
    def create_nresults_div(cls):
        cls.nresults = Div(text=str(MAX_SEARCH_RES))

    @classmethod
    def show(cls):
        sizing_mode = 'fixed'

        desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=PAGE_WIDTH)

        l = layout([
            [desc],
            [cls.qtext, cls.nresults],
            [cls.res_table],
            [cls.bar_chart]
        ], sizing_mode=sizing_mode)

        curdoc().add_root(l)
        curdoc().title = "Question bank exploration dashboard"

        show(l)

    @classmethod
    def init(cls):
        INIT_INDEX = 0
        INIT_KW = ''

        cls.base_df = load_clean_df()

        cls.update_results_src(INIT_KW)
        cls.update_similarity_src(INIT_INDEX)

        cls.create_table()
        cls.create_bar_chart()
        cls.create_qtext_box()
        cls.create_nresults_div()

        cls.select_index(INIT_INDEX)
        cls.search_for_kw(INIT_KW)

        cls.show()


App.init()
