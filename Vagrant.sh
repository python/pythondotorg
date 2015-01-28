#!/usr/bin/env bash
set -o pipefail
set -e
set -x

########
# Update

# Add ElasticSearch repository
wget -qO - https://packages.elasticsearch.org/GPG-KEY-elasticsearch | sudo apt-key add -
sudo add-apt-repository "deb http://packages.elasticsearch.org/elasticsearch/1.4/debian stable main"

sudo apt-get update
sudo apt-get --yes dist-upgrade
sudo apt-get -y upgrade

#######
# Basic
sudo apt-get -y -q install build-essential
sudo apt-get -y -q install git

##################
#  Python
sudo apt-get -y -q install python3-dev
sudo apt-get -y -q install python3-setuptools
sudo apt-get -y -q install python3-pip
sudo apt-get -y -q install python-virtualenv

##########
# Postgres
sudo apt-get -y -q install postgresql
sudo apt-get -y -q install postgresql-client
sudo apt-get -y -q install postgresql-contrib
sudo apt-get -y -q install libpq-dev

################
# Setup Database

DBUSER=vagrant
DBPASS=vagrant
DBNAME=pythondotorg
DBTEST=pythondotorg_test  # Django test database

# If dbuser does not exist, create it
if [ $(sudo -u postgres psql -tc "SELECT count(*) FROM pg_user WHERE usename='${DBUSER}'") == 0 ]; then
  sudo -u postgres psql -c "CREATE ROLE ${DBUSER} WITH PASSWORD '${DBPASS}' LOGIN SUPERUSER"
fi

if [ $(sudo -u postgres psql -tc "SELECT count(*) FROM pg_database WHERE datname='${DBNAME}'") == 0 ]; then
  sudo -u postgres createdb -O ${DBUSER} ${DBNAME}
fi

if [ $(sudo -u postgres psql -tc "SELECT count(*) FROM pg_database WHERE datname='${DBTEST}'") == 0 ]; then
  sudo -u postgres createdb -O ${DBUSER} ${DBTEST}
fi

######################
# Project dependencies
sudo apt-get -y -q install libxml2-dev
sudo apt-get -y -q install libxslt-dev
sudo apt-get -y -q install ruby1.9.1
sudo apt-get -y -q install ruby-bundler

sudo apt-get install -y -q openjdk-7-jre-headless
sudo apt-get install -y -q elasticsearch
sudo update-rc.d elasticsearch defaults 95 10 # Start ElasticSearch on boot
sudo /etc/init.d/elasticsearch start

###############
# Setup Project

# Configure bash to activate virtualenv and cd to project on login/ssh
if ! grep -q "PYTHONDOTORG" .bashrc
then
  cat >> .bashrc <<EOF
# PYTHONDOTORG: Activate venv and go to project
source env/bin/activate
cd pythondotorg
EOF
fi

# Create virtualenv if don't exists
test ! -d env && virtualenv -p python3 env

source env/bin/activate
cd pythondotorg

# Install pip-accel to speed up installing packages
# This avoid re-downloads and re-builds
pip install pip-accel

# Install project requirements
pip-accel install -r requirements.txt
bundle install

# Apply schema
./manage.py syncdb --noinput
./manage.py migrate --noinput

# Load data to database
find ./fixtures -name "*.json" -exec ./manage.py loaddata {} \;

# Load calendar events from the web
./manage.py import_ics_calendars

# Build search index
./manage.py update_index

# HACK: Create an admin user WITHOUT asking for password.
python -<<EOF
from django.core.management import setup_environ
from pydotorg.settings import local
setup_environ(local)
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
  User.objects.create_superuser('admin', 'admin@email.me', 'admin')
EOF
