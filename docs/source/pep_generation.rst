PEP Page Generation
===================

.. _pep_process:

Process Overview
----------------

We are generating the PEP pages by lightly parsing and cleaning up the HTML output from the `PEP Mercurial Repository <http://hg.python.org/peps/>`_.

The process is as follows:

1. Clone and/or update the PEP repo located in `settings.PEP_REPO_PATH` to the latest revision.
2. Run `pep2html.py`
3. Run `genpepindex.py`
4. Once all PEP HTML pages are generated, run `./manage.py generate_pep_pages`

.. note:: Steps 2 and 3 currently must be run using Python 2 and **NOT** Python 3 like the rest of Python.org

This process will be run periodically via cron to keep the PEP pages up to date.

Management Commands
-------------------

generate_pep_pages
^^^^^^^^^^^^^^^^^^

This Django management command generates `pages.Page` objects based on the output of the existing PEP repository
generation process. You run it like::

    ./manage.py generate_pep_pages

To get verbose output run it like::

    ./manage.py generate_pep_pages --verbosity=2

It uses the conversion code in the `peps.converters` module in an attempt to normalize the formatting for display
purposes.

dump_pep_pages
^^^^^^^^^^^^^^

This simply dumps our PEP related pages as JSON like dumpdata would do with a --pks options if the site was using
Django 1.6 or newer. The dumpdata content is written to stdout just like a normal dumpdata command.
