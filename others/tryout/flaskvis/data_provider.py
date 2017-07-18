import csv
import requests
from common import *


MAX = 100
df = load_clean_df()

def search_questions(text):
    qdf = df[df.all_text.str.contains(text)]

    if qdf.size > MAX:
        qdf = qdf.sample(MAX)

    return qdf.T.to_dict().values()
