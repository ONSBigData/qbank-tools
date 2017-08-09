#!/bin/bash

cur_dir=`dirname $0`
source "$cur_dir/deploy-common.sh"

/bin/bash $cur_dir/deploy.sh $QBANK_MAIN
/bin/bash $cur_dir/deploy.sh $QBANK_SIM_EVAL