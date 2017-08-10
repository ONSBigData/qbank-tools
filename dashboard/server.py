from flask import Flask, render_template, request

from dashboard.model import Model
from dashboard.presentation import Presentation
from dashboard.sim_eval import run_app
from dashboard.settings import *

from bokeh.embed import autoload_server

import support.bokeh_helper as bh
import qsim.sim_analyze as simeval
import qsim.all_sims as all_sims


flask_app = Flask(__name__)
Model.init()


@flask_app.after_request
def add_header(r):  #this is just to prevent caching of JS code
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


# --- flask routes -----------------------------------------------------------


@flask_app.route('/component')
def nresults_div():
    id = request.args.get('id')
    payload = request.args.to_dict()

    if SELECTED_RES_INDEX in payload:
        payload[SELECTED_RES_INDEX] = int(payload[SELECTED_RES_INDEX])
    if SELECTED_BAR_INDEX in payload:
        payload[SELECTED_BAR_INDEX] = int(payload[SELECTED_BAR_INDEX])
    if CS_ONLY in payload:
        payload[CS_ONLY] = payload[CS_ONLY] == 'true'

    comp = None

    if id == 'nresults-div':
        comp = Presentation.get_nresults_div(payload)
    if id == 'res-table':
        comp = Presentation.get_res_table(payload)
    if id == 'bar-chart':
        comp = Presentation.get_bar_chart(payload)
    if id == 'heatmap':
        comp = Presentation.get_heatmap(payload)
    if id == 'comp-div':
        comp = Presentation.get_comp_div(payload)

    return bh.get_code(comp)


@flask_app.route('/qcompare')
def qcompare():
    uuid_x = request.args.get(SELECTED_HM_X)
    uuid_y = request.args.get(SELECTED_HM_Y)
    sim_class_name = request.args.get(SIM)
    sim_class = all_sims.get_sim_class_by_name(sim_class_name)

    qx = Model.base_df.loc[uuid_x].copy()
    qy = Model.base_df.loc[uuid_y].copy()

    comp_df = simeval.create_comp_df(qx, qy, def_sim=sim_class())
    comp_div = simeval.get_comp_div(comp_df, width=PAGE_WIDTH)

    html = render_template(
        'qcompare.html',
        content=bh.get_code(comp_div),
        uuid_x=uuid_x,
        uuid_y=uuid_y,
        sim_name=sim_class_name,
        sims=all_sims.get_sim_names()
    )
    return render_template('frame.html', content=html)

@flask_app.route('/')
@flask_app.route('/simeval')
def simevalroute():
    script = autoload_server(model=None, url=SIM_EVAL_URL)
    html = render_template('simeval.html', script=script)
    return render_template('frame.html', content=html)


@flask_app.route('/qexplore')
def index():
    html = render_template('qexplore.html')
    return render_template('frame.html', content=html)


if __name__ == '__main__':
    import tornado.wsgi
    import tornado.httpserver

    http_server = tornado.httpserver.HTTPServer(
        tornado.wsgi.WSGIContainer(flask_app)
    )
    http_server.listen(5000)
    print('Flask application on http://localhost:5000/')

    run_app(show=False)
