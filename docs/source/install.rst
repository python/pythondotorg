Installing
==========

Using Vagrant
-------------

You can ignore the below instructions by using Vagrant. After installing::

    $ vagrant up
    $ vagrant ssh

The box will be provisioned by Chef with Python 3.3, a virtualenv set up with
requirements installed, and a database ready to use. The virtualenv is
activated upon login.

.. note:: You will need to run ``./manage.py createsuperuser`` to use the admin.


Getting started
---------------

You'll want a virtualenv. Python 3.3 actually includes virtualenv built-in, so
you can do::

    $ pyvenv-3.3 <env>
    $ source <env>/bin/activate

But you can also use your existing virtualenv and virtualenvwrapper::

    $ virtualenv --python=python3.3 <env>
    $ mkvirtualenv --python=python3.3 <env>

And then you'll need to install dependencies::

    $ pip install -r dev-requirements.txt

If you want to install the default Read the Docs theme, you can do::

    $ pip install -r docs-requirements.txt

.. note:: For deployment, you can just use ``requirements.txt``.

In your development environment, you won't need a production ready database, so
you can use Sqlite3::

    $ export DATABASE_URL=sqlite:///pydotorg.db

You can also add the following setting to ``pydotorg/settings/local.py``::

    DATABASES = {
        'default': dj_database_url.parse('sqlite:///pydotorg.db')
    }

Not it's time to run migrations::

    $ ./manage.py migrate

To compile and compress static media, you will need *compass* and
*yui-compressor*::

    $ gem install bundler
    $ bundle install

.. note::

   To install *yui-compressor*, use your OS's package manager or download it
   directly then add the executable to your ``PATH``.

To load all fixture files::

    $ invoke load_fixtures

or::

    $ ./manage.py loaddata fixtures/*.json

If you want to load a specific fixture, use its application name::

    $ ./manage.py loaddata downloads boxes

Finally, start the development server::

    $ ./manage.py runserver


Running tests
-------------

To run the test suite::

    $ ./manage.py test

To generate coverage report::

    $ coverage run manage.py test
    $ coverage report

Generate an HTML report with ``coverage html`` if you like.


Building documentation
----------------------

To build this documentation locally::

    $ make -C docs/ htmlview

If you don't want to open the browser automatically, you can do::

    $ make -C docs/ html


Useful commands
---------------

* Create a super user (for a new DB)::

      $ ./manage.py createsuperuser

* Want to save some data from your DB before nuking it, and then load it back
  in?::

      $ ./manage.py dumpdata --format=json --indent=4 $APPNAME > fixtures/$APPNAME.json


Troubleshooting
---------------

If you hit an error getting this repo setup, file a pull request with helpful
information so others don't have similar problems.

Python 3.3 and OSX 10.8.2
^^^^^^^^^^^^^^^^^^^^^^^^^

Homebrew's recipe for Python 3.3 has some difficulty installing distribute
and pip in a virtualenv. The `python.org installer for OSX <https://www.python.org/download/>`_
may work better, if you're having trouble.

Freetype not found on OSX
^^^^^^^^^^^^^^^^^^^^^^^^^

::

    _imagingft.c:60:10: fatal error: 'freetype/fterrors.h' file not found
    #include <freetype/fterrors.h>
             ^
    1 error generated.
    error: command 'clang' failed with exit status 1

If you've installed *freetype* (``brew install freetype``), you may need
to symlink version 2 into location for version 1 as mentioned by `this
Stack Overflow
question <http://stackoverflow.com/questions/20325473/error-installing-python-image-library-using-pip-on-mac-os-x-10-9>`_.

Freetype 2.5.3 is known to work with this repository::

    $ ln -s /usr/local/include/freetype2 /usr/local/include/freetype
