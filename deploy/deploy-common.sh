#!/bin/bash

cur_dir=`dirname $0`

# update these as necessary
CHECKPOINTS_DIR=$cur_dir/../../data/checkpoints
CLEAN_LIGHT_FPATH=$cur_dir/../../data/clean-light.csv

DEPLOY_ROOT="$cur_dir/../deploydir"
QBANK_MAIN='qbank-main'
QBANK_SIM_EVAL='qbank-sim-eval'