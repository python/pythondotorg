PEP Page Generation
===================

.. _pep_process:

Process Overview
----------------

We are generating the PEP pages by lightly parsing the HTML output from the
`PEP Repository`_ and then cleaning up some post-parsing formatting.

The PEP Page Generation process is as follows:

1. Clone the PEP Repository, if you have not already done so::

      $ git clone https://github.com/python/peps.git

2. From the cloned PEP Repository, run::

      $ make -j

3. Set ``PEP_REPO_PATH`` in ``pydotorg/settings/local.py`` to the location
   of the cloned PEP Repository

4. Run in your ``pythondotorg`` repository::

   $ ./manage.py generate_pep_pages

This process runs periodically via cron to keep the PEP pages up to date.

Management Commands
-------------------

generate_pep_pages
^^^^^^^^^^^^^^^^^^

This Django management command generates ``pages.Page`` objects from the output
of the existing PEP repository generation process. You run it like::

    $ ./manage.py generate_pep_pages

To get verbose output run it like::

    $ ./manage.py generate_pep_pages --verbosity=2

It uses the conversion code in the ``peps.converters`` module in an attempt to
normalize the formatting for display purposes.

dump_pep_pages
^^^^^^^^^^^^^^

This simply dumps our PEP related pages as JSON. The ``dumpdata`` content is
written to ``stdout`` just like a normal ``dumpdata`` command.

.. _PEP Repository: https://github.com/python/peps.git
