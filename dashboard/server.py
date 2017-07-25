from flask import Flask, render_template, request
from bokeh.embed import components

from dashboard.model import Model
from dashboard.presentation import Presentation

app = Flask(__name__)

Model.init()

@app.after_request
def add_header(r):  #this is just to prevent caching of JS code
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r


@app.route('/search-for-kw', methods=['POST'])
def search_for_kw():
    search_kw = request.form.get("kw")
    if search_kw is not None:
        Model.search_for_kw(search_kw)

    return 'OK'


@app.route('/select-res', methods=['POST'])
def select_res():
    index = request.form.get("index")
    if index is not None:
        Model.select_search_res(int(index))

    return 'OK'


@app.route('/select-bar', methods=['POST'])
def select_bar():
    index = request.form.get("index")
    if index is not None:
        Model.select_bar(int(index))

    return 'OK'


@app.route('/select-hm-cell', methods=['POST'])
def select_hm_cell():
    uuid_x = request.form.get('uuid_x')
    uuid_y = request.form.get('uuid_y')

    if uuid_x is not None and uuid_y is not None:
        Model.select_hm_cell(uuid_x, uuid_y)

    return 'OK'


@app.route('/toggle-cs-only', methods=['POST'])
def toggle_cs_only():
    value = request.form.get('cs_only') == 'true'

    Model.only_cross_survey = value
    Model.update_heatmap_df()
    Model.update_bar_chart_df()

    return 'OK'


@app.route('/component')
def nresults_div():
    id = request.args.get('id')

    comp = None

    if id == 'nresults-div':
        comp = Presentation.get_nresults_div()
    if id == 'res-table':
        comp = Presentation.get_res_table()
    if id == 'bar-chart':
        comp = Presentation.get_bar_chart()
    if id == 'heatmap':
        comp = Presentation.get_heatmap()
    if id == 'comp-div':
        comp = Presentation.get_comp_div()

    def get_code(obj):
        script, div = components(obj)

        return script + ' ' + div

    return get_code(comp)


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(port=5000, debug=True)  # With debug=True, Flask server will auto-reload when there are code changes

