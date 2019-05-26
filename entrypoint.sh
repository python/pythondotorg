#!/usr/bin/env sh

if [[ "${DB_TYPE}" == "postgres" ]]; then
  echo "Waiting for Postgres..."

  while ! nc -z $DB_HOST $DB_PORT; do
    sleep 0.1
  done

  echo "PostgreSQL started"
fi

python manage.py migrate
yes | python manage.py create_initial_data

exec "$@"
