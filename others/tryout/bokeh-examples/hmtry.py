import numpy as np

from helpers.common import *

matrix = np.loadtxt(DATA_DIR + '/survey-lda-matrix.txt')

print(matrix)

nba = pd.read_csv(("ppg2008.csv"), index_col=0)

# Normalize the data columns and sort.
nba = (nba - nba.mean()) / (nba.max() - nba.min())
nba.sort_values(by = 'PTS', inplace=True)

#
score = []
for x in nba.apply(tuple):
  score.extend(x)

data = {
  'players': list(nba.index) * len(nba.columns),
  'metric':  [item for item in list(nba.columns) for i in range(len(nba.index))],
  'score':   score,
}

print(data)
#
#
# from bokeh.charts import HeatMap, show, output_file
#
# output_file('test.html')
# hm = HeatMap(data, x='metric', y='players',values='score', title='Fruits', stat=None)
# show(hm)