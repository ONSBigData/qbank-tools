import nltk
from nltk.downloader import Downloader
from support.common import *

nltk.data.path.append(BUNDLED_DATA_DIR + '/nltk_data/')


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
