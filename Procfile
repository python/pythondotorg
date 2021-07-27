release: python manage.py migrate --noinput
web: python manage.py purge_fastly_cache && bin/start-nginx gunicorn -c gunicorn.conf pydotorg.wsgi
