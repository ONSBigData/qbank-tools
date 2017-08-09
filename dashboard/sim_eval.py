from bokeh.models import Div, Slider, Select, CheckboxGroup, CustomJS, TextInput, RadioGroup
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
import qsim.qsim_common as qsim
from qsim.sims.tfidf_cos_sim import TfidfCosSim
import qsim.all_sims as all_sims
import datetime
import traceback
import inspect

# --- constants -----------------------------------------------------------

WIDGET_BOX_WIDTH = 250
CHARTS_WIDTH = PAGE_WIDTH - WIDGET_BOX_WIDTH
DIV_WIDTH = CHARTS_WIDTH // 2 - 20

SEARCH_COLS = ['all_text', 'all_context', 'all_inclusions', 'all_exclusions', 'notes']
SEARCH_FIELD = 'search_field'
COL_OPTIONS = [
    'suff_qtext',
    'type',
    'close_seg_text',
    'all_inclusions',
    'all_exclusions',
    'all_context',
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
SIM_PARAMS_CHECKOPTS = [SIM_PARAM_REM_STOP, SIM_PARAM_STEM, SIM_PARAM_ONLY_ALPHA_NUM, SIM_PARAM_LOWER_CASE]

SAMPLE_SIZE_LABEL = 'Sample size (sampling from search results)'

class SimEvalApp:
    def update_chart(self, holding_div, create_chart_code_method):
        holding_div.text = 'Updating...'

        try:
            chart_code = create_chart_code_method()
            holding_div.text = chart_code
        except Exception as e:
            holding_div.text = 'Exception occured: {}\n{}'.format(e, traceback.format_exc())

    def get_sim(self, sim_class, cols):
        signature = inspect.signature(sim_class.__init__)
        sig_args = [p for p in signature.parameters]

        sim_params = {}

        for i, checkbox_param in enumerate(['rem_stopwords', 'stem', 'only_alphanum', 'lower']):
            if checkbox_param in sig_args:
                sim_params[checkbox_param] = i in self.sim_params_ctrl.active

        WV_DICT_MODEL_PARAM = 'wv_dict_model_name'
        if WV_DICT_MODEL_PARAM in sig_args:
            sim_params[WV_DICT_MODEL_PARAM] = [e for e in qsim.W2vModelName][self.wv_dict_model_ctrl.active]

        sim = sim_class(cols=cols, **sim_params)

        return sim

    def update(self):
        search_text = self.search_text_ctrl.value
        df = self.base_df[self.base_df[SEARCH_FIELD].str.contains(search_text)]

        sim_class_name = self.sim_ctrl.value
        sim_class = all_sims.get_sim_class_by_name(sim_class_name)
        cols = [COL_OPTIONS[i] for i in self.analysed_cols_ctrl.active]
        sim = self.get_sim(sim_class, cols)

        sim_input_nres = self.sim_input_nres_ctrl.value
        sim_input_text = self.sim_input_text_ctrl.value
        sim_input_sample_size = self.sim_input_sample_size_ctrl.value

        hm_sample_size = self.hm_sample_size_ctrl.value

        hist_sample_size = self.hist_sample_size_ctrl.value

        bc_sample_size = self.bc_sample_size_ctrl.value
        bc_bars = self.bc_bars_ctrl.value

        spectrum_start = self.spectrum_start_ctrl.value
        spectrum_end = self.spectrum_end_ctrl.value
        spectrum_buckets = self.spectrum_buckets_ctrl.value
        spectrum_bucket_size = self.spectrum_bucket_size_ctrl.value
        spectrum_cs_only = 0 in self.spectrum_cs_only_ctrl.active
        spectrum_sample = self.spectrum_spectrum_sample_size_ctrl.value

        self.top_div.text = '<b style="color: red;">UPDATING STILL IN PROGRESS...</b>'
        for div in self.hm_divs + self.bc_divs + self.hist_divs + [self.comp_div, self.sim_input_div, self.sim_input_desc_div]:
            div.text = 'Awaiting update...'

        # --- Top results -----------------------------------------------------------

        def create_sim_input_div():
            rows = []

            sdf = df.copy()
            if len(sdf) > sim_input_sample_size:
                sdf = sdf.sample(sim_input_sample_size)

            for _, row in sdf.iterrows():
                row_text = sim.preprocess_question(row)
                similarity = sim.get_text_sim(row_text, sim_input_text)
                if similarity is None:
                    similarity = 0

                rows.append((row, similarity))

            rows.sort(key=lambda x: x[1], reverse=True)
            for r in rows:
                r[0]['similarity'] = r[1]

            res_df = pd.DataFrame([r[0] for r in rows[:sim_input_nres]], columns=cols + ['similarity'])

            html = simeval.get_df_html_with_similarities_colored(res_df, similarity_col='similarity')

            return html

        self.update_chart(self.sim_input_div, create_sim_input_div)
        self.update_sim_input_desc_div()

        # --- Heatmaps -----------------------------------------------------------

        def create_hm(cs_only):
            if len(df) == 0:
                return Div(text='No data')

            return simeval.get_sim_heatmap(
                df,
                sim,
                tooltip_fields=cols + ['survey_name', 'uuid'],
                cs_only=cs_only,
                sample_size=hm_sample_size,
                width=DIV_WIDTH,
                js_on_event=('tap', CustomJS(code="""open_qcomparison_from_hm(cb_obj['x'], cb_obj['y'], '{}')""".format(sim_class_name)))
            )

        for i, cs_only in enumerate([True, False]):
            self.update_chart(self.hm_divs[i], lambda: bh.get_code(create_hm(cs_only)))

        # --- Histograms -----------------------------------------------------------

        def create_hist(cs_only):
            if len(df) == 0:
                return Div(text='No data')

            return simeval.get_sim_hist(
                df,
                sim,
                cs_only=cs_only,
                sample_size=hist_sample_size,
                width=DIV_WIDTH
            )
        for i, cs_only in enumerate([True, False]):
            self.update_chart(self.hist_divs[i], lambda: bh.get_code(create_hist(cs_only)))

        # --- Bar chart -----------------------------------------------------------

        def create_bar_chart(cs_only):
            if len(df) == 0:
                return Div(text='No data')

            on_tap_code = """open_qcomparison_from_bar(cb_obj, src, '{}');""".format(sim_class_name)

            return simeval.get_sim_bar_chart(
                df,
                sim,
                cs_only=cs_only,
                sample_size=bc_sample_size,
                bars=bc_bars,
                width=DIV_WIDTH,
                x_rot=1.5,
                tooltip_fields=cols + ['survey_name', 'uuid', 'similarity'],
                js_on_event=('tap', CustomJS(code=on_tap_code))
            )
        for i, cs_only in enumerate([True, False]):
            self.update_chart(self.bc_divs[i], lambda: bh.get_code(create_bar_chart(cs_only)))

        # --- Comp divs -----------------------------------------------------------

        def create_comp_div():
            if len(df) == 0:
                return 'No data'

            comp_divs = simeval.get_comp_divs(
                df,
                sim,
                sim_cols=cols,
                width=CHARTS_WIDTH,
                start=spectrum_start,
                end=spectrum_end,
                buckets=spectrum_buckets,
                bucket_size=spectrum_bucket_size,
                cs_only=spectrum_cs_only,
                sample=spectrum_sample
            )
            texts = [comp_div.text for comp_div in comp_divs]
            return '<br>'.join(texts)

        self.update_chart(self.comp_div, create_comp_div)

        # --- Others -----------------------------------------------------------

        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        self.top_div.text = '<b>Updated at: {} UTC. All results below are for a search results matching "{}". ' \
                            'Searching in a dataset of {} questions</b>'.format(current_time, search_text, len(self.base_df))

    def __init__(self):
        pd.set_option('display.max_colwidth', -1)

        try:
            self.base_df = load_clean_df()
        except:
            fpath = BUNDLED_DATA_DIR + '/clean-light.csv'
            self.base_df = load_clean_df(fpath=fpath)
        self.base_df[SEARCH_FIELD] = self.base_df.apply(lambda row: ' '.join(str(x).lower() for x in row[SEARCH_COLS] if pd.notnull(x)), axis=1)

        # divs holding the charts
        self.sim_input_desc_div = Div(text='', width=CHARTS_WIDTH)
        self.sim_input_div = Div(text='', width=CHARTS_WIDTH)
        self.hm_divs = [Div(text='', width=DIV_WIDTH) for _ in range(2)]
        self.hist_divs = [Div(text='', width=DIV_WIDTH) for _ in range(2)]
        self.bc_divs = [Div(text='', width=DIV_WIDTH) for _ in range(2)]
        self.comp_div = Div(text='', width=CHARTS_WIDTH)

        # other divs
        self.top_div = Div(text='', width=CHARTS_WIDTH)

        # controls
        self.search_text_ctrl = TextInput(title=None, value='', width=WIDGET_BOX_WIDTH - 50)

        self.sim_ctrl = Select(title=None, options=all_sims.get_sim_names(), value=all_sims.get_sim_name(TfidfCosSim))
        self.analysed_cols_ctrl = CheckboxGroup(labels=COL_OPTIONS, active=[COL_OPTIONS.index(c) for c in ['suff_qtext', 'type']])
        self.sim_params_ctrl = CheckboxGroup(labels=list(SIM_PARAMS_CHECKOPTS), active=list(range(len(SIM_PARAMS_CHECKOPTS))))
        self.wv_dict_model_ctrl = RadioGroup(labels=[e.name for e in qsim.W2vModelName], active=0)

        self.sim_input_nres_ctrl = Slider(title="Number of results", value=10, start=1, end=100, step=1)
        self.sim_input_sample_size_ctrl = Slider(title="Sample size", value=1000, start=100, end=len(self.base_df), step=100)
        self.sim_input_text_ctrl = TextInput(title=None, value='', width=WIDGET_BOX_WIDTH - 50)

        self.hm_sample_size_ctrl = Slider(title=SAMPLE_SIZE_LABEL, value=30, start=10, end=50, step=5)

        self.hist_sample_size_ctrl = Slider(title=SAMPLE_SIZE_LABEL, value=30, start=10, end=len(self.base_df), step=10)

        self.bc_sample_size_ctrl = Slider(title=SAMPLE_SIZE_LABEL, value=30, start=10, end=len(self.base_df), step=5)
        self.bc_bars_ctrl = Slider(title="Number of bars", value=10, start=5, end=25, step=1)

        self.spectrum_start_ctrl = Slider(title="from", value=0, start=0, end=1, step=0.01)
        self.spectrum_end_ctrl = Slider(title="to", value=1, start=0, end=1, step=0.01)
        self.spectrum_buckets_ctrl = Slider(title="Number of buckets", value=5, start=1, end=20, step=1)
        self.spectrum_bucket_size_ctrl = Slider(title="Questions per bucket", value=2, start=1, end=10, step=1)
        self.spectrum_cs_only_ctrl = CheckboxGroup(labels=['Cross survey pairs only'], active=[])
        self.spectrum_spectrum_sample_size_ctrl = Slider(title=SAMPLE_SIZE_LABEL, value=30, start=30, end=len(self.base_df), step=10)

        self.submit_btn = Button(label="Update", button_type="success")
        self.submit_btn.on_click(self.update)

        self.update()

    def update_sim_input_desc_div(self):
        desc = 'Top (up to) {} similarities to input: "{}"'.format(self.sim_input_nres_ctrl.value, self.sim_input_text_ctrl.value)

        self.sim_input_desc_div.text = self.get_desc_div(desc).text

    def get_title_div(self, title):
        return Div(text='<hr><h2 class="section_title">{}<h2>'.format(title), width=CHARTS_WIDTH)

    def get_desc_div(self, desc):
        return Div(text='<p class="section_desc">{}<p>'.format(desc), width=CHARTS_WIDTH)

    def get_widget_title_div(self, title):
        return Div(text='<b>{}</b>'.format(title))

    def get_widget_desc_div(self, desc):
        return Div(text='<i>({})</i>'.format(desc))

    def get_widget_label_div(self, label):
        return Div(text='{}'.format(label))

    def get_layout(self):
        sizing_mode = 'fixed'

        inputs = widgetbox(
            [
                self.submit_btn,
                Div(text='<hr>'),

                self.get_widget_title_div('Search'),
                self.get_widget_desc_div('exact match in all texts, inclusions, exclusions, context and notes'),
                self.search_text_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Similarity method'),
                self.get_widget_desc_div('which method should be used to calculate similarities'),
                self.sim_ctrl,
                self.get_widget_label_div('Method parameters (not all params are used with all methods)'),
                self.sim_params_ctrl,
                self.get_widget_label_div('Word vector model (only applicable for AvgWordVec and SentVec methods):'),
                self.wv_dict_model_ctrl,
                self.get_widget_label_div('Analyzed columns:'),
                self.analysed_cols_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Similarities to input section'),
                self.sim_input_text_ctrl,
                self.sim_input_nres_ctrl,
                self.sim_input_sample_size_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Heatmap section'),
                self.hm_sample_size_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Histogram section'),
                self.hist_sample_size_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Bar chart section'),
                self.bc_sample_size_ctrl,
                self.bc_bars_ctrl,
                Div(text='<hr>'),

                self.get_widget_title_div('Example questions pairs section'),
                self.get_widget_label_div('<i>Show pairs with similarities:</i>'),
                self.spectrum_start_ctrl,
                self.spectrum_end_ctrl,
                self.get_widget_label_div('<i>Split the similarity range into buckets:</i>'),
                self.spectrum_buckets_ctrl,
                self.spectrum_bucket_size_ctrl,
                self.spectrum_cs_only_ctrl,
                self.spectrum_spectrum_sample_size_ctrl,
            ],
            sizing_mode=sizing_mode, responsive=True, width=WIDGET_BOX_WIDTH
        )

        self.update_sim_input_desc_div()

        charts = layout([
            [self.top_div],

            [self.get_title_div('Similarities to input')],
            [self.sim_input_desc_div],
            [self.sim_input_div],

            [self.get_title_div('Heatmap of similarities')],
            [self.get_desc_div('This shows a heatmap of similarity scores for chosen sim. method. The entries '
                               'compared are selected as random sample (with chosen sample size) from the search '
                               'results. Click a cell to open up the question pair comparison')],
            self.hm_divs,

            [self.get_title_div('Histogram of similarity scores')],
            [self.get_desc_div('This shows a distribution of similarity scores via a histogram. The used similarity '
                               'scores are computed on a sample (with chosen sample size) from the search results')],
            self.hist_divs,

            [self.get_title_div('Bar chart of most similar question pairs')],
            [self.get_desc_div('This shows the bar chart of most similar question pairs computed on a sample (of chosen'
                               ' sample size) from the search results. Click a bar to open up the question pair '
                               'comparison')],
            self.bc_divs,

            [self.get_title_div('Example question pairs')],
            [self.get_desc_div('This shows examples of question pairs with similarity scores in chosen bands. With '
                               'proper settings, one can quickly see examples of question pairs across the whole '
                               'similarity spectrum')],
            [self.comp_div],
        ])

        l = layout([
            [inputs, charts],
            [Div(height=200)]  # some empty space
        ], sizing_mode=sizing_mode)

        return l



def run_app(show=True):
    def modify_doc(doc):
        app = SimEvalApp()
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
