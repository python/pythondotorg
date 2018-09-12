.. _management-commands:

Management Commands
===================

.. _command-create-initial-data:

create_initial_data
-------------------

This command creates initial data for the app using factories. 
You can run it like::

    $ ./manage.py create_initial_data

If you want to remove all existing data in the database before creating 
new one, specify :option:`--flush` option::

    $ ./manage.py create_initial_data --flush

If you want to specify any label to create any app specific data, 
specify :option:`--app-label` option::

    $ ./manage.py create_initial_data --app-label jobs

Command-line options
^^^^^^^^^^^^^^^^^^^^

.. program:: manage.py create_initial_data

.. option:: --flush

   Remove existing data in the database before creating new data.

.. option:: --app-label <app_label>

   Create initial data with the *app_label* provided.

.. _command-generate-pep-pages:

generate_pep_pages
------------------

This command generates ``pages.Page`` objects from the output
of the existing PEP repository generation process. You run it like::

    $ ./manage.py generate_pep_pages

To get verbose output, specify ``--verbosity`` option::

    $ ./manage.py generate_pep_pages --verbosity=2

It uses the conversion code in the ``peps/converters.py`` file, in an
attempt to normalize the formatting for display purposes.

.. _command-dump-pep-pages:

dump_pep_pages
--------------

This command simply dumps our PEP related pages as JSON to :attr:`sys.stdout`.
You can run like::

    $ ./manage.py dump_pep_pages
