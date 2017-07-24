from flaskapp import Flask, render_template, jsonify, request
import flaskvis.data_provider as dp
import os


app = Flask(__name__, template_folder=os.path.abspath('/home/ons21553/wspace/qbank/code/flaskvis/static/angular/src'))


@app.route("/search")
def search_questions():
    text = request.args.get('text')
    return jsonify(dp.search_questions(text))


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
