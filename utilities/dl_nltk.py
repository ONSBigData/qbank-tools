import nltk
from nltk.downloader import Downloader

def dl_nltk():
    TO_DL = ['stopwords', 'punkt']

    dler = Downloader('https://pastebin.com/raw/D3TBY4Mj')

    for to_dl in TO_DL:
        if not nltk.download(to_dl):
            dler.download(to_dl)

if __name__ == '__main__':
    dl_nltk()
