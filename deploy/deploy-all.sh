#!/bin/bash

cur_dir=`dirname $0`
source "$cur_dir/deploy-common.sh"

/bin/bash $cur_dir/deploy.sh main
/bin/bash $cur_dir/deploy.sh sim-eval