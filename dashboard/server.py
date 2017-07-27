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


@app.route('/component')
def nresults_div():
    id = request.args.get('id')
    payload = request.args.to_dict()

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

    def get_code(obj):
        script, div = components(obj)

        return script + ' ' + div

    return get_code(comp)


@app.route('/')
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(port=5000)  # With debug=True, Flask server will auto-reload when there are code changes

