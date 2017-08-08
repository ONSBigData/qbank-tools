from qsim.sims.tfidf_cos_sim import TfidfCosSim
from qsim.sims.exact_sim import ExactSim
from qsim.sims.avg_word_vec_sim import AvgWordVecSim
from qsim.sims.jaro_sim import JaroSim
from qsim.sims.sent_vec_sim import SentVecSim

SIMS = [TfidfCosSim, ExactSim, AvgWordVecSim, JaroSim, SentVecSim]


def get_sim_names():
    return [get_sim_name(s) for s in SIMS]


def get_sim_name(sim):
    return sim.__name__


def get_sim_class_by_name(sim_name):
    return [s for s in SIMS if get_sim_name(s) == sim_name][0]
