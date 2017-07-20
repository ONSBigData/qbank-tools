from os.path import dirname, join
import pandas as pd
from bokeh.io import curdoc, show
from bokeh.models import ColumnDataSource, Div
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.layouts import layout

template = """<div class="tooltip-parent"><div class="tooltipped"><%= value %></div><div class="tooltip-text"><%= value %></div></div>"""
# template = """<span href="#" data-toggle="tooltip" title="<%= value %>"><%= value %></span>"""

df = pd.DataFrame([
    ['this is a longer text that needs a tooltip, because otherwise we do not see the whole text', 'this is a short text'],
    ['this is another loooooooooooooooong text that needs a tooltip', 'not much here'],
], columns=['a', 'b'])

columns = [TableColumn(field=c, title=c, width=20, formatter=HTMLTemplateFormatter(template=template)) for c in ['a', 'b']]

table = DataTable(source=ColumnDataSource(df), columns=columns)

desc = Div(text=open(join(dirname(__file__), "desc.html")).read())

l = layout([[desc],[table]])

curdoc().add_root(l)

show(l)
