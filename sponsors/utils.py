"""Utility functions for the sponsors app."""

from pathlib import Path

from django.core.files.storage import default_storage


def file_from_storage(filename, mode):
    """Open a file from storage, creating it locally if it does not exist."""
    try:
        # if using S3 Storage the file will always exist
        file = default_storage.open(filename, mode)
    except FileNotFoundError as e:
        # local env, not using S3
        path = Path(e.filename).parent
        if not path.exists():
            path.mkdir(parents=True)
        Path(e.filename).touch()
        file = default_storage.open(filename, mode)

    return file
