from bokeh.models import Div, Slider, Select, CheckboxGroup, CustomJS
from bokeh.models.widgets import Button
from bokeh.layouts import layout, widgetbox

from bokeh.server.server import Server
from bokeh.application.handlers import FunctionHandler
from bokeh.application import Application
from tornado.ioloop import IOLoop

from helpers.common import *
import helpers.bokeh_helper as bh

import siman.simeval as simeval
from siman.sims.tfidf_cos import TfidfCosSim
import siman.all_sims as all_sims


# --- constants -----------------------------------------------------------

PAGE_WIDTH = 1500
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
SIM_PARAM_REM_STOP = 'remove stopwords'
SIM_PARAM_STEM = 'stemming'
SIM_PARAM_ONLY_ALPHA_NUM = 'only alphanum. chars'
SIM_PARAM_LOWER_CASE = 'lowercase'
SIM_PARAMS = [
    SIM_PARAM_REM_STOP,
    SIM_PARAM_STEM,
    SIM_PARAM_ONLY_ALPHA_NUM,
    SIM_PARAM_LOWER_CASE
]

INIT_HM_SAMPLE_SIZE = 30
INIT_HIST_SAMPLE_SIZE = 100
INIT_SIM = TfidfCosSim
INIT_COLS = ['suff_qtext', 'type']


class SimEvalApp:
    def update(self):
        # update parameters
        self.hm_sample_size = self.hm_sample_size_ctrl.value
        self.hist_sample_size = self.hist_sample_size_ctrl.value
        self.cols = [COL_OPTIONS[i] for i in self.analysed_cols_ctrl.active]
        sim_class = all_sims.get_sim_class_by_name(self.sim_ctrl.value)
        self.sim = sim_class(self.cols)

        # --- Heatmaps -----------------------------------------------------------

        def create_hm(cs_only):
            return simeval.get_sim_heatmap(
                self.df,
                self.sim,
                tooltip_fields=self.cols + ['survey_name'],
                cs_only=cs_only,
                sample_size=self.hm_sample_size,
                width=DIV_WIDTH,
                js_on_event=('tap', CustomJS(code="""open_qcomparison(cb_obj['x'], cb_obj['y'])"""))
            )
        hms = [create_hm(cs_only) for cs_only in [True, False]]
        for i in range(len(hms)):
            self.hm_divs[i].text = bh.get_code(hms[i])

        # --- Histograms -----------------------------------------------------------

        def create_hist(cs_only):
            return simeval.get_sim_hist(
                self.df,
                self.sim,
                cs_only=cs_only,
                sample_size=self.hist_sample_size,
                width=DIV_WIDTH
            )
        hists = [create_hist(cs_only) for cs_only in [True, False]]
        for i in range(len(hists)):
            self.hist_divs[i].text = bh.get_code(hists[i])

        # --- Comp divs -----------------------------------------------------------

        comp_divs = simeval.get_comp_divs(self.df, self.sim, sim_cols=self.cols)
        texts = [comp_div.text for comp_div in comp_divs]
        self.comp_div.text = '<br>'.join(texts)

    def __init__(self):
        self.df = load_clean_df()

        # init parameters
        self.hm_sample_size = INIT_HM_SAMPLE_SIZE
        self.hist_sample_size = INIT_HIST_SAMPLE_SIZE
        self.cols = INIT_COLS
        self.sim = INIT_SIM(cols=self.cols)

        # divs holding the charts
        self.hm_divs = [Div(text='', width=DIV_WIDTH) for _ in range(2)]
        self.hist_divs = [Div(text='', width=DIV_WIDTH) for _ in range(2)]
        self.comp_div = Div(text='', width=PAGE_WIDTH)

        # controls
        self.hm_sample_size_ctrl = Slider(title="Heatmap sample size", value=INIT_HM_SAMPLE_SIZE, start=10, end=100, step=5)
        self.hist_sample_size_ctrl = Slider(title="Histogram sample size", value=INIT_HIST_SAMPLE_SIZE, start=10, end=1000, step=10)
        self.sim_ctrl = Select(title="Similarity metric", options=[all_sims.get_sim_name(s) for s in all_sims.SIMS], value=all_sims.get_sim_name(INIT_SIM))
        self.analysed_cols_ctrl = CheckboxGroup(labels=COL_OPTIONS, active=[COL_OPTIONS.index(c) for c in INIT_COLS])
        self.sim_params = CheckboxGroup(labels=SIM_PARAMS, active=list(range(len(SIM_PARAMS))))

        self.submit_btn = Button(label="Submit", button_type="success")
        self.submit_btn.on_click(self.update)

        self.update()

    def get_layout(self):
        sizing_mode = 'fixed'

        inputs = widgetbox(
            [
                self.hm_sample_size_ctrl,
                self.sim_ctrl,
                Div(text='Analysed columns:'), self.analysed_cols_ctrl,
                Div(text='Similarity method params:<br><i>(Not all work for all methods)</i>'), self.sim_params,
                self.submit_btn,

            ],
            sizing_mode=sizing_mode, responsive=True, width=WIDGET_BOX_WIDTH
        )

        charts = layout([
            self.hm_divs,
            self.hist_divs
        ])

        l = layout([
            [inputs, charts],
            [self.comp_div],
            [Div(height=200)]  # some empty space
        ], sizing_mode=sizing_mode)

        return l


def run_app(show=True):
    def modify_doc(doc):
        app = SimEvalApp()

        l = app.get_layout()
        doc.add_root(l)
        doc.title = 'Similarity evaluation dashboard'

    io_loop = IOLoop.current()

    bokeh_app = Application(FunctionHandler(modify_doc))

    server = Server({'/': bokeh_app}, io_loop=io_loop, allow_websocket_origin=["*"])
    server.start()

    if show:
        print('Opening Bokeh application on http://localhost:5006/')
        io_loop.add_callback(server.show, "/")
    io_loop.start()


if __name__ == '__main__':
    run_app()
