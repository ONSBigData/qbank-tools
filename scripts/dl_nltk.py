import nltk
from nltk.downloader import Downloader

TO_DL = ['stopwords', 'punkt']

try:
    for to_dl in TO_DL:
        nltk.download(to_dl)
except:
    dler = Downloader('https://pastebin.com/raw/D3TBY4Mj')
    for to_dl in TO_DL:
        dler.download(to_dl)
