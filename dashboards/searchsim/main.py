import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

from bokeh.io import curdoc, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, Div, Range1d
from bokeh.models.widgets import TextInput, DataTable, TableColumn
from bokeh.layouts import widgetbox, layout

from os.path import dirname, join

from siman.simple_cos_sim import SimpleCosSim

from common import *

# --- constants -----------------------------------------------------------

MAX_SEARCH_RES = 50
MAX_BARS = 15
ANALYSED_COLS = ['text', 'type', 'close_seg_text', 'all_inclusions', 'all_exclusions']
DISPLAYED_COLS = ['survey_id', 'form_type', 'tr_code', 'text']
DISPLAYED_COLS += [c for c in ANALYSED_COLS if c not in DISPLAYED_COLS]

# --- data -----------------------------------------------------------

class Data:
    @classmethod
    def compute_sims_df(cls, selected_index):
        """Brings back a dataframe with (among others) similarity scores against selected question"""

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
    def update_search_res_source(cls, search_kw):
        """updates the search results data source, i.e. the data of the table, based on the searched key word"""

        cls.search_res_df = cls.base_df[cls.base_df['text'].str.contains(search_kw, na=False)]
        if len(cls.search_res_df) > MAX_SEARCH_RES:
            cls.search_res_df = cls.search_res_df.sample(MAX_SEARCH_RES)

        if not hasattr(cls, 'search_res_source'):
            cls.search_res_source = ColumnDataSource(cls.search_res_df)
        else:
            cls.search_res_source.data = ColumnDataSource(cls.search_res_df).data

    @classmethod
    def update_sims_source(cls, selected_index):
        """updates the similarity data source (i.e. underlying data used by the bar chart), based on the selected index"""

        cls.sims_df = cls.compute_sims_df(selected_index)
        
        if not hasattr(cls, 'sims_source'):
            cls.sims_source = ColumnDataSource(cls.sims_df)
        else:
            cls.sims_source.data = ColumnDataSource(cls.sims_df).data

    @classmethod
    def init(cls):
        cls.selected_index = 0

        cls.base_df = load_clean_df()

        cls.update_search_res_source('')
        cls.update_sims_source(cls.selected_index)

Data.init()


# --- table -----------------------------------------------------------

columns = [TableColumn(field=c, title=c) for c in DISPLAYED_COLS]
search_res_table = DataTable(source=Data.search_res_source, columns=columns, width=1000, height=280)


# --- bar chart -----------------------------------------------------------

tooltip_fields = [
    ("Survey ID", "@survey_id"),
    ("Form Type", "@form_type"),
    ("Tracking code", "@tr_code"),
    ("Text", "@text")
]

for col in ANALYSED_COLS:
    title = col.replace('_', ' ').title()
    tooltip_fields.append((title, '@{}'.format(col)))

hover = HoverTool(tooltips=tooltip_fields)

sim_bar_chart = figure(
    plot_height=600,
    plot_width=1300,
    title="",
    toolbar_location=None,
    tools=[hover],
    y_range=Range1d(0, 1)
)
sim_bar_chart.vbar(
    x="index",
    top="similarity",
    bottom=0,
    width=0.5,
    fill_color="color",
    source=Data.sims_source
)
sim_bar_chart.min_border_bottom = 200
sim_bar_chart.yaxis.axis_label = 'similarity'
sim_bar_chart.xaxis.axis_label = 'question'

# --- interactions -----------------------------------------------------------

def selected_search_result_handler(attr, old, new):
    Data.selected_index = new['1d']['indices'][0]
    Data.update_sims_source(Data.selected_index)

    tr_code = Data.search_res_df.iloc[Data.selected_index].name
    sim_bar_chart.title.text = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)

Data.search_res_source.on_change('selected', selected_search_result_handler)

qtext = TextInput(title="Search question text")
qtext.on_change('value', lambda attr, old, new: Data.update_search_res_source(qtext.value))


# --- final layout -----------------------------------------------------------

sizing_mode = 'fixed'

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=800)

inputs = widgetbox(*[qtext], sizing_mode=sizing_mode)

l = layout([
    [desc],
    [inputs, search_res_table],
    [sim_bar_chart]
], sizing_mode=sizing_mode)

curdoc().add_root(l)
curdoc().title = "Question bank exploration dashboard"

show(l)
