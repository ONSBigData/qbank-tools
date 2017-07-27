import bokeh.palettes as palettes
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
from bs4 import BeautifulSoup

import helpers.log_helper as lg
from dashboard.model import Model
from dashboard.settings import *
from helpers.common import *

PAGE_WIDTH = 1800
NARROW_COL_W = 100
WIDE_COL_W = 600
COL_WIDTHS = collections.defaultdict(lambda: NARROW_COL_W)
for c in ['qtext', 'close_seg_text', 'all_inclusions', 'all_exclusions']:
    COL_WIDTHS[c] = WIDE_COL_W
COL_WIDTHS['type'] = 200
COL_WIDTHS['survey_name'] = 200
COL_WIDTHS['uuid'] = 200

PALETTE = palettes.Magma256

LOG = lg.get_logger('dashboard')

class Presentation:
    @staticmethod
    def format_tooltip_fields(tooltip_fields):
        tooltip_fields = [(tf[0], '<div class="tooltip-field">{}</div>'.format(tf[1])) for tf in tooltip_fields]

        return tooltip_fields

    @classmethod
    def get_nresults_div(cls, payload):
        df = Model.get_res_df(payload)
        nresults = len(df)
        top_all = 'top' if nresults == MAX_SEARCH_RES else 'all'

        nresults = Div(text='Showing {} {} results'.format(top_all, nresults))

        return nresults

    @classmethod
    def get_res_table(cls, payload):
        df = Model.get_res_df(payload)

        template = """<div class="tooltip-parent"><div class="tooltipped"><%= value %></div><div class="tooltip-text"><%= value %></div></div>"""
        columns = [TableColumn(
            field=c,
            title=c,
            width=COL_WIDTHS[c],
            formatter=HTMLTemplateFormatter(template=template)
        ) for c in DISPLAYED_COLS]

        source = ColumnDataSource(df)

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
    def get_bar_chart(cls, payload):
        bar_chart_df = Model.get_bar_chart_df(payload)
        if bar_chart_df is None:
            return Div(text='')

        res_df = Model.get_res_df(payload)
        selected_res_index = int(payload[SELECTED_RES_INDEX])

        tooltip_fields = [
            ('Tr. code', '@tr_code'),
            ('Survey', '@survey_id (@survey_name)'),
            ('Form Type', '@form_type'),
        ]

        for col in ANALYSED_COLS:
            bar_char_title = col.replace('_', ' ').title()
            tooltip_fields.append((bar_char_title, '@{}'.format(col)))

        hover = HoverTool(tooltips=Presentation.format_tooltip_fields(tooltip_fields))

        bc = figure(
            plot_width=int(PAGE_WIDTH // 2 - 20),
            toolbar_location=None,
            tools=[hover],
            title="Select question",
            y_range=Range1d(0, 1)
        )

        src = ColumnDataSource(bar_chart_df)
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

        tr_code = res_df.iloc[selected_res_index].name
        bc.title.text = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)

        labels = dict([(i, bar_chart_df.iloc[i]['tr_code']) for i in range(len(bar_chart_df))])
        bc.xaxis.formatter = FuncTickFormatter(code="""var labels = {}; return labels[tick]; """.format(labels))

        callback = CustomJS(code="""
            select_bar(Math.round(cb_obj['x']))
        """)
        bc.js_on_event('tap', callback)

        return bc

    @classmethod
    def get_comp_div(cls, payload):
        comp_df = Model.get_comp_df(payload)

        if comp_df is None:
            return Div(text='')

        pd.set_option('display.max_colwidth', -1)

        FONT_COLOR_PALETTE = palettes.Greys256

        soup = BeautifulSoup(comp_df.to_html(), 'html5lib')
        for tr in soup.find_all('tr')[1:]:
            td = tr.find_all('td')[-1]
            if td.text != '':
                sim = float(td.text)
                bg_color = PALETTE[int(sim*(len(PALETTE) - 1))]
                color = FONT_COLOR_PALETTE[int((1 - sim) * (len(FONT_COLOR_PALETTE) - 1))]
                td.attrs['style'] = 'background-color: {}; color: {}'.format(bg_color, color)

        comp_div = Div(text=str(soup), width=PAGE_WIDTH)

        return comp_div

    @classmethod
    def get_heatmap(cls, payload):
        res_df = Model.get_res_df(payload)
        hm_df = Model.get_heatmap_df(payload)

        if hm_df is None:
            return Div(text='')

        mapper = LinearColorMapper(palette=PALETTE, low=0, high=1)
        tools = "hover"
        xy_range = list(hm_df['uuid_x'].unique())

        # plot
        hm = figure(
            tools=tools,
            toolbar_location=None,
            x_range=xy_range,
            y_range=xy_range,
            plot_width=int(PAGE_WIDTH // 2)
        )

        title = "Similarity heatmap"
        if len(res_df) > MAX_HEATMAP_ITEMS:
            title += ' (showing only random {} entries from results)'.format(MAX_HEATMAP_ITEMS)
        hm.title.text = title

        src = ColumnDataSource(hm_df)
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

        hm.select_one(HoverTool).tooltips = Presentation.format_tooltip_fields([
            ('Similarity', '@similarity'),
            ('X', '@uuid_x (@survey_name_x)'),
            ('Y', '@uuid_y (@survey_name_y)'),
            ('Text X', '@qtext_x'),
            ('Text Y', '@qtext_y'),
        ])

        callback = CustomJS(code="""
            select_hm_cell(cb_obj['x'], cb_obj['y'])
        """)
        hm.js_on_event('tap', callback)

        return hm
