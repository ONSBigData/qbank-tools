from bokeh.models import Div, Slider, Select, CheckboxGroup, CustomJS, TextInput
from bokeh.models.widgets import Button
from bokeh.layouts import layout, widgetbox

from bokeh.server.server import Server
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from tornado.ioloop import IOLoop

from helpers.common import *
from dashboard.settings import *
import helpers.bokeh_helper as bh

import qsim.sim_analyze as simeval
from qsim.sims.tfidf_cos_sim import TfidfCosSim
from qsim.sims.sent_vec_sim import SentVecSim
import qsim.all_sims as all_sims
import datetime
import traceback

# --- constants -----------------------------------------------------------

WIDGET_BOX_WIDTH = 250
CHARTS_WIDTH = PAGE_WIDTH - WIDGET_BOX_WIDTH
DIV_WIDTH = CHARTS_WIDTH // 2 - 20

COL_OPTIONS = [
    'suff_qtext',
    'type',
    'close_seg_text',
    'all_inclusions',
    'all_exclusions',
    'uuid',
    'survey_id',
    'survey_name',
    'form_type',
    'tr_code',
    'notes'
]

INIT_COLS = ['suff_qtext', 'type']
INIT_NRESULTS = 20
INIT_SEARCH = ''


class QSearchApp:
    def update_chart(self, holding_div, create_chart_code_method):
        holding_div.text = 'Updating...'

        try:
            chart_code = create_chart_code_method()
            holding_div.text = chart_code
        except Exception as e:
            holding_div.text = 'Exception occured: {}\n{}'.format(e, traceback.format_exc())

    def update_params(self):
        self.search_text = self.search_text_ctrl.value
        self.cols = [COL_OPTIONS[i] for i in self.analysed_cols_ctrl.active]
        self.nresults = 20

        self.update()

    def update(self):
        sim = SentVecSim(self.cols)

        for div in [self.res_div]:
            div.text = 'Awaiting update...'

        def create_res_div():
            rows = []

            for _, row in self.base_df.iterrows():
                row_text = sim.preprocess_row(row)
                similarity = sim.get_text_sim(row_text, self.search_text)
                if similarity is None:
                    similarity = 0

                rows.append((row, similarity))

            rows.sort(key=lambda x: x[1], reverse=True)

            df = pd.DataFrame([r[0] for r in rows[:self.nresults]], columns=self.cols)
            return df.to_html()

        self.update_chart(self.res_div, create_res_div)


    def __init__(self):
        pd.set_option('display.max_colwidth', -1)

        try:
            self.base_df = load_clean_df()
        except:
            fpath = BUNDLED_DATA_DIR + '/clean-light.csv'
            self.base_df = load_clean_df(fpath=fpath)

        # init parameters
        self.search_text = INIT_SEARCH
        self.cols = INIT_COLS
        self.nresults = INIT_NRESULTS

        # divs holding the charts
        self.res_div = Div(text='', width=CHARTS_WIDTH)

        # controls
        self.search_text_ctrl = TextInput(title=None, value=INIT_SEARCH, width=WIDGET_BOX_WIDTH - 50)
        self.analysed_cols_ctrl = CheckboxGroup(labels=COL_OPTIONS, active=[COL_OPTIONS.index(c) for c in INIT_COLS])

        self.submit_btn = Button(label="Submit", button_type="success")
        self.submit_btn.on_click(self.update_params)

        self.update()

    def get_layout(self):
        sizing_mode = 'fixed'

        inputs = widgetbox(
            [
                self.submit_btn,
                Div(text='<hr>'),

                Div(text='<b>Search:</i>'),
                self.search_text_ctrl,
                Div(text='<hr>')
            ],
            sizing_mode=sizing_mode, responsive=True, width=WIDGET_BOX_WIDTH
        )

        charts = layout([
            [Div(text='<h2>Example question pairs</h2>', width=CHARTS_WIDTH)],
            [self.res_div],
        ])

        l = layout([
            [inputs, charts],
            [Div(height=200)]  # some empty space
        ], sizing_mode=sizing_mode)

        return l



def run_app(show=True):
    def modify_doc(doc):
        app = QSearchApp()
        l = app.get_layout()
        doc.add_root(l)
        doc.title = 'Similarity evaluation dashboard'

    io_loop = IOLoop.instance()
    bokeh_app = Application(FunctionHandler(modify_doc))

    server = Server(
        {'/': bokeh_app},
        io_loop=io_loop,
        allow_websocket_origin="*",
        port=SIM_EVAL_PORT,
        host='*',
        address='localhost',
        use_xheaders=True
    )
    server.start()

    gh.print_and_flush('Starting Bokeh ioloop. Url: http://localhost:{}/'.format(SIM_EVAL_PORT))

    if show:
        io_loop.add_callback(server.show, "/")

    io_loop.start()


if __name__ == '__main__':
    run_app()
