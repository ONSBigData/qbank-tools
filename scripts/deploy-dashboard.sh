cp -r ../code/dashboard .
cp -r ../code/helpers .
cp -r ../code/siman .
cp -r ../code/utilities .
cp -r ../code/Procfile .
cp -r ../code/conda-requirements.txt .

#heroku local

git add -A
dt=`date +"%Y-%m-%d_%H-%M"`
git commit -m "$dt"

heroku ps:scale web=0

git push heroku master

##heroku run python 'scripts/dl_nltk.py' --app=qbank-dashboard

heroku ps:scale web=1

heroku open