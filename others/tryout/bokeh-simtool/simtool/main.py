import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

from os.path import dirname, join
from bokeh.plotting import figure
from bokeh.layouts import layout
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import TextInput
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.layouts import widgetbox
from bokeh.io import show
from bokeh.models import Range1d


from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from common import *

MAX_SEARCH_RES = 50
MAX_BARS = 15

class Data:
    @classmethod
    def compute_sims_df(cls, selected_index):
        df = cls.search_res_df.copy()
        df['text'] = df['text'].fillna('')

        tfidf_vectorizer = TfidfVectorizer(lowercase=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(df['text'])
        csm = cosine_similarity(tfidf_matrix, tfidf_matrix)

        df['similarity'] = csm[selected_index]

        df = df.drop(df.index[selected_index])

        df = df.sort_values(by='similarity', ascending=False)

        df['index'] = range(len(df))

        return df.iloc[:MAX_BARS]

    @classmethod
    def init(cls):
        cls.selected_index = 0

        cls.base_df = load_clean_df()

        cls.search_res_source = None
        cls.sims_source = None

        cls.update_search_res_source('')
        cls.update_sims_source(cls.selected_index)

    @classmethod
    def update_search_res_source(cls, search_kw):
        cls.search_res_df = cls.base_df[cls.base_df['text'].str.contains(search_kw, na=False)]
        cls.search_res_df = cls.search_res_df[['survey_id', 'form_type', 'tr_code', 'text']]
        if len(cls.search_res_df) > MAX_SEARCH_RES:
            cls.search_res_df = cls.search_res_df.sample(MAX_SEARCH_RES)
        
        if cls.search_res_source is None:
            cls.search_res_source = ColumnDataSource(cls.search_res_df)
        else:
            cls.search_res_source.data = ColumnDataSource(cls.search_res_df).data

    @classmethod
    def update_sims_source(cls, selected_index):
        cls.sims_df = cls.compute_sims_df(selected_index)
        
        if cls.sims_source is None:
            cls.sims_source = ColumnDataSource(cls.sims_df)
        else:
            cls.sims_source.data = ColumnDataSource(cls.sims_df).data

Data.init()

# table
columns = [TableColumn(field=c, title=c) for c in Data.search_res_df.columns]
search_res_table = DataTable(source=Data.search_res_source, columns=columns, width=800, height=280)

# plot
hover = HoverTool(tooltips=[
    ("Survey ID", "@survey_id"),
    ("Form Type", "@form_type"),
    ("Tracking code", "@tr_code"),
    ("Text", "@text"),
])

sim_bar_chart = figure(
    plot_height=600,
    plot_width=700,
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
    fill_color="#b3de69",
    source=Data.sims_source
)
sim_bar_chart.min_border_bottom = 200


# handling selection
def selected_search_result_handler(attr, old, new):
    Data.selected_index = new['1d']['indices'][0]
    Data.update_sims_source(Data.selected_index)

    tr_code = Data.search_res_df.loc[Data.selected_index]['tr_code']
    sim_bar_chart.title.text = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)
Data.search_res_source.on_change('selected', selected_search_result_handler)

# controls
qtext = TextInput(title="Search question text")
qtext.on_change('value', lambda attr, old, new: Data.update_search_res_source(qtext.value))

# final layout
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
