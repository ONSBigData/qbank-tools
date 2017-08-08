#!/bin/bash

cur_dir=`dirname $0`
source "$cur_dir/deploy-common.sh"

rm -rf $DEPLOY_ROOT
mkdir $DEPLOY_ROOT
cd $DEPLOY_ROOT
git init

heroku apps:destroy $QBANK_MAIN --confirm $QBANK_MAIN
heroku apps:destroy $QBANK_SIM_EVAL --confirm $QBANK_SIM_EVAL
heroku create $QBANK_MAIN --buildpack https://github.com/arose13/conda-buildpack.git
heroku create $QBANK_SIM_EVAL --buildpack https://github.com/arose13/conda-buildpack.git

git remote add $QBANK_MAIN https://git.heroku.com/$QBANK_MAIN.git
git remote add $QBANK_SIM_EVAL https://git.heroku.com/$QBANK_SIM_EVAL.git
