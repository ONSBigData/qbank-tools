import json
from json2html import *
from sys import argv

json_in = argv[1]
html_out = argv[2]


with open('/Users/edwari/Documents/Exercises/Python/json/json/mbs-json/'+ json_in, encoding="utf8") as data_file:
    data_202 = json.load(data_file)

raw_html = json2html.convert(json=data_202)

with open('/Users/edwari/Documents/Exercises/Python/json/html-files/mbs-html/' + html_out, 'w') as f:
    f.write(raw_html)

print(raw_html)