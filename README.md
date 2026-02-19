# python.org

[![CI](https://github.com/python/pythondotorg/actions/workflows/ci.yml/badge.svg)](https://github.com/python/pythondotorg/actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects/pythondotorg/badge/?version=latest)](https://pythondotorg.readthedocs.io/?badge=latest)

The codebase behind [python.org](https://www.python.org). Built with Django, PostgreSQL, Redis, and Celery.

> [!NOTE]
> The repository for CPython itself is at https://github.com/python/cpython, and the
> issue tracker is at https://github.com/python/cpython/issues/.
>
> Similarly, issues related to [Python's documentation](https://docs.python.org) can be filed in
> https://github.com/python/cpython/issues/.

### Quick start

```bash
make serve
```

Then visit http://localhost:8000. See the [full setup docs](https://pythondotorg.readthedocs.io/en/latest/install.html) for prerequisites.

### Contributing

Fork the repo, create a branch, and open a pull request. Before submitting:

- Run `make test` and make sure the suite passes
- Run `make lint` and `make fmt`
- Write tests for any new or changed code
- Check for missing migrations with `make migrations`

CI runs on every PR — it checks for ungenerated migrations and enforces a 75%
test coverage minimum. PRs that fail CI won't be merged.

See the full [contributing guide](https://pythondotorg.readthedocs.io/en/latest/contributing.html) for details.

### License

Apache License
