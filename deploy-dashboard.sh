cp -r ../code/dashboard .
cp -r ../code/helpers .
cp -r ../code/siman .
cp -r ../code/*.py .
cp -r ../code/Procfile .

git add -A
dt=`date +"%Y-%m-%d_%H-%M"`
git commit -m "$dt"

git push heroku master

# echo "python -m nltk.downloader stopwords" | heroku run bash --app=qbank-dashboard --no-tty
# echo "python -m nltk.downloader punkt" | heroku run bash --app=qbank-dashboard --no-tty

heroku open