#!/bin/bash

cur_dir=`dirname $0`
source "$cur_dir/deploy-common.sh"

# copy in some data to bundle with the app -----------------------------------
cp -r $CHECKPOINTS_DIR/*.pkl "$cur_dir/../dashboard/bundled_data/"
cp -r $CLEAN_LIGHT_FPATH "$cur_dir/../dashboard/bundled_data/"

cp -r "$cur_dir/../dashboard" "$DEPLOY_ROOT/"
cp -r "$cur_dir/../support" "$DEPLOY_ROOT/"
cp -r "$cur_dir/../qsim" "$DEPLOY_ROOT/"
cp -r "$cur_dir/../json_to_df" "$DEPLOY_ROOT/"
cp $cur_dir/../deploy/* "$DEPLOY_ROOT/"
cp $cur_dir/../requirements.txt "$DEPLOY_ROOT/"


# based on what's deployed, use relevant Procfile -----------------------------------
remote=""
if [[ $1 == 'main' || -z "$1" ]]
then
    cp "$cur_dir/Procfile_main" "$DEPLOY_ROOT/Procfile"
    remote=$QBANK_MAIN
elif [[ $1 == 'sim-eval' ]]
then
    cp "$cur_dir/Procfile_sim_eval" "$DEPLOY_ROOT/Procfile"
    remote=$QBANK_SIM_EVAL
fi

# deploy to Heroku -----------------------------------
cd $DEPLOY_ROOT

git add -A
dt=`date +"%Y-%m-%d_%H-%M"`
git commit -m "$dt"

if [[ $2 == 'local' ]]
then
    heroku local
else
    echo "deploying $remote"
    git push $remote master
    heroku open -a $remote
fi




