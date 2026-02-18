python.org
==========

.. image:: https://github.com/python/pythondotorg/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/python/pythondotorg/actions/workflows/ci.yml

The codebase behind `python.org <https://www.python.org>`_. It's a Django 5.2
application backed by PostgreSQL, Redis, and Celery, with Elasticsearch
powering site search via Haystack.

Quick start
-----------

.. code-block:: bash

   make serve

Then visit http://localhost:8000. See :doc:`install.md` for prerequisites and
full setup instructions.

Make targets
------------

:``serve``: Start the full stack (Postgres, Redis, web, worker, static).
:``test``: Run the test suite.
:``migrations``: Generate migrations from model changes.
:``migrate``: Apply pending migrations.
:``manage <cmd>``: Run any Django management command.
:``shell``: Open the Django interactive shell.
:``docker_shell``: Open a bash session inside the web container.
:``clean``: Tear down containers and reset state.
:``lint``: Run the ruff linter with ``--fix``.
:``fmt``: Run the ruff formatter.
:``ci``: Run lint, fmt, then tests in sequence.

Apps at a glance
----------------

**Content & CMS**
   ``pages``, ``blogs``, ``boxes``, ``codesamples``, ``successstories``,
   ``minutes``, ``banners``

**Community**
   ``events``, ``jobs``, ``community``, ``companies``, ``work_groups``

**Core**
   ``downloads``, ``sponsors``, ``nominations``, ``users``, ``mailing``

**Base**
   ``cms`` — shared model mixins (``ContentManageable``, ``NameSlugModel``,
   etc.) used across most apps.

Docker services
---------------

The ``docker-compose.yml`` defines five services:

- **postgres** — PostgreSQL 15.3 database.
- **redis** — Redis 7 for caching and Celery broker.
- **web** — Django dev server on port 8000.
- **worker** — Celery worker with beat scheduler (``django-celery-beat``).
- **static** — SCSS compilation and static asset pipeline.

Testing & CI
------------

Run the full suite:

.. code-block:: bash

   make test

Run tests for a single app:

.. code-block:: bash

   make manage test events

CI (GitHub Actions) enforces a 75% coverage minimum and checks for missing
migrations. See :doc:`contributing` for PR expectations.

.. toctree::
   :maxdepth: 2
   :hidden:

   install.md
   contributing
   administration
   commands

:Source code: https://github.com/python/pythondotorg
:Issue tracker: https://github.com/python/pythondotorg/issues
:License: Apache License
