import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

from os.path import dirname, join
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import TextInput, Select
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn
from bokeh.layouts import widgetbox
from bokeh.io import output_file, show

from common import *

MAX_SEARCH_RES = 50
MAX_BARS = 15

qtext = TextInput(title="Question text contains")

cdf = load_clean_df()
cdf = cdf[['survey_id', 'survey_name', 'form_type', 'tr_code', 'text']]
qdf = cdf.copy()[:MAX_SEARCH_RES]

qbank_source = ColumnDataSource(qdf)

selected_q_index = None
sdf = pd.DataFrame(columns=list(cdf.columns) + ['x', 'sim'])
sim_source = ColumnDataSource(sdf)



def get_sim_scores_df():
    df = qdf.copy()
    df['text'] = df['text'].fillna('')

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    tfidf_vectorizer = TfidfVectorizer(lowercase=True)
    tfidf_matrix = tfidf_vectorizer.fit_transform(df['text'])
    csm = cosine_similarity(tfidf_matrix, tfidf_matrix)

    df['sim'] = csm[selected_q_index]

    df = df.drop(df.index[selected_q_index])

    df = df.sort_values(by='sim', ascending=False)
    df['x'] = range(len(df))



    return df


def updatesim():
    global sim_source

    if selected_q_index is None:
        return
    sdf = get_sim_scores_df().iloc[:MAX_BARS]

    sim_source.data = ColumnDataSource(sdf).data

def update():
    global qbank_source
    global qdf

    qdf = cdf[cdf['text'].str.contains(qtext.value, na=False)]
    qbank_source.data = ColumnDataSource(qdf).data

# table
columns = [TableColumn(field=c, title=c) for c in cdf.columns]
data_table = DataTable(source=qbank_source, columns=columns, width=400, height=280)

hover = HoverTool(tooltips=[
    ("Survey ID", "@survey_id"),
    ("Form Type", "@form_type"),
    ("Tracking code", "@tr_code"),
    ("Text", "@text"),
])

# plot
p = figure(plot_height=600, plot_width=700, title="", toolbar_location=None, tools=[hover])
p.vbar(x="x", top="sim", bottom=0, width=0.5, fill_color="#b3de69", source=sim_source)


def select_item(attr, old, new):
    global selected_q_index
    selected_q_index = new['1d']['indices'][0]
    p.title.text = str(selected_q_index)
    updatesim()
qbank_source.on_change('selected', select_item)

controls = [qtext]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())




sizing_mode = 'fixed'

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=800)
inputs = widgetbox(*controls, sizing_mode=sizing_mode)

l = layout([
    [desc],
    [inputs, data_table],
    [p]
], sizing_mode=sizing_mode)

curdoc().add_root(l)
curdoc().title = "Question bank"

selected_q_index = 3
updatesim()

show(l)
