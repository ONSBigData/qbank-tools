from os.path import dirname, join

import numpy as np

import os
import sys
sys.path.append('/home/ons21553/wspace/qbank/code')

from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import TextInput, Select
from bokeh.io import curdoc

from common import *

desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=800)

# Create Input controls
# survey = Select(title="Genre", value="All", options=open(join(dirname(__file__), 'genres.txt')).read().split())
qtext = TextInput(title="Question text contains")

cdf = load_clean_df()

# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(x=[], survey_id=[], survey_name=[], form_type=[], tr_code=[], text=[], text_len=[]))

hover = HoverTool(tooltips=[
    ("Survey ID", "@survey_id"),
    ("Form Type", "@form_type"),
    ("Tracking code", "@tr_code")
])

p = figure(plot_height=600, plot_width=700, title="", toolbar_location=None, tools=[hover])
p.vbar(x="x", width=0.5, bottom=0, top="text_len", color="#CAB2D6", source=source)


def select_questions():
    qdf = cdf[cdf['survey_name'].str.contains(qtext.value, na=False)]

    return qdf


def update():
    df = select_questions()

    df = df.reset_index()

    df = df.iloc[:10]
    df['text_len'] = df['text'].str.len()


    df = df[['survey_id', 'survey_name', 'form_type', 'tr_code', 'text', 'text_len']]
    d = {}
    for c in df.columns:
        d[c] = df[c]

    d['x'] = list(range(len(df)))
    d['top'] = df['text_len']

    source.data = d

controls = [qtext]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())

sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example

inputs = widgetbox(*controls, sizing_mode=sizing_mode)
l = layout([
    [desc],
    [inputs, p],
], sizing_mode=sizing_mode)

update()  # initial load of the data

curdoc().add_root(l)
curdoc().title = "Questions"
