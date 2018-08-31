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
