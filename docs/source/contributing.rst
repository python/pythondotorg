Contributing
============

Bugs
----

File bugs as issues on GitHub_. Check existing issues first to avoid
duplicates.

Code
----

The source is licensed under the `Apache 2 license <license_>`_. Fork the
pythondotorg_ repository, create a branch, and open a pull request.

See :doc:`install` to set up your development environment.

Before submitting a PR
~~~~~~~~~~~~~~~~~~~~~~

1. Run the test suite and make sure it passes:

   .. code-block:: bash

      make test

2. Run the linter and formatter:

   .. code-block:: bash

      make lint
      make fmt

3. If you changed models, check for missing migrations:

   .. code-block:: bash

      make migrations

4. Write tests for any new or changed code.

5. Keep pull requests focused — one issue or feature per PR is easier to
   review than a large PR that touches many parts of the system.

6. Include a clear description of what your PR does and why.

CI checks
~~~~~~~~~

GitHub Actions runs on every push and pull request. It will:

- Check for ungenerated migrations (``makemigrations --check --dry-run``)
- Run the full test suite
- Enforce a **75% minimum test coverage** threshold

Dependencies are installed with ``uv sync --locked`` using ``uv.lock``.
After changing dependencies in ``pyproject.toml``, run ``uv lock`` and include
both files in your pull request. Dependabot updates them together using its
uv integration.

PRs that fail CI won't be merged.

Code style
~~~~~~~~~~

- Follow :pep:`8`
- Use ``make lint`` (ruff) to catch issues and ``make fmt`` (ruff) to
  auto-format

Documentation
-------------

The documentation uses Sphinx, MyST, and the Shibuya theme. Install
`uv <https://docs.astral.sh/uv/getting-started/installation/>`_, then run:

.. code-block:: bash

   make docs

Open ``docs/_build/html/index.html`` to view the result. Builds use the locked
``docs`` dependency group and fail on Sphinx warnings, including on Read the
Docs.

For a live-reloading preview at http://127.0.0.1:8001:

.. code-block:: bash

   make docs-serve

Use ``DOCS_PORT=8002`` to choose another preview port, or
``DOCS_BUILDDIR=/tmp/pythondotorg-docs`` to choose another output directory.
``make docs-clean`` removes the selected output directory.


.. _GitHub: https://github.com/python/pythondotorg/issues
.. _license: https://github.com/python/pythondotorg/blob/main/LICENSE
.. _pythondotorg: https://github.com/python/pythondotorg
