python.org
==========

[![Build Status](https://next.travis-ci.com/proevo/pythondotorg.png?token=rzZWMj7qjjfKoW211CMz&branch=master)](https://next.travis-ci.com/proevo/pythondotorg)

The new python.org!

Getting going
-------------

Requires :sparkles:Python 3.3!:sparkles: (`brew install python3`)

You'll want a virtualenv. Python 3.3 actually includes virtualenv built-in,
so you can do:

    $ pyvenv-3.3 <env>
    $ source <env>/bin/activate
    (etc)

But you can also use your existing virtualenv/wrapper:

    $ mkvirtualenv --python=python3.3 <env>

And then it's the standard:

    $ pip install -r requirements.txt
    $ ./manage.py syncdb

You may need to specify the pip version, even with the virtualenv activated:

    $ pip-3.3 install -r requirements.txt

This expects a local database named "python.org". If you need to change it:

    $ export DATABASE_URL=postgres://user:pass@host:port/dbname

To compile and compress static media, you will need compass and yui-compressor:

    $ gem install bundler
    $ bundle install
    $ brew install yuicompressor

NOTE: On OSX you may need to adjust your PATH to be able to find the sass binary, etc.

### Python 3.3 and OSX 10.8.2

Homebrew's recipe for python3.3 has some difficulty installing distribute
and pip in a virtualenv. The [python.org installer for OSX](http://www.python.org/download/)
may work better, if you're having trouble.

### Using Vagrant

You can ignore the above instructions by using [Vagrant](http://www.vagrantup.com/). After installing:

    $ vagrant up
    $ vagrant ssh

The box will be provisioned by Chef with Python 3.3, a virtualenv set up with requirements installed, and a database ready to use. The virtualenv is activated upon login. You will need to run `./manage.py createsuperuser` to use the admin.

Running tests
-------------

Install `coverage` (`pip install coverage`), then::

    $ coverage run manage.py test
    $ coverage report

Generate an HTML report with `coverage html` if you like.


------------


Cheatsheet for Front End devs that know enough to be dangerous
-------------

But not really enough to remember all these CLI commands by heart. 

### Spinning up a VM

1. Open Terminal.app
2. `cd ~/github/python`
3. `source ENV/bin/activate`
4. Maybe you need to install requirements? `pip install -r requirements.txt`
5. `export DATABASE_URL="postgres://localhost/python.org"`
6. `./manage.py runserver 0.0.0.0:8000` (or whatever port you run at)

### Nuke the DB!

1. Do steps 1-4 above.
2. `export PATH="/Applications/Postgres.app/Contents/MacOS/bin:$PATH"`
3. `dropdb python.org`
4. `createdb python.org`
5. `./manage.py syncdb`
6. `./manage.py migrate`
7. Install data below if you like. 

### Other Useful Commands

Create a super user (for a new DB):
`./manage.py createsuperuser`

Install Meeting Minutes:
`./manage.py import_psf_meeting_notes`

Want to save some data from your DB before nuking it, and then load it back in? 
`./manage.py dumpdata --format=json --indent=4 [app-name] > fixtures/[app-name].json`

Load a specific fixture: 
`./manage.py loaddata fixtures/[name].json`

Load all fixture files: 
`find ./fixtures -name "*.json" -exec ./manage.py loaddata {} \;`

List All the active DBs: 
`psql -U postgres -c '\l'`
esq from window... `q`

If PostGres can't connect to your localhost DB, put this in pydotorg/local.py:
`DATABASES = {
    'default': dj_database_url.config(default='postgres://localhost:{port#}/{DBName, probably python.org}')
}`