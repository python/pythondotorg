#!/usr/bin/env sh

python manage.py migrate --no-input
yes | python manage.py create_initial_data

exec "$@"
