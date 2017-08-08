import logging
import helpers.log_helper as lg
import qsim.qsim_common as qsim
import pandas as pd


class BaseSim:
    def __init__(self, cols, debug):
        self._debug = debug
        self._lg = lg.get_logger(str(self.__class__.__name__))
        if not debug:
            self._lg.setLevel(logging.WARNING)

        self._cols = cols

    def _get_text_sim(self, x, y):
        raise NotImplementedError

    def _get_similarity_matrix(self, df):
        raise NotImplementedError

    def get_text_sim(self, x, y):
        if pd.isnull(x) or pd.isnull(y) or x == '' or y == '':
            return None

        try:
            return self._get_text_sim(x, y)
        except:
            return None

    def get_similarity_matrix(self, df, cs_only=False):
        sim_matrix = self._get_similarity_matrix(df)

        if cs_only:
            cs_matrix = qsim.get_cross_survey_matrix(df)
            sim_matrix[~cs_matrix] = 0

        return sim_matrix