from flask import Flask, render_template, request

from dashboard.model import Model
from dashboard.presentation import Presentation
from dashboard.sim_eval_app import run_app
from dashboard.settings import *

from bokeh.embed import autoload_server

import atexit
import threading

import helpers.bokeh_helper as bh

flask_app = Flask(__name__)
Model.init()
bokeh_thread = None

@atexit.register
def kill_server():
    bokeh_thread.stop()


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
    payload = request.args.to_dict()

    comp_div = Presentation.get_comp_div(payload)

    return render_template('frame.html', content=bh.get_code(comp_div))


@flask_app.route('/simeval')
def simeval():
    script = autoload_server(model=None, url="http://localhost:5006/")
    return render_template('frame.html', content=script)


@flask_app.route('/')
@flask_app.route('/qexplore')
def index():
    html = render_template('qexplore.html')
    return render_template('frame.html', content=html)

if __name__ == '__main__':
    bokeh_thread = threading.Thread(target=run_app, kwargs={'show': False})
    bokeh_thread.start()

    print('Opening Flask application on http://localhost:5000/')
    flask_app.run(port=5000)  # With debug=True, Flask server will auto-reload when there are code changes

