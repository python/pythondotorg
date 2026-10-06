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

PRs that fail CI won't be merged.

Code style
~~~~~~~~~~

- Follow :pep:`8`
- Use ``make lint`` (ruff) to catch issues and ``make fmt`` (ruff) to
  auto-format

The agreements app requires annotated function signatures. Inside the development
web container, run its Django-aware type check with:

.. code-block:: bash

   uv run python -m mypy

The configuration in ``pyproject.toml`` checks ``apps/agreements`` without requiring
a typing migration of the legacy apps. Preserve explicit types for domain objects
and quote snapshots; keep dynamic types limited to Django and JSON boundaries.

.. _GitHub: https://github.com/python/pythondotorg/issues
.. _license: https://github.com/python/pythondotorg/blob/main/LICENSE
.. _pythondotorg: https://github.com/python/pythondotorg
