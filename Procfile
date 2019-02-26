release: python manage.py migrate --noinput
web: bin/start-nginx gunicorn -c gunicorn.conf pydotorg.wsgi
