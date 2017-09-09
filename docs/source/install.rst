Installing
==========

Here are two ways to hack on python.org:

1. :ref:`vagrant-setup`
2. :ref:`manual-setup`

.. _vagrant-setup:

Easy setup using Vagrant
------------------------

::

    $ vagrant up
    $ vagrant ssh
    # go to pythondotorg/ directory and activate virtualenv, then run
    $ ./manage.py runserver 0.0.0.0:8000
    # on your local shell
    $ google-chrome http://localhost:8001/

The box will be provisioned by Ansible_ 1.9.6 with Python 3.4, a virtualenv
set up with requirements installed, and a database ready to use.

The box also creates a superuser with username ``cbiggles`` for you. However, you
will need to set a password before using it::

    $ vagrant ssh
    $ cd pythondotorg
    $ . venv/bin/activate
    $ ./manage.py changepassword cbiggles

.. note::

   You will also need to run ``./manage.py create_initial_data`` to create
   initial data for the most used applications.

.. _Ansible: http://docs.ansible.com/ansible/intro_installation.html

.. _manual-setup:

Manual setup
------------

First, clone the repository::

    $ git clone git://github.com/python/pythondotorg.git

Then create a virtual environment::

    $ python3.4 -m venv venv

And then you'll need to install dependencies::

    $ pip install -r dev-requirements.txt

*pythondotorg* will look for a PostgreSQL database named ``pythondotorg`` by
default. Run the following command to create a new database::

    $ createdb pythondotorg -E utf-8 -l en_US.UTF-8

To change database configuration, you can add the following setting to
``pydotorg/settings/local.py`` (or you can use the ``DATABASE_URL`` environment
variable)::

    DATABASES = {
        'default': dj_database_url.parse('postgres:///your_database_name')
    }

Now it's time to run migrations::

    $ ./manage.py migrate

To compile and compress static media, you will need *compass* and
*yui-compressor*::

    $ gem install bundler
    $ bundle install

.. note::

   To install *yui-compressor*, use your OS's package manager or download it
   directly then add the executable to your ``PATH``.

To create initial data for the most used applications, run::

    $ ./manage.py create_initial_data

Finally, start the development server::

    $ ./manage.py runserver


Optional: Install Elasticsearch
-------------------------------

The search feature in Python.org uses Elasticsearch engine.  If you want to
test out this feature, you will need to install Elasticsearch_.

Once you have it installed, update the URL value of ``HAYSTACK_CONNECTIONS``
settings in ``pydotorg/settings/local.py`` to your local ElasticSearch server.

.. _Elasticsearch: https://www.elastic.co/downloads/elasticsearch


Generating CSS files automatically
----------------------------------

Due to performance issues of django-pipeline_, we are using a dummy compiler
``pydotorg.compilers.DummySASSCompiler`` in development mode. To generate CSS
files, use ``sass`` itself in a separate terminal window::

    $ cd static
    $ sass --compass --scss -I $(dirname $(dirname $(gem which susy))) --trace --watch sass/style.scss:sass/style.css

.. _django-pipeline: https://github.com/cyberdelia/django-pipeline/issues/313


Running tests
-------------

To run the test suite::

    $ ./manage.py test

To generate coverage report::

    $ coverage run manage.py test
    $ coverage report

Generate an HTML report with ``coverage html`` if you like.


Useful commands
---------------

* Create a super user (for a new DB)::

      $ ./manage.py createsuperuser

* Want to save some data from your DB before nuking it, and then load it back
  in?::

      $ ./manage.py dumpdata --format=json --indent=4 $APPNAME > fixtures/$APPNAME.json
