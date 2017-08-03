import bokeh.palettes as palettes
from bokeh.models import ColumnDataSource, Div, CustomJS
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
import siman.simeval as simeval
import helpers.log_helper as lg
import helpers.bokeh_helper as bh
from dashboard.model import Model
from dashboard.settings import *
from helpers.common import *

NARROW_COL_W = 100
WIDE_COL_W = 600
COL_WIDTHS = collections.defaultdict(lambda: NARROW_COL_W)
for c in ['suff_qtext', 'close_seg_text', 'all_inclusions', 'all_exclusions']:
    COL_WIDTHS[c] = WIDE_COL_W
COL_WIDTHS['type'] = 200
COL_WIDTHS['survey_name'] = 200
COL_WIDTHS['uuid'] = 200

PALETTE = palettes.Magma256

LOG = lg.get_logger('dashboard')


class Presentation:
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
        selected_res_index = payload[SELECTED_RES_INDEX]

        tooltip_fields = [
            ('Tr. code', '@tr_code'),
            ('Survey', '@survey_id (@survey_name)'),
            ('Form Type', '@form_type'),
        ]
        tooltip_fields.extend(bh.get_tooltip_fields(ANALYSED_COLS))

        tr_code = res_df.iloc[selected_res_index].name
        title = 'Top {} similar questions for question {}'.format(MAX_BARS, tr_code)

        tap_callback = CustomJS(code="""
            select_bar(Math.round(cb_obj['x']))
        """)

        bar_chart = bh.get_bar_chart(
            bar_chart_df,
            'tr_code',
            'similarity',
            'color',
            tooltip_fields=tooltip_fields,
            width=int(PAGE_WIDTH // 2 - 20),
            title=title,
            js_on_event=('tap', tap_callback)
        )

        return bar_chart

    @classmethod
    def get_comp_div(cls, payload):
        comp_df = Model.get_comp_df(payload)
        comp_div = simeval.get_comp_div(comp_df, palette=PALETTE, width=PAGE_WIDTH)

        return comp_div

    @classmethod
    def get_heatmap(cls, payload):
        res_df = Model.get_res_df(payload)
        hm_df = Model.get_heatmap_df(payload)

        if hm_df is None:
            return Div(text='')

        title = "Similarity heatmap"
        if len(res_df) > MAX_HEATMAP_ITEMS:
            title += ' (showing only random {} entries from results)'.format(MAX_HEATMAP_ITEMS)

        tooltip_fields = [
            ('Similarity', '@similarity'),
            ('X', '@uuid_x (@survey_name_x)'),
            ('Y', '@uuid_y (@survey_name_y)'),
            ('Text X', '@qtext_x'),
            ('Text Y', '@qtext_y'),
        ]

        tap_callback = CustomJS(code="""
            select_hm_cell(cb_obj['x'], cb_obj['y'])
        """)

        hm = bh.get_heatmap(
            hm_df,
            'uuid_x',
            'uuid_y',
            'similarity',
            palette=PALETTE,
            title=title,
            width=int(PAGE_WIDTH // 2),
            tooltip_fields=tooltip_fields,
            js_on_event=('tap', tap_callback)
        )

        return hm
