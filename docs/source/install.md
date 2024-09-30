Installing
==========

As a prerequisite to working on Pythondotorg, Docker, Docker Compose and `make` will need to be installed locally.

```{note}
Docker Compose will be installed by [Docker Mac](https://docs.docker.com/desktop/install/mac-install/) and [Docker for Windows](https://docs.docker.com/desktop/install/windows-install/) automatically.

`make` 	is a build automation tool that automatically builds executebale programs and libraries from source code by reading files called Makefiles. The [`make`](https://www.gnu.org/software/make/) utility comes defaulted with most unix distributions.  
```

Getting started
---------------

To get the Pythondotorg source code, [fork](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) the repository on [GitHub](https://github.com/python/pythondotorg) and [clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) it to your local machine: 

```
git clone git@github.com:YOUR-USERNAME/pythondotorg.git
```

Add a [remote](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/configuring-a-remote-repository-for-a-fork) and [sync](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/syncing-a-fork) regularly to stay current with the repository. 

```
git remote add upstream https://github.com/python/pythondotorg
git checkout main
git fetch upstream 
git merge upstream/main 
```

Installing Docker
-----------------

Install [Docker Engine](https://docs.docker.com/engine/install/) 

```{note}
The best experience for building Pythondotorg on Windows is to use the [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/)(WSL) in combination with both [Docker for Windows](https://docs.docker.com/desktop/install/windows-install/) and [Docker for Linux](https://docs.docker.com/engine/install/).
```

Verify that the Docker installation is successful by running: `docker -v`

Running pythondotorg locally 
----------------------------
Once you have Docker and Docker Compose installed, run:

```
make serve
```

This will pull down all the required docker containers, build the environment for pythondotorg, run migrations, load development fixtures, and start all of the necessary services. 

Once complete, you will see the following in your terminal output:

```
web_1       | Starting development server at http://0.0.0.0:8000/
web_1       | Quit the server with CONTROL-C.
``` 

You can view these results in your local web browser at: <http://localhost:8000>

To reset your local environment, run:

```
make clean
```

To apply migrations, run: 

``` 
make migrate
```

To generate new migrations, run: 

```
make migrations
```

You can also run arbitrary Django management commands via:

```
make manage <NAME_OF_COMMAND>
```

This is a simple wrapper around running `python manage.py` in the container, all arguments passed to `make manage` will be passed through.


   
Manual setup
------------

First, install [PostgreSQL](https://www.postgresql.org/download/) on your machine and run it. *pythondotorg* currently uses Postgres 15.x.

Then clone the repository:

```
$ git clone git://github.com/python/pythondotorg.git
```

Then create a virtual environment:

```
$ python3 -m venv venv
```

And then you'll need to install dependencies. You don't need to use `pip3` inside a Python 3 virtual environment:

```
$ pip install -r dev-requirements.txt
```

*pythondotorg* will look for a PostgreSQL database named `pythondotorg` by default. Run the following command to create a new database:

```
$ createdb pythondotorg -E utf-8 -l en_US.UTF-8
```

````{note}
If the above command fails to create a database and you see an error message similar to:

```
createdb: database creation failed: ERROR:  permission denied to create database
```

Use the following command to create a database with *postgres* user as the owner:

```
$ sudo -u postgres createdb pythondotorg -E utf-8 -l en_US.UTF-8
```

Note that this solution may not work if you've installed PostgreSQL via Homebrew.

If you get an error like this:

```
createdb: database creation failed: ERROR:  new collation (en_US.UTF-8) is incompatible with the collation of the template database (en_GB.UTF-8)
```

Then you will have to change the value of the `-l` option to what your database was set up with initially.
````

To change database configuration, you can add the following setting to `pydotorg/settings/local.py` (or you can use the `DATABASE_URL` environment variable):

```
DATABASES = {
    'default': dj_database_url.parse('postgres:///your_database_name'),
}
```

If you prefer to use a simpler setup for your database you can use SQLite. Set the `DATABASE_URL` environment variable for the current terminal session:

```
$ export DATABASE_URL="sqlite:///pythondotorg.db"
```

```{note}
If you prefer to set this variable in a more permanent way add the above line in your `.bashrc` file. Then it will be set for all terminal sessions in your system.
```

Whichever database type you chose, now it's time to run migrations:

```
$ ./manage.py migrate
```

To compile and compress static media, you will need *compass* and *yui-compressor*:

```
$ gem install bundler
$ bundle install
```

```{note}
To install *yui-compressor*, use your OS's package manager or download it directly then add the executable to your `PATH`.
```

To create initial data for the most used applications, run:

```
$ ./manage.py create_initial_data
```

See `pythondotorg`[create_initial_data](https://pythondotorg.readthedocs.io/commands.html#command-create-initial-data) for the command options to specify while creating initial data.

Finally, start the development server:

```
$ ./manage.py runserver
```

Optional: Install Elasticsearch
-------------------------------

The search feature in Python.org uses Elasticsearch engine. If you want to test out this feature, you will need to install [Elasticsearch](https://www.elastic.co/downloads/elasticsearch).

Once you have it installed, update the URL value of `HAYSTACK_CONNECTIONS` settings in `pydotorg/settings/local.py` to your local ElasticSearch server.

Generating CSS files automatically
----------------------------------

```{warning}
When editing frontend styles, ensure you ONLY edit the `.scss` files. 

These will then be compiled into `.css` files automatically.
```

Static files are automatically compiled inside the [Docker Compose `static` container](../../docker-compose.yml)
when running `make serve`.

When your pull request has stylesheet changes, commit the `.scss` files and the compiled `.css` files. 
Otherwise, ignore committing and pushing the `.css` files.

Running tests
-------------

To run the test suite:

```
$ ./manage.py test
```

To generate coverage report:

```
$ coverage run manage.py test
$ coverage report
```

Generate an HTML report with `coverage html` if you like.

Useful commands
---------------

-   Create a super user (for a new DB):

```
    $ ./manage.py createsuperuser
```

-   Want to save some data from your DB before nuking it, and then load it back in?:

```
    $ ./manage.py dumpdata --format=json --indent=4 $APPNAME > fixtures/$APPNAME.json
```


