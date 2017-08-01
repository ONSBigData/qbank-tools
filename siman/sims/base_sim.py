import logging
import helpers.log_helper as lg


class BaseSim:
    def __init__(self, cols, debug):
        self._debug = debug
        self._lg = lg.get_logger(str(self.__class__.__name__))
        if not debug:
            self._lg.setLevel(logging.WARNING)

        self._cols = cols

    def get_similarity_matrix(self, df):
        raise NotImplementedError