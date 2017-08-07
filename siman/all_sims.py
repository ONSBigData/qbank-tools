from siman.sims.tfidf_cos import TfidfCosSim
from siman.sims.exact import ExactSim
from siman.sims.avg_wv import AvgWvSim
from siman.sims.jaro import JaroSim
from siman.sims.sent2vec import Sent2VecSim

SIMS = [TfidfCosSim, ExactSim, AvgWvSim, JaroSim, Sent2VecSim]


def get_sim_names():
    return [get_sim_name(s) for s in SIMS]

def get_sim_name(sim):
    return sim.__name__


def get_sim_class_by_name(sim_name):
    return [s for s in SIMS if get_sim_name(s) == sim_name][0]