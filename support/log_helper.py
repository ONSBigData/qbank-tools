import support.general_helper as general_helper
import support.path_helper as path_helper
import logging as lg
import sys


DEFAULT_LOGGER = 'qbank'
LOG_DIR = path_helper.from_root('log/', create_if_needed=True)

FILE_NAME = '{}/{}_{}.log'.format(
    LOG_DIR,
    general_helper.get_date(),
    general_helper.get_time())

def get_logger(name=DEFAULT_LOGGER):
    logger = lg.getLogger(name)

    if len(logger.handlers) == 0:
        stream_handler = lg.StreamHandler(sys.stdout)
        file_handler = lg.FileHandler(FILE_NAME)
        formatter = lg.Formatter('%(asctime)s  %(levelname)8s  %(name)35s >>> %(message)s')
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(lg.DEBUG)
        logger.debug('Logger {} initialized'.format(name))

    return logger


qbank = get_logger(DEFAULT_LOGGER)  # could be used as general logger
