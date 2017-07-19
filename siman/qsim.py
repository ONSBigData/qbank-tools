from nltk.corpus import stopwords

def get_stop_words():
    sws = set(stopwords.words('english'))
    for x in ['survey', 'section', 'business', 'period', 'total', 'service', 'services']:
        sws.add(x)

    return sws