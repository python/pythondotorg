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

4. Generate PEP pages in your ``pythondotorg`` repository 
   (More details at :ref:`command-generate-pep-pages`). You can run like::

   $ ./manage.py generate_pep_pages

This process runs periodically via cron to keep the PEP pages up to date.
   
See :ref:`management-commands` for all management commands.

.. _PEP Repository: https://github.com/python/peps.git