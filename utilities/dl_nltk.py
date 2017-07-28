import nltk
import helpers.path_helper as ph
from nltk.downloader import Downloader

nltk.data.path.append(ph.from_root('nltk_data/'))


def dl_nltk():
    TO_DL = ['stopwords', 'punkt']

    dler = Downloader('https://pastebin.com/raw/D3TBY4Mj')

    for to_dl in TO_DL:
        if not nltk.download(to_dl):
            print('Downloading NLTK data from alternative source...')
            if not dler.download(to_dl):
                print('Failed download NLTK data...')

if __name__ == '__main__':
    dl_nltk()
